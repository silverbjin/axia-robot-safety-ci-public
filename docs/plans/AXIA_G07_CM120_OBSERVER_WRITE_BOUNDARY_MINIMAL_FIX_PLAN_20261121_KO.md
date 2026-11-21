# AXIA G07 — CM120 및 7개 토픽 동시 지연 최소 수정 계획

**일자**: 2026-11-21  
**기준**: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`; 기존 공식 TurtleBot3/Nav2/Collision Monitor 재사용  
**상태**: PLAN_ONLY / ACTUAL_FIX_NOT_IMPLEMENTED / OWNER_L3_HOLD  
**공개 개발 기준**: PR #210, `fix/g07-owner-1ibycgpg-cm120-firstclock-20261121`  
**기존 실험 후보**: Student PR #79 그룹 분리 L1 실패, Student PR #80 SingleThreaded L1 성공·실제 Gazebo L2 1/2 실패

## 1. 증거 고정 및 첫 실패

실제 native CI #44855963095, immutable workflow SHA `9b0fef8c5c1502685c5e16486408225c7930eb00`, 학생 소스 SHA `2218584a907d3b7082588dc40625c8156cc88486`.

- Cycle 1 **FAIL**: PRE_STOP 최초 `/odom` `264.699048484→265.059473585`, 360.425101ms >300ms. 거의 동시 7채널 첫 위반: `/scan` 342.189295ms, `/clock` 338.477114ms, `pre_guard` 377.734158ms >120ms, `supervised` 377.355937ms, Guard 374.237092ms, Supervisor 377.391612ms. Goal 이후 실제 CLEAR→SLOW→STOP/Cancel ACK는 있었지만 TTL 실패로 L2 FAIL.
- 같은 `pre_guard` consecutive seq +1 실제 RMW Source **52.640339ms** / Received **378.084177ms** / Observer Host Monotonic **377.734158ms**. Source 주기만으로 DDS->take 또는 Callback 원인 확정 불가.
- 독립 ROS 수신기 같은 호스트에서 원 Observer 공백 내부 **7회 연속 수신**, 해당 인접 receive host gap 최대 약53.6ms. 그러나 원본 `independent_cm_rmw.jsonl` **292/292건의** `rmw_source_ns`, `rmw_received_ns`, `rmw_publication_seq`가 모두 -1이므로 **동일 publication 정확한 교차 매칭 불가**. 이 한계를 공개 CI에서 fail-closed 유지.
- Cycle 2 **PASS** / 네이티브 전체 **1/2 FAIL**. 기존 Multi 2/2 L2 #44830956042는 별도 소스·과거 성공, 이번 수정의 증거가 아님.
- Goal 전 독립 12초 gate `/scan` max112.270968ms, `/safety/scan` 115.856504ms, Clock18.099961ms, Odom43.891267ms, 평균 local RTF0.998124. 따라서 **Goal 이후 관찰 중 공백**을 별도 재현 대상으로 유지. preGoal PASS가 Moving TTL PASS를 뜻하지 않음.

### 소스에서 발견한 최우선 검증 가설 (아직 root 미확정)

Student `block_B/day07/h01_runtime/tools/p2_l3_live_session.py::Observer._write`:
```python
with self.lock:
    self.event_file.write(json.dumps({'kind':kind,'t':t,**kv},sort_keys=True)+'\n')
    if flush_sec is not None and 0 <= t-self._last_periodic_flush_mono >= flush_sec:
        self.event_file.flush()
        self._last_periodic_flush_mono=t
    self.latest[kind]=t
