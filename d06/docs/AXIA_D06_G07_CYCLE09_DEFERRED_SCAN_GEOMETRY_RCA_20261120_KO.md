# AXIA D06/G07 Cycle 09 — Student Scan 콜백 O(1) 수신 계측 / deferred geometry 중간 보고

기준일 2026-11-20 KST. 공개 PR #177 / Student PR #62 Draft. `main` 미병합. 출고 HOLD.

## 1. 최초 실패와 계층별 원본 증거

공개 실 Jazzy/Harmonic/Nav2/Waffle L2 [#44563618730](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44563618730), CI SHA `92aed23ef5fccdf5a582ede22c2671956e9bdc23`, artifact #14550112638, NO_GOAL.

- CI 전용 GUI 선기동 이후 Nav2 READY host monotonic 169.103초부터 20초 동안 **독립 Gazebo native / ROS Raw / ROS Safety**에서는 Scan300 위반 없음.
- 그러나 Student 20.031초 Raw201 최대414.828ms / Safety200 최대414.021ms, 전체 거리 Safety 200/200 CLEAR이지만 Raw/Safety TTL300 둘 다 FAIL.
- 첫 Student Safety 위반 정확 source-stamp **48.201→48.300초**: Student callback host gap **403.214ms**; 동일 stamp Gazebo native **89.281ms**, independent ROS Safety **86.495ms**. 두 번째 Student callback 독립 ROS peer 대비 **315.142ms 늦음**. 계층 `AFTER_INDEPENDENT_ROS_RECEIPT`.
- /clock global receipt RTF 약0.9986; 이는 Student 콜백 지연이 없다는 증명이 아님.
- 해당 세션 Navigation/Localization SHUTDOWN ACK, Collision Monitor 및 Gazebo server child exit0. 정상 종료는 Scan TTL 위반을 무효화하지 않음.

## 2. 단일 수정 가설 및 실제 파일

`silverbjin/axia-robot-safety-student` `block_B/day07/h01_runtime/tools/g07_wslg_no_goal_sensor_probe.py`. 이전 Scan callback은 host-monotonic timestamp를 기록한 후 front-sector/side-sector/near-ring을 ROS executor 실행 흐름 **안에서** 반복 계산. 두 Scan 토픽과 같은 전용 executor의 장시간 작업/스케줄러 지연을 분리하기 위해 이번에는 **콜백 즉시 recv/header stamp 및 LaserScan 참조만 기록**하고 기존 순수 geometry 계산을 두 executor 정지 후 동일 Python 함수로 수행.

- 수신 타임스탬프, 원본 stamp, 동일 메시지 개수 및 300ms 안전 TTL 불변.
- front/side/near 유효성 검사는 원래 조건과 동일. 유효하지 않은 LaserScan 행은 검증에서 제외하고, 실제 receipt에 기반해 2회 정상 선행 준비와 최종 20초 dwell을 **다시 계산**. 계산 중 경과 시간은 dwell로 세지 않음(FAIL closed).
- callback 측정 20초 + .2초 여유는 순수 관측 길이 보정용이며 Scan300/CM120/Guard150 제한시간을 연장하지 않음.
- Student commit `0565e580f5b7c80d719960a6046de3e45c8ea477`, probe blob `922516dd0bb8818bdf1ed057813168886d3b3b8e`.
- 공개 Owner `d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh` SHA `cb147989b7ef86af671cff8c65bf9317cc4de9ea`, blob `d19a364d7180c542a7204111bb68b3394c5d42f9`으로 Student pinned. 외부 Owner/공개 L0/L2 checkout도 동일 SHA/blob 연계.
- ROS2 Publisher/Goal/Twist/Fault/새 sensor/Planner/Nav2/CM/Guard 개발 없음.

## 3. TDD RED → GREEN → REFACTOR → REVIEW → COMMIT

- RED `d06/tests/test_d06_c09_deferred_scan_geometry.py`: 콜백 내 geometry 제거, 그대로 deferred geometry front1.414m/side2.52m, invalid LaserScan fail closed, 실제 receipt timestamp 보존 요구.
- 공개 의도한 RED [#44565508503](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44565508503): `AttributeError: ... no attribute enrich_scan_geometry`, 기존 callback에 `"_laser_msg":msg` 부재.
- GREEN Student code above. 기존 `d06/tests/test_d06_g07_student_first_receipt_pair.py`가 geometry가 콜백 내부에 있다고 가정한 오래된 테스트를 새 구조에 맞춰 수정. C09 테스트에서 function declaration과 실제 deferred call을 혼동한 순서 검사도 정확한 함수 호출 위치로 정정.
- 공개 **GREEN L0** [#44566309832](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44566309832), **134/134 PASS**.
- 공개 코드 SHA `84af2ea35ac439b6cf665b323c8d8d19f77a9067`, runner canary #44566328139 SUCCESS.
- Student public L0/L1 [#44565651247](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44565651247), [#44565651414](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44565651414) PASS, 실제 Gazebo L2 실증과 구분.

## 4. 실제 L2 및 미검증 항목

동일 공개 코드 SHA 실 Gazebo L2 [#44566309993](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44566309993) 검증 예정/진행. 필요한 판정: 원본 JSONL의 Nav2 READY 직후 native/raw/safety ≤300ms, Student Raw/Safety 20초 ≤300ms, Nav2 관리 ACK, CM/Guard/Supervisor/Gazebo native exit0, witness unsubscribe, Goal/Fault 없음, artifact SHA256 보존.

C09은 아직 개선 인과의 실증이 아님. 실제 NVIDIA WSLg D3D12 Gazebo SIGSEGV 최초 core stack은 미확보, 강사 WSL2 L3 NOT_RUN. 사용자의 SW stop != certified E-Stop.

`D06_GAZEBO_LIVE_RELEASE=HOLD`
`AXIA_MVP_DEMO_ACCEPTED=HOLD`
`CERTIFIED_ESTOP=false`

## 5. 실제 Gazebo L2 완료 — C09 엄격 인수 FAIL (추가 원본 RCA)

실제 Run: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44566309993
tested SHA 84af2ea35ac439b6cf665b323c8d8d19f77a9067, artifact #14552316501.

- CI 선기동 GUI + 공식 Nav2 READY host monotonic171.630초 이후 native/ROS 20초 관측에서 Scan300 위반 없음 (post_ready_proxy=NO_ROS_TTL_VIOLATION_WITNESSED).
- 독립 ROS Safety의 whole-session 첫 위반은 READY 이전 28.200→28.302초 source pair에서 405.049ms이고 Gazebo native106.244ms, Raw431.115ms, Clock RTF1.002108. READY 전 독립 관측 범위는 별도 보존.
- Student qualified 20.114초 Raw203 max 365.814ms / Safety202 max 365.478ms, 거리 Safety202/202 CLEAR; Scan300 FAIL.
- **Student 최초 위반** source stamp 52.302→52.401초: Student Safety gap365.478ms, Gazebo native100.544ms, 독립 ROS Safety102.191ms. 두 번째 Student callback이 독립 peer보다 263.015ms 늦음. AFTER_INDEPENDENT_ROS_RECEIPT 경계. 오프라인 geometry로 이전보다 gap이 감소했어도 300ms 엄격 인수에 실패하므로 geometry 단독 root 가설은 기각.
- Global /clock RTF 약0.999343; 이것은 개별 ROS callback 300ms 준수 증거가 아님.
- Navigation SHUTDOWN ACK1.856059s, Localization manage_nodes SHUTDOWN 한 번 전송 후 30.000354s SERVICE_TIMEOUT. 같은 manager get_parameters 24.207ms, 동일 callback group is_active 27.966ms 응답 (is_active=true). 실제 RMW=rmw_fastrtps_cpp. SHUTDOWN 자체 ACK가 없으므로 정상 관리 종료 아님; DDS/RMW root 가설은 아직 UNDETERMINED.
- CM native child exit0와 부모 graceful marker는 전체 시연 인수를 뜻하지 않음. WSLg GPU Gazebo SIGSEGV 첫 core stack 미확보.

## 6. C09 판정 및 다음 단일 가설

L0 134/134 PASS는 ROS-free 계약 내 유효. 실제 L2는 FAIL이므로 출고 HOLD.
다음은 이미 존재하는 CPU affinity / DDS-RMW 관련 브랜치에서 실제 개선 근거가 있는지 조사하여 재사용 후보 선정.
고정 안전 TTL300/CM120/Guard150, 공식 Nav2, TB3 센서 10Hz 변경 금지. Timeout 확대, SHUTDOWN 재요청, 단순 현장 반복 금지.

D06_GAZEBO_LIVE_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
