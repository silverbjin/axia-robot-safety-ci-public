# AXIA G07 Task04 — CV2U3T4v WSL2 Scan 300ms TTL 최초 위반·RTF 국소 저하 분석

2026-11-19 KST | 분석 전용 / 로봇·안전 정책 수정 없음 / 강사 WSL2 L3 **HOLD**

## 1. 원본 증거 custody

- 강사 WSL2 원본 TAR `owner-moving-CV2U3T4v.tar.gz` SHA256 `ab2d67d95295dc08782d41b441855c838f486757bf7fb15dface674b4dc568cf`.
- 원본 소형 ZIP `owner-moving-CV2U3T4v.diagnostics.zip` SHA256 `3b6436f1380457721cfde30fb2b2ed1579183c40c05bbb18bce1449fdb316540`.
- 첨부 바이트를 재계산하여 2개 모두 원본 `.sha256` 표기와 일치. `.sha256` 파일에는 원래 WSL2 절대 경로가 포함되므로 다른 컨테이너에서 직접 `sha256sum -c`가 실패할 수 있음. basename과 해시 자체를 비교해 무결성 확인; **증거 불일치가 아님**.
- tar 내 `native/rosbag2/rosbag2_0.db3`: SQLite `PRAGMA quick_check=ok`; 실제 14개 ROS 토픽.
- Student SHA `efff0fb8bf941de74572336d1988dfb0005e11f7`, public read-only gate `71b85c42ea474276fedd9f345521317b8c348b4e`, 공개 실제 Gazebo L2 PASS [#44455960504](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455960504), Owner release `cd8c23c52588f5efd6295b6904e15b1aa54496e7`. CI 성공은 이 WSL2 L3의 PASS가 아님.
- 비공개 개인 경로, 원본 SQLite rosbag, 전체 TAR/ZIP은 공개 GitHub에 업로드하지 않고 이 수치·비식별 관찰 사실만 기록.

## 2. 먼저 성공한 단계 (추측 아닌 실제 원본)

- 공식 ROS/Nav2/Gazebo 패리티: 25개 Debian 패키지와 5개 공식 파일 SHA 일치, `CORE_PARITY_PASS`. Gazebo Harmonic 8.15.0, `libgz-transport13=13.6.0`, WSL2 Ubuntu24.04, domain86.
- 한 개 Gazebo 서버, Gazebo/RViz 두 창 표시 `rviz=1 gazebo=1`. 원래 oZG Xacro/SDF 시작 실패는 재발하지 않음.
- PREGOAL `CLEAR` front1.417762m side2.504368m, 장애물 물리 pregoal `P2_G07_OWNER_PREGOAL_L2_READY_NO_GOAL` front2.032889m side0.724823m, Gazebo 물리 set_pose ACK.
- 과거 HFbm에서 실패했던 controlling-TTY 인수가 **12초에 성공**:
  ```text
  OWNER_GOAL_CONSENT_PENDING timeout_sec=180 goal_sent=false
  OWNER_GOAL_CONSENT_ACCEPTED elapsed_sec=12
  AXIA_G07_TASK04_OWNER_MANUAL_CONTROLLING_TTY_GOAL_CONSENT_PASS
  AXIA_G07_TASK04_OWNER_POST_CONSENT_FRESH_SCAN_ODOM_GUARD_CLOCK_PASS
  ```
- 정확한 실제 Goal UUID `4174f5865a3c4bc2bf468a125f6670d7`, 실행 상태 2 (`EXECUTING`) 확인.
- CLEAR front2.051469m final vx0.037008m/s → SLOW front0.741130m final vx0.006895m/s → STOP front0.389818m final vx0.0m/s; CM final output 0, physical odom 이동0.231441m, zero dwell1.006738s.
- 실제 Gazebo Contact witness complete=true, positive_contacts=0 / observed_iterations=32596. Guard `first_guard_latch=null`, `latched=false`.
- **정확 Goal UUID 최종 Cancel ACK, ordered Nav/Loc Lifecycle ACK 및 전체 안전 21/21은 검증 단계까지 도달하지 못했으므로 성공으로 보고하지 않는다**. `native/teardown.txt=P2_L2_GRACEFUL_TEARDOWN`은 Goal cancel / Lifecycle ACK의 대체 증거가 아님.

## 3. 최초 실패: Scan wall-time 300ms 경계 초과

`native/g07_ci_moving/ci_moving_goal_result.json` 및 `actual_ros_events.jsonl`:

```text
first_timing_violation.channel=scan
first_timing_violation.first_violation_from=342.331026241 (Observer monotonic sec)
first_timing_violation.first_violation_at=342.639467342
first_timing_violation.first_violation_sec=0.30844110099997124
first_timing_violation.limit_sec=0.300
first_timing_violation.first_violation_stage=CROSSES_STOP
reason=RuntimeError:ACTUAL_MOVING_GOAL_CI_ORACLE_SENSOR_DELIVERY_TTL_BOUNDARY_max_scan_interval_sec
```

8.441ms 초과, 첫 후속 동작 실패가 아닌 **최초 안전 시간 위반**. Scan 직전 구간 `342.033071009 → 342.331026241` 역시 297.955ms로 경계에 근접. 이때 Supervisor/Guard 여전히 메시지를 전달했으나 Guard latch가 발생했다는 증거는 없음. `source_timeout=1.0` (공식 CM 활성 파라미터)와 검증기의 Scan 300ms는 서로 다른 계약이며, Guard가 CM fresh 출력을 보고 있다는 사실만으로 Scan 300ms를 통과시킬 수 없다.

`native_runner.log` 마지막의 `P2_L3_G07_OWNER_COMMON_BLOCKED`는 이 위반에서 파생. `first_failure.txt=NATIVE_RUNNER_FAILED_REVIEW_RAW`은 **외부 래퍼의 generic 오류이며 최초 원인을 은폐**한다. `cannot use Destroyable because destruction was requested`는 종료 과정의 2차 예외로 첫 원인으로 오인하지 않는다.

관련 같은 주행창 Observer period:

| 계층 | 측정 최대 구간 | 판정 해석 |
|---|---:|---|
| Scan | **308.441ms** | **300ms 위반** |
| Odom | 184.047ms | 300ms 이내 |
| Clock | 104.243ms | 300ms 이내 |
| Guard 상태 | 110.117ms | 상태 콜백 주기는 정상 범위 |
| CM/pre-guard observer | 108.051ms | 자체 수신 주기 |
| Supervisor source | 129.490ms | CM source+observer 엄격 120ms 동일 계약으로 환산하면 안 됨 |
| Supervisor 상태 | 129.583ms | 별도 FSM 샘플 주기 |

모든 안전 계층 종합 통합 PASS는 위 Scan 실패로 **미검증**. 원래 CM Source/Observer 페어 120ms와 내부 Guard CM TTL150ms는 별도 raw review 전까지 전체 PASS로 승격하지 않는다.

## 4. 원인 분리: 샘플 누락인지 순간 RTF 저하인지

원본 rosbag SQLite의 저장시간 및 LaserScan CDR Header.stamp를 직접 디코드해 동일 지점을 비교했다.

| `/scan` ROS bag 수신간격 | Sim LaserScan Header.stamp 간격 | 해석 |
|---:|---:|---|
| 269.196ms | 102ms | 실제시간 수신 지연, 시뮬레이션 시간 약 10Hz |
| **327.168ms** | **99ms** | 다음 순서의 시뮬레이션 Scan은 유지 |
| 130.647ms | 99ms | 회복 |

동시 `/safety/scan` rosbag gap **326.571ms**. 원본 raw `/scan`과 Fault Injector 경유 `/safety/scan` 양쪽에서 보이므로 **Observer만의 큐 정체**나 **Fault Injector만의 단독 결함**으로 간주할 수 없다.

같은 wall interval 약 `1795062244.075→1795062244.397` 구간의 `/clock`에는 30개 표본, Sim 시간은 **약 0.087초**, 실제시간 약 0.322초. 국소 clock 진행비 약 **27%**. 이는 공식 Gazebo WorldStats RTF 직접 측정은 아니지만 **로봇 센서의 10Hz simulated-time 스케줄 대비 현장 wall-time 300ms TTL 불일치가 일어난 이유를 직접 지지하는 증거**다. 평균 RTF 90%라고 이 짧은 구간을 배제할 수 없다.

`/clock`은 완전히 끊긴 것이 아니라 짧은 진행을 이어갔고, Guard/CM 상태 콜백도 계속 들어왔음. 따라서 전체 호스트가 0.3초 완전히 멈춘 것이라는 가설은 현재 원본과 맞지 않음.

Gazebo 물리 Stop 침입 set_pose native 서비스 응답에 1.682064s가 소요되고 Scan 첫 위반은 `CROSSES_STOP`. 서비스 호출·Gazebo 물리/센서 렌더 루프·WSL2/WSLg CPU/GPU 스케줄링 경쟁이 원인 후보지만 **정확한 병목은 미확정**. LiDAR `update_rate=10Hz`의 정상 simulated-time stamp와 wall-time 지연을 구분해야 한다.

## 5. 권장 최소 후속 작업 (이번 분석에서는 실행/수정하지 않음)

1. 원본 CV2U3T4v TAR/ZIP/SHA256과 성공했던 공개 L2 원본을 보존. 새로운 WSL2 현장 재실행 반복 금지.
2. 공개 CI의 기존 Task04 실제 Gazebo L2에 **ROS bag의 원본 LaserScan header simulated-time gap vs wall-time receive gap vs Clock 국소 진행 비율**이라는 작은 read-only 진단을 추가한다. STOP 물리 set_pose 요청 전후 이벤트(요청/ACK/Scan 생산/bridge 수신/Observer 수신) 시간 경계를 기록한다. 새 ROS 노드나 범용 성능 인프라는 만들지 않는다.
3. Sanitized fixture에서 `10Hz sim stamp 정상, wall gap >300ms`이면 반드시 RED/HOLD가 나오게 회귀 계약을 고정한다. 이후 원인을 입증한 단일 병목(예: WSL2 CPU 경합, GUI/렌더, 물리 set_pose 실행)만 최소 조치한다.
4. LiDAR 10Hz, Scan 300ms, CM120ms/Guard150ms, stop/cancel 및 핵심 World 물리 시나리오 임계값을 **완화하지 않는다**. 이전 D08 GPU 서버 렌더 방식은 G07의 근거리 false scan ring 재발 위험이 있으므로 계측 없이 가져오지 않는다.
5. 수정 후 L0 RED→GREEN → 실제 Gazebo/GUI Moving L2 21/21 PASS → Owner Bootstrap L0 → 강사 WSL2 단일 L3 인수. 각각 실측 주기·최초 위험 FSM·문제 재현·Git SHA/CI Run을 근거로 별도 보고.
6. 실패 시 외부 `first_failure.txt`에는 `ci_moving_goal_result.json.first_timing_violation`의 첫 채널·간격·위반시각을 반영해 generic 오류로 덮지 않는 **진단 전용** 개선 권장.

## 6. 실제 수행한 검증 수준 및 Git 정책

- 수행: 첨부 SHA 직접 재계산 두 개 일치, `tar -tzf`·`unzip -l`, SQLite `quick_check=ok`, 14개 topic 이름/개수 및 bag timestamps, CDR LaserScan Header stamp 파싱, 원본 JSONL 중 STOP/TLL 경계·Goal/PID/Guard evidence 대조. **ROS2/Gazebo를 이 분석 환경에서 새로 실행하지 않음**.
- 현재 베이스: 공개 CI/Student `fix/g07-task04-owner-timing-evidence-20261119` Draft PR [#182](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/182) / [#61](https://github.com/silverbjin/axia-robot-safety-student/pull/61).
- 이 문서는 **분석 보고서만 커밋**. 새로운 CI 회귀 RED/GREEN, 코드 fix, Owner release는 수행하지 않았고 주장하지 않는다.
- 최종 판정: `OWNER_WSL2_L3=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`, `MAIN_MERGED=false`.
