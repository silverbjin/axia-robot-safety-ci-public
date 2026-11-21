# AXIA G07 — persistent single Executor 단일 원인 후보의 실제 검증 및 출고 부적합 (2026-11-21)

## 1. 결론

**신규 G07 Owner WSL2 인수 준비 미충족. Candidate rejected / HOLD / 실제 Gazebo 0-of-2.**
리팩토링 후에도 발생하는 최초 Scan/Clock/Odom 수신 타이밍 위반의 한 원인 후보를 **최소 수정 → RED/GREEN → 실제 Native 2-cycle**로 검증했으나 해결되지 않았다. 더 많은 임시 Executor·DDS 참여자·센서 설정과 TTL 완화 없이 현재 브랜치는 시험 증거로 보존하고 **출고하지 않는다**. 이전 교육용 `jrCIgoGl` 인수 증거는 그대로 유지한다.

## 2. 원인 가설과 공식 소스 확인

ROS 2 Jazzy `ros2/rclpy@jazzy`, `rclpy/rclpy/__init__.py`의 `spin_once(node, timeout_sec)`는 **매 호출마다** `executor.add_node(node)` → `executor.spin_once()` → finally `executor.remove_node(node)`를 수행한다. Student `tools/p2_g07_scan_wall_pregoal.py`는 발견 워밍업과 실제 12초 센서 관측에서 `rclpy.spin_once(node,timeout_sec=.04)`를 호출했다. 약 300Hz Clock + 10Hz Scan + Odom의 고빈도 반복 add/remove는 불필요한 waitset 동작과 기본 Executor 재등록을 발생시킨다. 이는 *코드상 확인된 반복 연산*이지만, 300–400ms 실제 수신 지연의 근본 원인이라고 단정한 것은 아니다.

참고 공식 소스: https://github.com/ros2/rclpy/blob/jazzy/rclpy/rclpy/__init__.py

## 3. 실제 RED→GREEN

