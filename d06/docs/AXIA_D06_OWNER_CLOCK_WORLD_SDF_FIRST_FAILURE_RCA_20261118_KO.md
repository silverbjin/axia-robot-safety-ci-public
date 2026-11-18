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


## 최종 GREEN: 실제 수정된 동일 Student SHA와 물리 시연

### 2026-11-18 실제 공개 Native L2 성공

- [Actions #44273028236](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44273028236), public workflow HEAD `6bb4cf2676c1424e6255ba2f8e1f1bdb23019958`, **실제 Student 수정 SHA `c7654a5426ec17e724cc7590f01f8a43206a000c`**, run completed/success, job `134694114168`.
- 동일 workflow에 Jazzy real Launch `tools/test_g07_owner_clock_world_launch.py` 4개가 실제 실행. 사례: Owner/CI 적용 범위, 원래 H01/기본 동작 유지, Xacro exit !=0, SDF 부재/0바이트/유효하지 않은 XML을 실제 `Shutdown`으로 차단, 정상 Xacro+유효 SDF일 때만 `gazebo_server` action 반환. 실제 stdout: `G07_WORLD_XACRO_SDF_READY_BEFORE_GAZEBO`. 이 단위 테스트들은 ROS graph 미기동이며 실제 물리 L2 결과는 별도 같은 Run 단계에서 확보.
- 실제 Gazebo physical plugin, official Jazzy/Harmonic Nav2 Waffle, Xvfb Gazebo + RViz 동시, 단일 Goal, `AXIA_G07_TASK04_NATIVE_ONE_MOVING_RUNNER_RC=0 RVIZ_X11=1 GAZEBO_X11=1`.
- 엄격한 기존 Task04 read-only 21항목 checker 결과 `TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS`, `first_failure=NONE`. 실제 단일 Goal·odom 이동·CLEAR→SLOW→STOP, /clock timestamp 10회 이상 연속 및 실제 시간 진행, CM source+observer<=120ms, Guard native CM age<=150ms, Scan<=300ms, Contact0, 정확 UUID Cancel ACK status5, SQLite14-topic **실제 메시지**, Navigation + Localization ACK, CM process clean exit0 검사에 근거함. 별도 성공 Run들을 합산하여 PASS 만들지 않음.
- 공개 artifact allowlisted numeric `axia-task04-moving-native-numeric-44273028236` ID `14412718399`. 개인 현장 Bag·로그 업로드 없음. 이 Run의 CI Xvfb 성공은 WSL2 WSLg GPU/프로세스 스케줄러 동등성 증명이 아님.

### 2026-11-18 D06 연결 실행기 L0 GREEN

- 공개 브랜치 `fix/d06-owner-clock-l2-candidate-20261118`, D06 스크립트 `d06/scripts/axia_d06_g07_classroom_once.sh`는 Owner에서 **검증된 물리장애물의 relocated world flag `AXIA_P2_G07_RELOCATED_OBSTACLE=1`**을 실행 전 내보냄. Exact Student SHA `c7654a5426ec17e724cc7590f01f8a43206a000c`와 실제 위 새 Native L2 workflow run `44273028236`/HEAD `6bb4cf...`, 수정 Launch Git blob `784a8d188f73ff4ae6d8bde136cfbd8591f942cf`를 이전 소스/Owner admission과 함께 고정하고 Git hash-object로 검사.
- [최종 공개 L0 #44273959319](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44273959319), HEAD `ea69abfb4bee996765be15bd36e2378099e99029`, 완료/success.
- 실제 로그: 기존 Owner/보안/Goal admission 16/16 PASS, 실제 고정 Student parity 5/5 PASS, 실제 Bash/Python heredoc 3/3 PASS, 신규 Clock first-boundary regression 5/5 PASS = **29/29 PASS**. `D06_G07_CLASSROOM_PUBLIC_L0_PASS SIXTEEN_PLUS_FIVE_OWNER_PARITY_PLUS_THREE_HEREDOC_PLUS_FIVE_CLOCK_TESTS NO_ROS_NO_GAZEBO_NO_GOAL`.
- 최초 RED [#44272348265](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44272348265): 5개 신규 회귀 중 2 FAIL, Owner relocated flag 누락 및 Moving Launch가 SDF 순서를 보정하지 않음. 실제 수정 후 L0 + 실제 Native L2로 GREEN.
- 유일한 구현 변경: D06 Owner simulation flag와 공개 Student P2 Launch의 fail-closed 순서. Nav2/CM/Guard/TF/Goal publisher/TTL 포크 또는 E-Stop 기능 추가 없음.

### 현재 검증 수준

- 기존 다른 G07 성공 증거 보존, 최근 새 수정 동일 Student SHA Native L2 완료.
- 새 WSL2 강사 실제 GUI Moving Goal L3 **NOT_RUN**, 결과 `AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false`; 사용자 현장 최초 실패가 다시 발생하면 현장에서 같은 Goal 반복 금지, TAR.GZ/SHA256 원본을 공개 CI 최초 실패 회귀로 편입해야 함.
- 사용자 승인 전 `main` 병합하지 않음. 실제 Owner L3가 끝나지 않았더라도 최신 공개 CI가 성공한 SHA를 강사용 **인수 후보**로만 제공 가능; Owner L3 PASS 및 제품 최종 인수로 보고 금지.
