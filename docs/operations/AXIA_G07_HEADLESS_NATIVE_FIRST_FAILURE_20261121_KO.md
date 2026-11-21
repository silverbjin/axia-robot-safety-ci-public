# AXIA G07 Headless Gazebo 실제 0/2 최초 실패 경계 기록

날짜 2026-11-21. 상태: HEADLESS_NATIVE_L2=0/2_FAIL, GUI_PRESENT_NATIVE_L2=2/2_PASS, OWNER_WSL2_L3=NOT_RUN, MAIN_NOT_MERGED.

## 같은 Student Source / 다른 GUI 조건

- Student 소스: 5667575aac777c374735b1c351445bcc8f83140e. Robot/CM/Guard/Nav2/TTL/Goal 동일, G07 깊이 센서 기본 OFF.
- 이전 GUI-present Native Gazebo 실제 2/2: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44902396373 ; Public head SHA 09ea6cbc8b9079532ef13c0962d193966e99a03b. 독립 두 Cycle 모두 성공, Guard CM internal age 19.131/42.611ms, 실제 Goal/Cancel, CLEAR→SLOW→STOP, odom dwell≥1초, Nav/Loc 종료, child exit0, depth OFF 및 실제 LiDAR/safety Scan 관측.
- GUI-OFF Native: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44903962133 ; Public head SHA 9edf630771768dde499f5f67ed6015d5eeb23e54. workflow env의 AXIA_G07_TASK04_CI_GUI_MOVING=0, QT_QPA_PLATFORM=offscreen 변경 외 같은 Student. 두 Cycle 모두 runner rc2, GUI windows 0/0, Native result 0/2 FAIL.
- RED Public #44903906267: 1 fail / 335 pass / 3 skip. GUI-off workflow static GREEN Public #44903967205: 336 pass / 3 skip. 정적 GREEN을 실제 Native PASS로 승격 금지.

## 최초 실패 (마지막 예외 아님)

- Cycle1: SCAN_PREFLIGHT_STREAM_DISCOVERY_TIMEOUT, read-only Scan observer 샘플 0, 그러나 실제 run rosbag /scan=559 messages. Gazebo+ROS bridge publisher 존재; read-only observer의 DDS 발견/수신/실행 원인 미확정. Goal 미발행.
- Cycle2: 최초 /clock 수신 간격 333.63413ms >300ms, odom 357.160233ms >300ms, Scan read-only 수신 간격 378.402543ms, Scan header 99ms. Original exact pair ROS bag은 OBSERVER_RX_GAP_NOT_REPRODUCED_IN_BAG_CANDIDATE_HOLD. 즉 Scan source generation 고장 확인된 것은 아님. /clock, /odom이 기존 정식 300ms 기준 초과이므로 Goal 차단이 맞음.
- 최초 FSM 상태 전이 및 운용 후 TTL은 Goal 이전이어서 미관측. GUI가 없어서 차단된 것이 아님. 저비용으로 허용할 수 있는 정상 headless 시연의 충분한 증거는 현재 미확보.
- Headless original artifact Cycle1 ID 14706907411, ZIP SHA256 c2993ea9c5272a81493eb4ccc54a1836573010e105cf01d53fdffdef3060f19d.
- Headless original artifact Cycle2 ID 14706134989, ZIP SHA256 8bcc8983e336c9677d274e5c41e269a1121efb7ca54538c2d085ff6805bbf86b.
- GUI-present PASS artifact Cycle1 ID 14706572120, SHA256 eb7af3056c768ad662cf7f20c7587f1ca47458130c6dfe0debcf0014e7e61c2f.
- GUI-present PASS artifact Cycle2 ID 14706751374, SHA256 a85b4477315a492fa0ce5892a119ba48f1332f82b7af9b181707d10967fe36d6.

## Scope & guardrails

1. GUI 창/렌더러 자체는 formal acceptance gate에서 제외. GUI 비정상만으로 차단하지 않지만 필수 sensor/safety evidence가 모자라면 NO_GOAL.
2. Scan wall>300ms은 진단. 실제 Scan Header missing/reversal/staleness, 운용중 scan freshness, /clock/odom300ms, CM/Guard TTL 모두 유지.
3. G07 단일 session temporary SDF만 RealSense depth OFF, 공식 원본과 다른 수업 활성화 경로 보존. GUI-present actual 2/2에서 G07_REAL_DEPTH_ABSENT_SCAN_PRESENT_PASS 실증.
4. Localization STARTUP ACK timeout은 원본 기록 및 읽기전용 map_server/amcl ACTIVE, 실제 AMCL pose 및 TF 준비 후 Goal 대체 경로로 구현. 타임아웃 대체 자체가 실제 native에서 발생하지 않아 그 분기 검증은 미완. Nav/Loc 종료 ACK는 그대로 검수.
5. 새 Executor, Fake Scan, 수동 Goal bypass, E-Stop 인증 주장, Clock/Odom timeout 완화 금지. 근본 RMW/Observer callback 정체는 아직 UNDETERMINED.

## 출고 판정

GUI-present native 실제 2/2는 명시된 **그 범위만 PASS**. GUI-OFF real headless 0/2는 별도 HOLD. 기존 성공한 release 범위를 보존하되 headless 결과를 PASS로 표기하거나 강사 WSL2 완료로 승격 금지. 교사 WSL2 L3 원샷은 아직 NOT_RUN. 실패 재발 시 본 CI 사례를 회귀로 우선 유지, 현장 반복 시도 금지. Software STOP은 certified hardware E-Stop이 아님. Main merge 없음.