Student Draft PR [#107](https://github.com/silverbjin/axia-robot-safety-student/pull/107), branch `fix/g07-pregoal-persistent-single-executor-20261121`:
- RED `51c48238dbe24f700586b29afa49d2f712c63a64`: 기존 프리플라이트에서 global spin_once 함수 반복과 explicit SingleThreadedExecutor 부재를 검출하는 4 unittest 추가.
- 기존 Block B CI 연결 `66bd5763883233e913bcd3309b6dc50c139b65bd`; [real RED #44916547800](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44916547800): **2 FAIL / 2 PASS**.
- GREEN `12c8894a2ff725c05bca4c9ba3e7f418200f8355`: 같은 NO_GOAL 프리플라이트 프로세스 내 명시적 `SingleThreadedExecutor` 1개 생성/노드 1회 등록/워밍업과 12초 관측에서 재사용/종료 후 정리. 기존 ROS subscriber 4개, Topic QoS, 300ms Clock/Odom, 300ms scan diagnostic, 150ms Scan Header, 12초 관측창 유지, Fault·Goal·Guard·CM·Nav2 변경 없음.
- 초기 GREEN L0가 1개 실패한 이유는 실제 코드가 아니라 과거 호출을 설명한 **주석까지 문자열 탐색**하던 테스트의 오검출. 실제 AST.Call만 검사하도록 수정 `720e687d023dcebf2dc4a818397e928156ad5a9e`.
- [Student L0 GREEN #44916638746](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44916638746): 기존 Block B CI **SUCCESS**. 녹색 CI는 ROS-free 회귀이며 실제 timing 개선 증거가 아니다.

Public Draft PR [#230](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/230), branch `fix/g07-pregoal-persistent-executor-native-20261121`:
- native 정확한 Public 소스 SHA `03530c76913649aeadd905adc0914b37ec5aa6ec`; Student checkout 고정 SHA `720e687d023dcebf2dc4a818397e928156ad5a9e`.
- 기존 2-cycle full GUI-present native L2, 모든 Goal 권한/Shutdown/14-topic bag/CM120/Guard150/Clock-Odom300 및 Header150 그대로. 신규 워크플로 또는 새 ROS node 없음.
- [Public Python #44916676482](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44916676482): **341 passed / 3 skipped in 4.90s**.

## 4. 실제 Native 2-cycle — 출고 HOLD

[Public native #44916662519](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44916662519): **0/2 FAIL**.

| Cycle | FIRST failure | 근거 및 범위 |
| --- | --- | --- |
| 1, job 136883640232 | preGoal `SCAN_PREFLIGHT_CLOCK_ODOM_INTERVAL_BREACH`, Goal 미발행 | `/scan` 첫 callback gap **410.175131ms** (300 제한), 동일 발행 seq+1/header99ms, RMW source **112.409324ms** vs received **409.683177ms**, Clock max **334.532461ms**. Scan callback gap은 진단이지만 실제 clock/odom 경계 violation이 Goal을 차단. |
| 2, job 136883640056 | preGoal `SCAN_PREFLIGHT_STREAM_DISCOVERY_TIMEOUT`, Goal 미발행 | 8초 안에 Scan RMW 수신 관측 **0 samples**; Clock/Odom/scan 전체 메시지수는 압축 아티팩트로만 확인 가능, 원인 미확정. 이전 ROS node DDS discovery, server startup과 각각 구분해야 함. |

Cycle1 **409ms receipt gap**은 동일 scan 발행 간격112ms와 크게 다르므로 Publisher 단독 주기 장애로 증명할 수 없다. 동시에 Clock은 해당 scan gap 안에서도 callback을 실행하므로 **전체 Python executor 정지**만으로 설명할 수 없다. 다른 participant rosbag에서 과거 동일 헤더쌍을 약108ms로 받았다는 기왕 증거와 양립한다. Candidate의 기본 Executor 재등록 제거로 문제가 해결됐다고 볼 근거가 없음. Cycle2 무수신은 후보가 원인이라는 증거도 아니므로 `PERSISTENT_EXECUTOR_CAUSED_DISCOVERY_TIMEOUT`으로 단정하지 않는다.

**Artifact custody (GitHub Actions ZIP digest, WSL2 raw bag hash 아님):**
- Cycle1 artifact ID `14712411302`, `sha256:6374d9344832df968eea211f2b69c59b09da9c66ac753ab97609d3eedea6a852`, 11734 bytes.
- Cycle2 artifact ID `14712287081`, `sha256:48b1883e938fe0bcacb2d31a8c590e105cbaf678ac922e8569086e38e2f0be38`, 10857 bytes.
- Expiry 2026-12-05. 장기 증거 보관 정책은 별도.
- Original previous Native [#44914827138](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44914827138) 0/2: Cycle1 first /scan439.011892ms + Clock335.393855ms/Odom374.025229ms; Cycle2 postGoal first Odom362.100229ms, CM preGuard379.730024ms, original CM RMW receive375.941379ms vs independent54.116537ms. 이전 실패와 새 실패는 다른 실행이라 숫자를 하나의 단일 run으로 병합하지 말 것.

## 5. 다음 디버깅 분기(새 기능 금지)

재검증 순서:
1. **기존 Recorder와 Sensor preGoal의 동일 헤더쌍·발행 seq+1**을 맞추고, Gazebo native publish→ros_gz bridge→FastDDS original vs independent reader의 첫 receipt/take gap을 확인. 같은 monotonic timebase가 아니면 임의 차감하지 않는다.
2. 서로 다른 참가자에서 100ms와 410ms의 첫 수신 간격이 다르다는 기존 증거가 있으므로, 원래 reader/Participant의 RMW 수신·queue·take/Executor 경계를 분리한다. 원인 확정 전 타이밍 실패 원인을 공식 Nav2/CM 자체나 CPU affinity로 돌리지 않는다.
3. 실제 **CM 내부→Guard 내부** 120/150ms 및 실제 scan/clock/odom 300ms 독립 증거를 유지해야 하는 인수 기준을 완화하지 않는다. Subscriber 계측만 바꿔 PASS로 바꾸지 않는다.
4. 새 실제 L2 2/2가 나온 정확한 Student/Public SHA를 확인하기 전에는 새로운 Owner WSL2 Moving Goal 스크립트를 배포하지 않는다. 수업은 기존 `jrCIgoGl` acceptance/Replay 사용.

## 6. 최종 상태

- Student PR #107: 구조상 재등록 제거 GREEN, 실증상 **REJECTED as timing fix**, main 미병합.
- Public PR #230: L0 PASS, actual G07 Moving Native **0/2 FAIL**, Owner release HOLD.
- 기존 Instructor/Student main과 `jrCIgoGl`: 변경하지 않음.
- L0 GREEN / L1 only existing scoped evidence / New L2 FAIL / New L3 **NOT_RUN**.
- `CERTIFIED_ESTOP=false`; SW 보호정지는 인증 E-Stop 아님.
