# AXIA G07 — 강사 WSL2 최종 인수까지의 최소 개발계획 (2026-11-21)

> **문서 상태: PLAN_ONLY / OWNER_RELEASE=HOLD.** 계획 수립 자체는 RED/GREEN 또는 ROS/Gazebo 실제 성공을 뜻하지 않는다.
>
> **기준:** `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md` (세부 원문 변경 금지, 본 문서에서 미확인 내용은 새 기준으로 간주하지 않는다).
> Public Draft [#215](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/215) / Student Draft [#89](https://github.com/silverbjin/axia-robot-safety-student/pull/89).
> 기존 Public #210–#215, Student #83/#84/#86/#88/#89, D08 Public #206, G07 Task01/02 #161/#167을 **중복 구현하지 않는다**.

## 0. 완료 정의, 범위와 금지

**목적:** TB3 Waffle + ROS 2 Jazzy + Gazebo Harmonic + 공식 Nav2/Collision Monitor에서 한 번의 실제 Moving Goal로 CLEAR→SLOW→STOP, 실제 LiDAR, 로봇 움직임, 1초 이상 odom zero dwell, 정확히 같은 Goal UUID Cancel(terminal=5), Nav/Localization shutdown ACK 및 clean child exit, 14-topic 원본 증거를 유지하면서 모든 기존 안전 TTL을 통과하고, 그 **동일 SHA**를 강사 WSL2에서 딱 한 번 인수한다.

**고정 계약:** 원래 `MultiThreadedExecutor(num_threads=2)`; CM delivery ≤120ms; Guard delivery/internal 안전 age ≤150ms; Scan/SafetyScan/Odom/Clock ≤300ms; 12초 pre-Goal Scan/Clock/Odom/graph; 사람/장애물 실제 Gazebo pose와 Header/raw bag; Goal TTY 인가; 실패 시 안전 상태, 최초 Supervisor *안전 악화* 전이, 최초 타이밍 위반, 정확한 UUID 취소; 14-topic custody. 엄격한 비교 부등호와 실제 Baseline 값은 기존 테스트를 따른다.

**금지:** EventsExecutor(실제 L1/Native `SystemError`), SingleThreadedExecutor(실패 후보), 20ms bounded-wait candidate(실제 0/2), Observer writer I/O root 입증 전 리팩터링, 임계값 확장, 가짜 Scan/Goal/cmd_vel, Nav2/Collision Monitor 포크, 새 Planner/안전 노드, 현장 Goal 반복, main 무승인 병합, SW STOP을 인증 E-Stop으로 표시. 강사용 솔루션은 Private, 학생 TODO는 독립 Student; raw bag·개인 경로·UUID는 Public에 게시하지 않는다.

### 현재 검증 동결점 (새 인수 성공으로 승격 금지)

| 기준 | Public / Student 및 실제 실행 | 결과 |
|---|---|---|
| 원본 Multi2 2cycle | Public `9d229c86e77dfe138a59ca446e8ac78e322b24cc`, Student `78483d12a664d2a92960ecf2721b32916baba231`, native [#44870371777](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44870371777) | **1/2 FAIL**; Cycle1 최초 Odom364.601ms, 일곱 채널 공동 공백 |
| 20ms bounded-wait A/B | Public `60636e1172e71fddc120015ddf263350201d690e`, Student `ba20f93a8cfc839342df9b543d29a0ae3a4e51c9`, native [#44870974857](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44870974857) | **0/2 FAIL / 기각** |
| 첫 Scan 정확 경계 | #44870974857 Cycle2, Artifact #14694186347 | Observer600.503ms / Source107.857ms / 원본 RMW Received599.696ms / 동일 Scan Header rosbag107.738ms, Goal **미발행** |
| 최신 in-flight wait 관측 | Public `8fabdb2507b1d13b1ee8406c9d05f733ab2c6482`, Student `6895f90815fe62a4358abe6b306854af5b8cb6a5`, native [#44871515361](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44871515361) | **1/2 FAIL**; Cycle2 SLOW 97표본, 최대 양의 Supervisor vx=0.0001208934m/s |
| 최신 문서 브랜치 | Public `210149c9e8d7280937031ab8652a38bd3651a3a8` | Python [#44872008910](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44872008910) **324 PASS, 3 SKIP**, Runner Canary PASS; strict Native 2/2는 FAIL, WSL2 NOT_RUN |

증거 인덱스: [직전 forensic 보고서](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/210149c9e8d7280937031ab8652a38bd3651a3a8/docs/operations/AXIA_G07_MVP12_PRE_WSL2_FIRST_RMW_WAITSET_SLOW_HOLD_20261121_KO.md).

## G00 — 기존 증거/브랜치 동결 및 최초 사건 경계 확정 (신규 Goal 0회)

- **입력:** Public #210–#215, Student #89, D08 #206(동일/독립 ROS, `rcl take`, CM service A/B), #161/#167(과거 CM/TF 이력) 및 위 native artifact. 코드가 해결된 것인지, **수치와 해당 SHA**가 일치하는지 먼저 대조한다. 이전 A/B를 새로 구현하지 않는다.
- **실행:** 각 artifact SHA256 검증 후 정확한 첫 시점의 (a) Supervisor FSM 상태 변화, (b) Guard latch 및 internal CM age, (c) Scan/Clock/Odom/CM/Guard **실제 수신 간격**, (d) Goal 상태와 위치·헤딩, (e) ROS bag 동일 Header pair를 단일 사건표로 작성한다.
- **필수 구분:** 최초 `BOOT_SAFE→NORMAL`은 **안전 악화 전이가 아니다**. 그 후 실제 악화 전이가 관측되지 않으면 `FIRST_UNSAFE_SUPERVISOR_TRANSITION_NOT_OBSERVED`로 명시한다. RMW Source/Received(시스템 시각)와 Observer callback(호스트 monotonic)의 **각 시간축 내부 간격**만 비교하고, 서로 다른 절대시각을 빼지 않는다. 독립 bag Header 일치는 별도 수신 경로를 보일 뿐 동일 DDS publication seq 증거를 자동으로 주지 않는다.
- **산출물:** `docs/operations/AXIA_G07_G00_EVIDENCE_BOUNDARY_INDEX_KO.md`(예정), 사용한 artifact IDs/SHA256, 최초 사건표, 열린 검증 질문 ≤2개.
- **완료/다음:** 증거 누락과 중복 테스트를 명시하면 G10/G20 분리 진행. 신규 기능 변경 없음.

## G10 — 트랙 A: 최초 RMW→take→Executor 지연 직접 분리

**질문:** 왜 독립 bag/CM 수신은 ~50–108ms인데 원래 Observer는 355–600ms 동안 7개 채널에서 동시에 수신되지 않는가? 기존 Python stack `_wait_for_ready_callbacks` 및 idle pool은 **wait 경로 후보**이지 DDS 수신/OS/GIL 원인의 확증이 아니다.

1. **L0 RED:** 원래 #44870974857 Cycle2 첫 Scan 600.503ms, #44870371777 첫 CM Source50.019ms vs original Received382.004ms, #44870974857 첫 CM Source50.457ms vs original Received354.987ms를 최소 fixture로 추가 또는 기존 경계 테스트 확장. 정확한 first pair seq/헤더 누락, 전이 누락, 시각계 혼합에서 반드시 `HOLD`.
2. **L1 실제 ROS Jazzy no-Goal:** 기존 `AXIA G07 original spin Scan RMW real L1`와 D08 #206의 동일 Python / 독립 OS ROS 수신 계측을 재사용. 추가 프로덕션 노드 없이 기존 CI 계측 범위에서만 `rcl_wait` ready, take 진입/반환, callback 진입, executor 실제 실행/worker 기동 간 **동일 호스트 monotonic** 타이밍을 포착한다. 설치되어 있고 안전한 tracer가 없으면 기존 스택/저비용 read-only hook만 사용; 재현 불가 시 `UNVERIFIED`, 새 C++ wrapper/의존성 추가로 확대하지 않는다.
3. **독립 원인 분리:** (A) Source 자체 지연, (B) 원 Observer RMW Received만 지연, (C) RMW 정상/take·dispatch 늦음, (D) 독립 ROS까지 동일 지연, (E) 프로세스 전체 GIL·CPU 대기 중 어디인지 동시 첫 구간으로 특정한다. 실제 Fast DDS/RMW 구현·패키지 버전/SHM 설정을 읽되, [Fast DDS #6535](https://github.com/eProsima/Fast-DDS/issues/6535)·[rclpy #1452](https://github.com/ros2/rclpy/issues/1452)는 **참고 후보**로만 기록한다. 유사한 333ms가 보고됐다는 이유로 SHM/버전을 변경하지 않는다.
4. **GREEN 수정은 한 곳만:** 실증된 경계에서 *기존* 계측/실행 구성의 최소 수정(지원되는 공식 설정/재사용 코드 우선). Writer 이동, 새 Worker/Executor 유형, 새 ROS 노드, TTL 완화는 금지. L1 정상 센서뿐 아니라 **Source→Observer, Supervisor→CM→Guard 각 데이터 전달과 Guard 내부 age** 회귀까지 포함한다.
5. **REFACTOR→REVIEW→COMMIT:** 임시 실험 비활성/정리. 테스트 실패를 예상 밖 exception으로 숨기지 않고 root candidate와 한계를 리뷰한다. 수정 후 첫 동일 경계 재발하면 G10으로 복귀, 무작위 native Goal 재시도 금지.

**Gate A:** 최초 원인의 어느 경계인지 실제 수치로 확인되었고, 해당 수정에 대한 L0 RED→GREEN, ROS L1, 첫 CM120/Guard150/Scan300 및 관련 7채널 주기 검증이 성공한 상태. 인과 미확정이면 `A=HOLD`.

## G20 — 트랙 B: 실제 SLOW 구간 배치·헤딩 조건 최소 수정

**근거:** #44871515361 Cycle2 `CI_MOVING_GOAL_TIMEOUT_SLOW`. 97 표본, SLOW LiDAR 0.6776m 구간에서도 Supervisor 전진속도 음수, 감속 구간 최대 양의 전진속도 0.0001208934m/s. Robot odom yaw 약 0.115→1.520rad, 전방 장애물은 이후 front>1.6m. 첫 실패는 Nav2의 정상 회전/경로 변화와 물리 장애물 배치 시점의 불일치 **후보**. 독립 확인 전 Nav2 잘못이라고 단정하지 않는다.

1. **재현 RED:** 기존 `slow_timeout_trace.json`, 동일 활성 Goal UUID, `ci_slow_native_gazebo_set_pose_ack.log`, obstacle world XY, 로봇 map/odom heading 및 Scan 전방각을 같은 시점으로 결합. `front 0.4–0.75`만으로 SLOW PASS를 주장하지 않고 반드시 기존 Supervisor **양의 전진속도>0.005m/s**, CM·최종 속도가 실제로 감속한 로그를 확인한다.
2. **최소 GREEN 후보:** Goal/Planner/Controller/CM/Supervisor 코드는 그대로. 기존 `obstacle_world_pose` 및 set-pose 호출의 **실제 이동 헤딩과 전방 LiDAR 각도** 정합성을 검토하고, 이미 확보한 CLEAR 실제 전진·Goal EXECUTING 직후 전방 진행 방향에서 SLOW 물리 장애물을 배치하도록 기존 fixture 조건만 제한/수정한다. 좌표는 검증된 map↔odom anchor만 사용한다. Nav2가 실제로 회전 중이라면 목표를 임의로 강제하거나 양의 `cmd_vel`을 주입하지 말고 실패를 유지한다.
3. **순차 인수:** real set-pose ACK → 새 실제 Scan(서로 다른 Header) 2개 이상 → 실제 Supervisor 양의 전진권한 → CM SLOW 감속 → 같은 UUID로 STOP 영역, 최종 0속도 및 odom zero≥1초 → Cancel ACK를 하나의 Goal로 검증한다. SLOW 실패를 STOP/PASS로 승격하지 않는다.
4. **REVIEW/COMMIT:** 테스트에는 실제 #44871515361 음수/미세속도 사례를 RED fixture로 유지. 시연 임계값, ROS QoS, 안전 FSM, planner 확장 금지.

**Gate B:** L0 RED→GREEN 후 **실제 Gazebo 물리 SLOW→STOP** 1회 검증(트랙 단위)은 성공하고 heading/first Scan/정확한 ACK 증거가 보존되어야 한다. 이후 전체 2/2에서 반드시 다시 검증. 실패 시 `B=HOLD`.

## G30 — 공개 CI 통합 검증 (트랙 A·B 모두 통과할 때만)

- **실행 순서:** Student 해당 코드·계약 고정 SHA 확정 → Public 리뷰어/계측 SHA 고정 → scoped L0 + 전체 Python contract + Runner Canary → ROS Jazzy L1 데이터 전달 주기 → 실제 Harmonic/Gazebo/공식 TB3/Nav2/Collision Monitor **서로 독립적인 cold run 2/2**, 동일 Public/Student 소스 SHA로 수행. 과거 다른 SHA의 성공을 합산 금지.
- **네이티브 각 Cycle 합격조건:** GUI Gazebo/RViz 실제 표시, 12초 pre-Goal sensor/graph, 7채널 최초·최대 수신 주기(Scan/SafetyScan/Odom/Clock300, CM120, Guard/Supervisor150), Guard 내부 CM age/timeout, Superviser 첫 실제 safety transition, 14-topic raw bag custody, 실제 CLEAR→SLOW→STOP, 물리 장애물 set-pose ACK, 진짜 odom 변위와 ≥1초 zero dwell, 정확 UUID `CANCELED=5`, Nav+Localization shutdown ACK, CM/Guard/Supervisor children clean exit0, no Guard unsafe latch, cleanup. 어떠한 항목도 SKIP으로 합격 처리하지 않는다.
- **실패시:** 가장 먼저 발생한 안전 상태/시간 경계를 진단하고, 그 재현 가능한 조각을 CI RED로 넣은 다음에만 수정을 진행한다. 현장 WSL2 Goal 반복 금지, L2 재실행도 이력 없는 무작위 시도 금지.
- **합격 증거:** `run_id` + `job_id` 2개 + 같은 commit SHA + 실제 stdout sentinel + 각 Cycle 첫 사건과 max gap + artifact 2개 SHA256 + TEST PASS / 실제 L2 PASS를 구분한 인수 레지스터.
- **Gate C:** **strict native 2/2 PASS**이고 full L0 및 Runner Canary 녹색. 현재 C=HOLD.

## G40 — SHA 고정 강사 WSL2 최종 실행기 출고 준비

**G30 통과 전에는 WSL2 실행 URL/Goal 명령을 제공하지 않는다.**

1. 기존 `scripts/axia_g07_1ibycgpg_single_observer_wsl2_l3_once.sh`의 실패 1/2 fail-closed gate와 `scripts/axia_g07_task04_owner_moving_l3_once.sh`의 PIN/TTY/ROS/ZIP 계약을 재사용. 새 인수용 파일은 인수 신뢰 경계에 필요한 최소 PIN/검증 메시지 조정만 수행한다.
2. PIN: Public release SHA, Student exact SHA, 실제 2-cycle Run/두 Job 성공, workflow 이름, artifacts check-sums. `--ci-check`에서 GitHub API 403/타임아웃/한 Cycle 실패/잘못된 SHA/skip은 **NO_GOAL_HOLD**. `--self-check`는 ROS/Gazebo/Goal 없이 bash syntax/source/readonly hash 검증.
3. 공개 CI에서 (a) `bash -n`, (b) `--self-check`, (c) `--ci-check` 성공/실패의 positive·negative fixtures, (d) Owner TTY 거부/인증 실패시 Goal=0, (e) 로그 최소 ZIP(+SHA256, 원본 bag은 WSL2 전용) 검증. 거짓 PASS 문구 금지.
4. RED→GREEN→REFACTOR→REVIEW→COMMIT → 공개 CI GREEN 이후 **하나의 curl+SHA256+실행 명령**을 출고한다. 정확한 PIN/실제 스크립트 경로는 G30 검증 후 확정하며 현재 문서에는 임의 URL/명령을 생성하지 않는다.
5. **Gate D:** CI에 의해 진짜 검증된 release script 및 출고 체크리스트 완성. `OWNER_L3_NOT_RUN` 유지.

## G50 — 강사 WSL2에서 단 한 번 최종 인수

- **선행조건:** Gate A+B+C+D 모두 PASS. 사용자 Ubuntu24.04 WSL2/Jazzy/Harmonic/WSLg 환경 진단과 권한 확인, Private instructor repo 접근, Goal TTY 수동 승인. GUI가 필요한 Gazebo/RViz, RMW/패키지 버전, GPU/RTF는 현장 조건에서 별도 기록(무료 독립 NVIDIA 호스트는 필수 게이트로 추가하지 않는다).
- **사용자 동작:** 배포된 SHA 검증 원샷을 한 번 실행. Script가 환경·Public CI SHA/Run 확인→Gazebo/Nav2→수동 TTY 승인→하나의 Goal/CLEAR/SLOW/STOP/정지/Cancel/종료→증거 최소 패키징 수행. 중간 승인 입력을 여러 번 요구하지 않도록 구성하되 안전상 **Goal 승인 1회**는 유지.
- **합격:** 14-topic 원본 custody 및 SHA256, GUI 확인, 모든 기존 120/150/300ms 주기와 내부 Guard age, 최초 Supervisor safety state, 실물 대신 실제 Gazebo 장애물/속도, odom 1초, action exact UUID Cancel=5, Nav/Loc clean shutdown, 모든 자식 PID 종료 확인. SW STOP이며 **인증된 하드웨어 E-Stop 아님**을 보고서에 명시.
- **현장 실패시:** `FIELD_HOLD`; 최초 상태 전이/타이밍 위반이 포함된 작고 검증된 diagnostic ZIP만 회수. 재현 가능 부분을 **공개 CI 회귀 RED→GREEN에 먼저 편입**하고 새로운 exact SHA에서 strict L2 2/2를 다시 확보한다. 동일한 현장 재시도 반복 금지.
- **Gate E:** 한 번의 Owner WSL2 L3 **실제 실행**과 raw 증거 리뷰까지 완료한 때에만 `OWNER_L3_ACCEPTED`.

## G60 — 보고/병합 결정

- Public 원본 증거는 SHA/수치 요약만; Private instructor에 정답/개인 raw evidence; Student에는 TODO, 정답 누출 금지.
- 각 개발 단위 필수 제출: 변경 파일 전체 경로, 실행 명령, 실제 stdout/stderr 요지, 테스트 범위(L0/L1/L2/L3), 최초 실패, 미검증 항목, branch/commit/PR/Run/Job/artifact/hash, review 및 commit.
- **사용자 명시 승인 전**에는 Public·Student·Instructor 어느 저장소의 `main`에도 병합하지 않는다. PR Draft를 유지하며 인수 성공과 병합은 별개 절차.

## 작업 순서 및 실패 시 의사결정

```text
G00 기존 증거/브랜치 동결
    ├── G10 A: 최초 Source→RMW→take→Executor 경계 분리 → 최소 수정 → L1 안전 TTL
    └── G20 B: SLOW 실제 헤딩/장애물 전방 배치 → 최소 수정 → Gazebo 물리 SLOW/STOP
                  ↓ A와 B 둘 다 GREEN
G30 전체 공개 계약 + 같은 SHA 실제 독립 Gazebo Moving Goal 2/2
                  ↓ PASS 2/2 & 필수 Gate 누락 없음
G40 Owner SHA pin/self-check/ci-check + 공개 CI 출고 검증
                  ↓ GREEN
G50 WSL2 한 번 최종 인수(현장 TTY Goal 승인)
                  ↓ raw evidence PASS
G60 최종 보고 → 별도 main 병합 승인 요청
```

**중단 조건:** A 인과 미확정, B SLOW 실제 양의 전진권한 미확보, C 실제 2/2 미달, D 출고 검증 오류 중 하나라도 존재하면 `RELEASE=HOLD`. WSL2 현장 실행/새 실행 명령은 없다.

## 실행·검증 명령의 역할 (현재 제공 가능 범위)

기존 GitHub Actions/Student checkout 환경에서의 **테스트 명령 예시**이며, 본 계획을 게시한다고 새 테스트를 실행한 것은 아니다.

```bash
# Public repo checked out at target candidate SHA
python3 -m unittest discover -s tests -p 'test_g07_first_scan_rmw_evidence_export.py' -v
python3 -m pytest -q -ra tests

# Student independent checkout at exact pinned SHA
cd block_B/day07/h01_runtime
python3 -m unittest discover -s tools -p 'test_g07_observer_io_first_boundary.py' -v

# Public native run 결과 읽기(해당 workflow는 push 시 GitHub Actions가 실제 기동)
gh run view RUN_ID --repo silverbjin/axia-robot-safety-ci-public --json status,conclusion,headSha,jobs
gh run download RUN_ID --repo silverbjin/axia-robot-safety-ci-public --dir ./g07_numeric_evidence
```

`RUN_ID`는 **새 GitHub native 2-cycle이 실제 완료된 후**의 ID로 바꾼다. GitHub Actions 이력이 없는 결과는 발명하지 않는다. User WSL2의 새로운 Goal 명령은 Gate C/D 이후에만 출고한다.

**현재 인계 상태:** `PLAN_APPROVED_NOT_IMPLEMENTED`는 사용자 승인 시에만 적용. 본 문서 자체는 `PLAN_CREATED`, `ROOT_UNDETERMINED`, `A_HOLD`, `B_HOLD`, `C_HOLD`, `OWNER_WSL2_L3_NOT_RUN`, `MAIN_NOT_MERGED`.
