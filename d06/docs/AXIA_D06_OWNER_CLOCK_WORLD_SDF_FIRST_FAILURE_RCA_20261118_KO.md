# AXIA D06/G07 — WSL2 /clock 첫 오류 및 월드 SDF Launch 회귀 개발 보고서

2026-11-18 KST · 교육용 MVP · 공개 CI 기반 RED → GREEN → REFACTOR → REVIEW → COMMIT

## 기준 원본과 무결성

- 강사 Owner 원본: `d06-moving-EJ3xmCNP.tar.gz`, SHA256 `d41d041c29e923e765bf075d5ac30ac917c5d8328b38b95b57986b89d04d01ca`. 첨부 `.sha256`와 완전 일치.
- TAR 내부 `SHA256SUMS` **30/30 PASS**, `native/SHA256SUMS` **22/22 PASS**.
- 실제 Launch 원본 `native/launch.log` **첫 오류 2개**: `G07_TASK02_SIMPLE_TF_SIM_ONLY_AUTHORITY_DENIED` 및 `[Errno 2] No such file or directory: '/tmp/nav2_ulg0sey2.sdf'`. 기록에는 단일 선행 원인이라고 단정할 만큼 더 상세한 타임스탬프가 없음; 독립적 코드 불변조건 2건으로 추적한다.
- 이후 `staged_startup.log`: `P2_STAGED_NO_GOAL_BLOCKED: CLOCK_READY: CLOCK_MISSING`, `clock_diagnostics.json`: wall **45.001s**, samples=0, advances=0, sim time ns=0. Clock timeout은 최초 실패가 아닌 결과.
- rosbag sqlite 실제 기록: `/tf_static` 1 메시지, `/tf` 0, **/clock 0**. 시작 로그 `G07_CI_OWNER_BAG_RECORDING_STARTED actual_topics=14`는 구독을 요청했다는 사실일 뿐 SQLite 14-topic PASS 증거 아님.
- Native S02 witness: 15,997 Gazebo update cycles, Contact 0, missing_iterations=0, sensor_found=true. Gazebo 엔진 **일부 루프**는 구동했지만 ROS 시간 브리지 수신 및 Nav2 준비가 정상임을 뜻하지 않음.
- `startup_verdict.json`은 `goal_sent=false`, Gazebo acceptance NOT_ACCEPTED. 실제 Goal·CM Guard 120/150ms·SLOW/STOP/Cancel/양 Lifecycle ACK 검증 **NOT_RUN**.

## 두 최초 실패의 코드 계약

A. 정확한 Student G07 public ref `e9adb73d658859a53976d9848aa75bd5be710def`의 `ros2_ws/src/axia_safety_bringup/launch/axia_p2_launch_policy.py`는 Owner simulation-only simple TF에서 `AXIA_P2_G07_RELOCATED_OBSTACLE=1`을 요구한다. 기존 D06 Owner wrapper `a9f3fff0e285d8517abdf04bb724de5d653318ca`는 `AXIA_G07_TASK02_SIMPLE_TF_CANDIDATE=1`만 내보내고 relocate flag를 누락해 Launch 값 예외가 발생했다.

B. Official Jazzy `nav2_bringup/launch/tb3_simulation_launch.py`는 world Xacro 출력 `/tmp/nav2_*.sdf`와 Gazebo server를 독립 ExecuteProcess로 즉시 시작한다. 기존 AXIA 자체 D07-H01의 `OnProcessExit` 순서 보정은 `AXIA_D07_H01_GUI_NO_GOAL=1`에만 적용되어 G07 Owner/Moving CI는 임시 파일 생성과 Gazebo 읽기 경합에 노출됐다. [Official Nav2 #5350](https://github.com/ros-navigation/navigation2/issues/5350)와 동일 종류의 임시 SDF Race다. 본 원본에서는 TF 거부와 파일 누락 모두 기록되어 있으며 불필요하게 인과관계를 하나로 단정하지 않는다.

## 공개 CI RED 근거

- 새 `d06/tests/test_d06_owner_clock_first_failures.py` 5개 조건: 실제 승인된 world fixture 및 wrapper flag, G07 공식 Simple TF 권한 구성, Owner+CI moving Launch 순서, 원래 D07 NO_GOAL 유지, /clock 실패의 성공 승격 방지.
- 실제 [공개 RED #44272348265](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44272348265): 새 5개 중 **2개 FAIL**. 정확히 `test_owner_relocated_world_flag_matches_real_frozen_fixture`와 `test_owner_launch_orders_xacro_before_gazebo_and_fails_closed`. 기존 성공 계약 테스트는 보존.

## 최소 수정 (후속 GREEN·CI 최종 판정 별도)

1. D06 Owner wrapper에서 검증된 G07 물리 world `axia_p2_g07_obstacle`의 좌표(-0.58,-0.5) 및 기존 Exact Blob 불변 조건에 한해서 `AXIA_P2_G07_RELOCATED_OBSTACLE=1`을 내보내고, 실제 수동 TTY Goal 이전에 검증한다. CI 권한 위장 없음.
2. G07 Student `axia_tb3_p2.launch.py`의 기존 `_order_h01_world_xacro_before_gazebo`를 D07 H01 외에 **G07 Task04 Owner 또는 실제 공개 CI Moving**만 적용. OnProcessExit 이벤트에서 Xacro returncode=0, 임시 SDF 파일 실제 존재/크기/유효 XML+world element 검사 후 Gazebo 서버를 시작한다. 실패면 `Shutdown`으로 Fail-closed, NO_GOAL. 원래 공식 Nav2/Gazebo/CM/Guard 코드는 수정하지 않음.
3. 실제 Jazzy Launch 객체 기반 단위 테스트에서 Owner·CI 허용, 비인가 모드 유지, Xacro 실패/임시 SDF 누락/손상 Gazebo NO_START, 정상 SDF Gazebo START를 검증한다.
4. 공개 원래 G07 Task04 단일 Moving native L2 workflow는 **수정 Student exact SHA**로 다시 실행하고 기존 21가지 실제 Gazebo/RViz/Goal/RMW source CM120/Guard native age150/Scan300/S02 Contact0/SQLite14/UUID Cancel/Navigation+Localization ACK/CM exit0 검증을 모두 요구한다. 실제 ROS /clock 수신을 포함한 전파 주기를 검사. Xvfb GREEN≠Owner WSLg L3.

## 수정의 안전 경계 및 출고 규칙

- 코드 범위: D06 Owner env flag 1줄, Student P2 Launch 이벤트 순서 및 File validity gate, 해당 실패의 필수 L0 테스트, CI workflow, 이번 교육 보고서.
- 불허: 이미 성공한 G07의 Goal 엔진 재작성, Guard/CM Scan TTL 변경, 정적 메시지만 출력한 PASS, 기다리는 시간 늘리기, 임의 SDF 생성, 원본 증거 공개 업로드, CI Goal 승인 위장.
- 공개 CI 정상 통합 **GREEN 이전** 새 WSL2 스크립트 SHA를 공개하지 않는다.
- 승인을 얻지 않은 main 병합·학생 답안 누출 금지.
- 현재 실제 강사 WSL2 Owner L3 = NOT_RUN, SW Stop != 인증된 E-Stop, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.