```
실제 CI owner parity는 `buffered_evidence=True`, `periodic_flush_sec=.75`. 즉 JSON 직렬화·파일 쓰기·주기 flush가 **하나의 Observer callback lock에서 동기 실행**되며, 공유 callback group 및 락 대기가 다수 토픽의 동시 수신공백을 만들 수 있음. 아직 `flush()` 호출별 실행 시간이 기존 원본에 없으므로 **후보이며 입증된 원인으로 기재하지 않음**. 먼저 이 국소 지연과 첫 360~378ms 공백의 overlap을 계측해야 함. ROS 2 Jazzy Executor issue ros2/rclpy#1452는 관련 선행 보고이나 이번 장애의 root proof가 아님.

## 2. 작업 단위 — RED → GREEN → REFACTOR → REVIEW → COMMIT

### S0. 기존 성공·현재 실패 보존 / 브랜치 중복 감사 — 코드 변경 없음
- 기존 PR #73·#79·#80과 공개 PR #210의 파일 SHA·설정·실제 CI 상태 점검. 새로운 Planner/Publisher/Guard/Collision Monitor 도입 금지.
- 공개 fixture `tests/fixtures/g07_native_single_44855963095_first_gap.json`, 기존 `tests/test_g07_native_single_44855963095_independent_witness.py`, `tests/test_g07_cm_observer_first_gap.py`을 재사용. 독립 witness 원본 all(-1)을 유효한 DDS 시퀀스로 승격 금지.
- 수치 fixture는 첫 위반 Odom 360.425ms와 7채널 교차 결과를 **RED/HOLD**로 유지해야 함. ROS bag/Goal UUID/개인 경로는 GitHub 업로드 금지.

### S1. 첫 callback/lock/flush 병목을 단 한 번에 분리 — read-only 최소 계측
- 단일 기존 Observer 클래스에서 `time.monotonic_ns()`로: 콜백 진입, `self.lock` 대기 시작/획득, 직렬화 소요, `event_file.write()` 소요, flush 시작/끝, 콜백 완료를 bounded in-memory 카운터/first N 로그로 수집. 원본 이벤트 의미 및 판정은 변경 금지. 콜백에서 별도 파일 출력/print/시스템 명령 호출 금지.
- 같은 프로세스의 비제어 heartbeat를 독립 Python thread에서 20ms 전후로 기록: heartbeat도 멈춘 경우 host scheduling/GIL/CPU 후보; heartbeat는 정상이고 callback만 멈추면 Executor/lock/flush 후보. heartbeat는 **안전 PASS 근거가 아님**.
- 기존 독립 CM witness의 메타데이터 세 필드 개별 취급(이미 변경된 public diagnostic)을 유지. 정확한 seq/소스 timestamp/GID의 지원 여부를 Jazzy 런타임에서 확인. 정확한 쌍이 안 맞으면 `EXACT_PAIR_UNVERIFIED_HOLD`, 단지 host-monotonic witness 연속성 후보만 표기.
- Goal 전 12초 검사뿐 아니라 **실제 Moving PRE_STOP 최초 위반**을 관통하는 500ms 전후 좁은 window 비교. 모든 7개 토픽과 Guard 실제 내부 age는 별도 기록. 모든 측정치는 같은 도메인 내 **간격끼리만** 비교하고 Monotonic 절대값과 RMW System 절대값을 빼지 않음.
- **S1 Done**: 최초 360~378ms 위반과 flush/lock/heartbeat의 시간적 중첩 여부를 판정할 수 있어야 함. 원인 미확정이면 반드시 `FIRST_BOUNDARY_UNDETERMINED_HOLD`. L0 숫자 회귀 → 동일 환경 저부하 ROS Jazzy L1 → 필요할 때만 native NO_GOAL 부하 계측. 불필요한 실제 Goal 반복 금지.

### S2. S1에서 I/O 병목이 확인된 경우에만 최소 수정
- **RED**: 기존 Observer의 동기 `flush()`가 150~380ms로 지연되도록 제한된 CI unit fixture를 주입하고, 원래 7채널 callback interarrival strict gate가 HOLD되는지 입증. 이 합성 RED를 실제 Gazebo 고장 재현으로 주장 금지.
- **GREEN**: 콜백 내부를 `bounded deque append + 상태 갱신`으로 최소화하고, 현재 사용 중인 main loop/기존 evidence gate 쪽에서 snapshot만 짧게 가져온 다음 **록 바깥에서** JSON serialize/write/flush 수행. 기존 ROS 노드나 새 Publisher 생성 금지. callback lock 아래 파일 flush 금지. buffer overflow, writer fail, timestamp missing은 fail-closed. 정상 및 예외 종료 시 기존 14-topic rosbag custody와 JSON event digest를 보존.
- 기존 `p2_g07_ci_moving_goal.py`의 Goal/Cancel, Nav2 shutdown, Guard/CM, 실제 Gazebo witness는 재사용. 반드시 변경된 테스트에서 `--self-check`, `bash -n`, `py_compile`, Scan/Clock/Odom300, CM120, Guard150, action cancel, shutdown 계약을 회귀.
- **S2 Done**: RED의 동일 stall source에서 AFTER/BEFORE 원인을 분리하고, 파일 쓰기가 콜백·공유 lock를 직접 정지시키지 않음을 확인. S1에서 flush/lock 연관성이 없으면 S2 구현을 진행하지 않고 S3의 제한된 Executor/OS 스케줄링 경계 진단으로 이동.

### S3. S1이 I/O root를 기각하거나 수정 후에도 공백이 재현될 때만
- 기존 독립 ROS CM witness, 14-topic raw rosbag, rclpy Executor 원본 코드와 native process heartbeat를 조합. 동일 source publication pair를 정확히 식별할 메타데이터가 없으면 조인 불가(지표 불완전 HOLD).
- 독립 process heartbeat가 안정되고 original Observer만 중단이면 original callback/executor/lock/GIL을 좁힘. 별도 process 및 rosbag 수신도 동시 중단이면 RMW/host/WSL2 scheduling 또는 Gazebo generation으로 범위를 확장하되 **발행자/수신자 간 시계 epoch 혼합 금지**.
- 공식 ros2_tracing/LTTng를 쓰더라도 **기존 환경에서 즉시 이용 가능할 때만** 하나의 read-only 1회 trace, 추가 다중 환경/커스텀 C++ 노드/새 middleware 도입 안 함.
- SingleThreadedExecutor 단독 채택 금지: 실제 L2 1/2 FAIL. 콜백 그룹 분리 단독 채택 금지: 실제 L1 FAIL. 무조건 스레드 수 증설, 타이밍 기준 완화, 임의 sleep/timeout 변경 금지.

### S4. 안전 검증 · 실제 Gazebo L2 · Owner WSL2 최종 단일 인수
- 소스 수정이 결정되면 **Student 새로운 독립 Draft PR** / Public 새로운 Draft PR 또는 명시적 기존 PR의 후속 브랜치로 구분. 교수 정답은 비공개 강사용 저장소 유지. 교차 의존 SHA 정확히 고정; 원래 성공한 2/2 release SHA는 변경하지 않음.
- 공개 CI L0: 첫 실패(원본 7토픽 숫자), write-lock fixture RED→GREEN, scan/clock/odom/CM/Guard/goal/shutdown 필수 계약 및 앞선 역방향/순방향 RMW 시계 불연속 fail-closed. 모든 payload TTL 그대로.
- 실제 Jazzy/Harmonic/TB3/Nav2 + Collision Monitor + Guard + rosbag14-topic + RViz/Gazebo Xvfb **독립 cold-run 2/2**: 각각 12s NO_GOAL preflight, 실제 물리적 장애물 fixture, CLEAR→SLOW→STOP, 1s odom ZERO, 정확한 UUID 취소, Navigation/Localization clean ACK, CM/Guard exit0, **첫 위반 0건**, source+observer CM<=120ms, Guard 내부 age<=150ms, /scan /safety/scan /odom /clock<=300ms, guard/supervised 전달<=150ms; 저장된 first boundary RAW 검증. GUI 2개 필요. CI 이전 성공 run은 이번 수정의 2/2로 대체 불가.
- 신규 CI 2/2 SUCCESS 후에만 SHA-pinned `bash -n`, `--self-check`, `--ci-check`, 실제 `--run` Owner 스크립트를 공개 repo에 **별도 불변 commit**로 배포. 강사 WSL2 Ubuntu24.04/WSLg NVIDIA에서 수동 TTY 승인 후 단 1회 L3 인수. 기존 Goal 자동 발행 금지.
- WSL2 새 첫 위반 발견 시 재시도 금지 → 소형 ZIP(원본 SHA manifest, first safety transition, first timing boundary)만 제출 → 공개 CI 새 회귀 RED→GREEN 우선. L3에서 새 2/2 소스의 모든 7토픽·Guard 내부 TTL·Goal/Shutdown까지 확인 전까지 RELEASE=HOLD.

## 3. 예상 작업 경로와 명령 (계획된 명령, 현재 실행하지 않음)

공개 CI:
```bash
python3 -m unittest discover -s tests -p 'test_g07_cm_observer_first_gap.py' -v
python3 -m unittest discover -s tests -p 'test_g07_native_single_44855963095_independent_witness.py' -v
python3 -m unittest discover -s tests -p 'test_g07_isolated_cm_witness.py' -v
python3 -m pytest -q -ra tests
```

Student:
```bash
python3 -m py_compile block_B/day07/h01_runtime/tools/p2_l3_live_session.py
python3 -m py_compile block_B/day07/h01_runtime/tools/p2_g07_ci_moving_goal.py
```

실제 CI native L2는 기존 `.github/workflows/axia-g07-1ibycgpg-single-observer-native-l2.yml`을 **직접 안전 기준 변경하는 대신**, 새 파일명으로 후보 SHA에 한 번만 재고정한 workflow를 작성할 예정. L3 스크립트는 **기존 blocked 후보를 재사용/공개하지 않고**, 새 2/2 PASS에 한해 별도 sha256 pinned 출고할 예정.

## 4. 성공/중단 판정

| 조건 | 판정 |
|---|---|
| S1에서 최초 flush/lock 360~378ms와 실제 유효한 콜백 stop이 동시에 관측 | Root candidate confirmed **only for observer-side I/O**, 실제 이관 전 HOLD |
| CI synthetic RED / 최소 I/O 변경 GREEN, 콜백 I/O=0, 원본 fail-closed 유지 | L0/L1 PASS candidate, **L2 NOT_RUN** |
| 실제 native 2개 독립 Goal 중 하나라도 120/150/300ms 초과 | **L2 HOLD, WSL2 스크립트 미출고** |
| 실제 L2 **2/2 PASS** + checksum/버전 정확성 | WSL2 **출고 준비**, 현장 L3 미인수 |
| 실제 WSL2 L3 1회 모든 기준 통과 | **시뮬레이션 MVP 범위 인수**; 하드웨어 안전 인증/E-Stop 아님 |
| 원인 미확정·센서 native/RMW 증거 부족 | **원인 미확정 HOLD**; 새 로봇 기능·안전 임계값 변경 금지 |

**이 문서는 계획만 기록함**. 지금 수행한 실제 통합 검증은 native L2 #44855963095 FAIL 1/2, 현장 WSL2 이번 후보 NOT_RUN. Main merge는 사용자 사전 승인 없이는 금지.
