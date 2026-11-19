# AXIA D06/G07 Cycle 08 — GUI pre-Nav2 READY 단일 가설 / RED→GREEN 중간 보고

기준: 2026-11-20 KST | 공개 Draft PR #177 / Student Draft PR #62, main 미병합.
목표는 **최초 READY 직후** native Scan300 지연을 최소 수정으로 제거하는 것이며, Goal/velocity/fault/E-Stop 개발은 이 범위가 아님.

## 1. 최초 실패와 원본

공개 실제 Gazebo/ROS2 Jazzy/공식 Nav2/TB3 Waffle 동일 세션 [#44561289931](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44561289931), SHA `81e4d467ad1ef53950f230fc51745cecc2032a0a`, artifact #14550390779.

- Nav2 ACTION READY host monotonic 161.058s 이후 최초 위험 source-stamp **36.801→36.900초**.
- Gazebo native Scan receive 161.735915→162.038143 = **302.228ms** >300ms.
- 독립 ROS raw 302.476ms, safety 301.446ms, native /clock local RTF **0.288141**. 리소스 지연이 최소한 native 수신 이전에 존재하나 GPU·physics publisher 원인 단정 불가.
- Student 별도 20.009초 Scan Raw199/Safety200 max132.818/133.149ms 거리 CLEAR, Nav2 Navigation/Localization Shutdown ACK, CM/Guard/Supervisor/Gazebo exit0. 이 성공 범위를 전체 안전 통합 PASS로 오판하지 않음.
- 소스 확인: 기존 `p2_no_goal_smoke_ci.sh`는 공식 staged Nav2 startup이 완료된 **후** Gazebo GUI/RViz 자식 프로세스들을 시작한다. 첫 위반은 READY 뒤 약 0.7초에 관측됨. GUI 초기 실행 부하가 simulator RTF 하락과 겹친다는 단일 원인 후보이나 CPU trace 증거 없어 확정 불가.

## 2. 최소 수정: CI-only GUI 실행 시점 이동

- 학생 경로: `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh`.
- 학생 커밋 `2e53172863549e8797def5726fa536c6ec74b5e4`, smoke blob `81adb67b40b3c7ee937bc2c695c4906282391774`.
- `GITHUB_ACTIONS=true`, `AXIA_G07_CI_SENSOR_TRUTH_NO_GOAL=1`, `AXIA_D06_L2_GUI_NICE_ONLY=15`, `AXIA_D06_L2_GUI_PRE_NAV2_READY=1`, `SENSOR_NO_GOAL=1`, `GoalAllowed=0` 조건을 모두 충족할 때에만 기존 단일 `gz sim -g` 및 RViz GUI 자식을 staged Nav2 READY 이전에 구동. **Gazebo 서버를 하나 더 실행하지 않음.**
- staged startup 이후 두 GUI를 **중복 시작하지 않고** 기존 PID 재사용. 기존 모드(특히 강사 WSLg)는 변경 없음.
- 안전 TTL300/CM120/Guard150, sensor 10Hz/QoS, official Nav2, Supervisor, Guard, Collision Monitor 동작·Goal/fault 설정 모두 불변.
- 주행이 없는 NO_GOAL 실제 Xvfb 도구에서만 검증하는 가설. 신규 Publisher/Planner/CM 알고리즘 없음.

## 3. RED→GREEN→REFACTOR→REVIEW→COMMIT

- 새 public L0 `d06/tests/test_d06_c08_ci_gui_pre_nav2_ready.py`: GUI 시작 source 위치가 staged startup보다 이른지, 기존 PID 중복 실행이 없는지, 스코프가 CI/NO_GOAL에만 한정됐는지, 원래 WSLg Owner 경로와 엄격 `assert gap<=.300`가 보존되는지 검사.
- RED [#44562836213](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44562836213): 이전 Student 소스에 `CI_PRE_READY_GUI=0`/사전 GUI 분기 부재.
- 최초 GREEN 후보 SHA `38e674cdc67989115f96f2df810c64b0bf367f79`에서 오래된 Student 별도 경로의 소프트웨어 GL 설정 문자열까지 거부하는 **테스트 오류** 발견. #44563487745 FAIL. 새 pre-ready 분기로 테스트 범위를 좁혀 정정.
- 최종 공개 **GREEN L0** [#44563630615](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44563630615): **131/131 PASS**, tested code SHA `92aed23ef5fccdf5a582ede22c2671956e9bdc23`; runner canary #44563630652 SUCCESS.
- public source Git pin/Owner/blob/워크플로 일괄 검증, CI env opt-in 및 출력 `D06_CI_L2_GUI_PRE_NAV2_STARTED`와 `D06_CI_L2_GUI_EARLY_REUSED_NOT_SPAWNED` 순서 증거 추가.
- **실제 L2** [#44563618730](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44563618730) same SHA 현재 검사 대상. 실행 결과 완료 시 원본 artifact 기반 별도 추가.

## 4. 검증 계층과 출고 조건

- 현재 L0 성공은 real Gazebo 20s Scan300 실증 또는 WSLg D3D12 종료 SIGSEGV 원인 해결 증거가 아님.
- 실제 L2에서는 **첫 post-READY 20s native/raw/safety ≤300ms**, Student dual qualified 20s ≤300ms, Nav2 Nav/Loc ACK, native Collision Monitor/Guard/Supervisor/Gazebo exit0, viewer PID/창 확인, SHA/아티팩트 검증 모두 필수.
- 강사 NVIDIA WSLg -11 최초 core stack 미확보, 실제 L3 NOT_RUN; 3개 안전 계층 CM120/Guard150 물리 데이터 연결과 Moving Goal 미검증.

`D06_GAZEBO_LIVE_RELEASE=HOLD`
`AXIA_MVP_DEMO_ACCEPTED=HOLD`
`CERTIFIED_ESTOP=false`
`MAIN_MERGED=false`

## 5. C08 실제 Gazebo L2 완료 — Strict FAIL, 후단 Student 콜백 지연 확인

[Run #44563618730](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44563618730), 소스 SHA `92aed23ef5fccdf5a582ede22c2671956e9bdc23`; artifact #14550112638.

- `D06_CI_L2_GUI_PRE_NAV2_STARTED`가 Nav2 READY보다 앞서고 같은 GUI PID를 나중에 재사용함. 별도 Gazebo server 두 번째 실행 없음.
- Nav2 READY host monotonic169.103초 이후 20초 native/ROS Scan300 첫 위반 **NO_ROS_TTL_VIOLATION_WITNESSED**. 이는 해당 구간 관측만의 결과이며 GUI 선기동이 모든 환경에서 해결책이라는 인과 증거는 아님.
- 이후 Student 20.031초 window의 Raw201 중 최초 위반, 최대 **414.828ms**; Safety200 중 최초 위반, 최대 **414.021ms**. 안전 판정 `NO_GOAL_SENSOR_UNSAFE_HOLD`. 소스 시각 48.201→48.300초의 Student 첫 Safety 수신 간격 **403.214ms**.
- 정확히 동일한 stamp pair에서 Gazebo native **89.281ms**, 독립 ROS Safety **86.495ms**; 두 번째 Student Safety callback은 peer보다 **315.142ms 뒤**. 원인 경계 `AFTER_INDEPENDENT_ROS_RECEIPT`; GPU LiDAR publisher와 bridge를 403ms 지연 원인으로 단정 불가.
- Student global /clock receipt RTF 약0.998593, Safety 거리 200/200 CLEAR. 거리 CLEAR ≠ Scan TTL CLEAR.
- Navigation SHUTDOWN **ACK 1.858822초**, Localization **ACK 0.253673초**, CM/Gazebo server exit0 (Guard/Supervisor 정상 종료). 안전 종료는 Scoped PASS이나 Sensor TTL FAIL로 **전체 L2 FAIL**.
- 이번 변경은 CI-only Xvfb 실행 순서 실험. 강사 WSLg D3D12/Gazebo SIGSEGV 해결 및 owner L3 증거가 아님.

**다음 단일 개발 후보:** Student `scan_callback`이 최초 수신 host-monotonic을 기록한 다음 동기적으로 LaserScan 전방·측면·near-ring 기하 계산을 수행하는 경계를 줄인다. 동일 수치/거리 판정·300ms TTL을 유지하면서 메시지 수신 기록만 즉시 저장하고, 나머지 순수 계산은 관측 종료 후 수행한다. 원본 정확한 stamp pair 회귀 먼저 RED; 수정 GREEN 이후 실제 Jazzy/Harmonic L2 재검증. 인과 입증 전 추가 CPU/GPU 최적화 확대 금지.

`D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`.
