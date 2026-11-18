# AXIA G07 Task04 — 실제 Gazebo Moving Goal 최초 실패 경계와 최소 회귀 (2026-11-18)

문서 용도: 주니어 ROS 2 개발자가 시니어의 **증거→가설→RED→GREEN→검증 범위** 판단을 그대로 재현하는 교육용 보고서. 공식 Nav2·TurtleBot3 Waffle·Gazebo Harmonic과 기존 Supervisor/CM/Guard 경로 재사용. 이 문서 자체는 L3 출고 증명이 아니다.

## 고정 성공과 신규 실패는 분리한다

- 기존 Task03 실제 S02/SQLite14/CM120/Guard150/UUID5/Lifecycle L2: [#44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904), Student `01752add2e30c90c4d3286ef3a450f97746ecb55`.
- 기존 Task04 NO_GOAL Gazebo/RViz GUI: [#44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061). 현장 GUI 단독 육안 인수는 별도 성공.
- 새 Task04 Moving + GUI 실제 L2 최초 성공: [#44249348860](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44249348860), Student `1129cd8804954fd6481d1b6b4ebf0e0b98c68c3c`, 원시 수치 artifact ID 14403685546. 원본 runner rc=0, 두 GUI 창, Action/CM/Guard/Contact/SQLite/종료 strict oracle PASS. **다른 SHA의 통합 성공은 이후 변경 코드의 L2 PASS가 아니다.**
- CI 공개 숫자·SHA 자료 외 원본 bag, 사용자 WSL2 로그, 개인 식별 자료는 공개 저장소로 복사하지 않는다.
- 현재 목표는 같은 Student `b274d7c075a570c649697ed5fe55166f2296f8f6`로 변경 경계 포함 실제 L2 1회 확인; 현장 Owner Moving L3는 아직 미실행이다.

## 사이클 3: GUI가 정상인데 Goal 이전 ASSERT에서 막힌 이유

**원본:** [Run #44250223189](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44250223189), 실제 Waffle/Nav2/Gazebo + Xvfb. `P2_STAGED_NO_GOAL_READY`, GUI 창 2개, `AXIA_G07_OWNER_PREGOAL_PHYSICAL_L2_PASS_NO_GOAL`, `G07_TF_LISTENER_REGISTERED_BEFORE_EXECUTOR` 이후 마지막 메시지 `AXIA_G07_PUBLIC_CI_MOVING_GOAL_BLOCKED AssertionError:`. 실제 Goal 발행 전. 기존 FSM `BOOT_SAFE`는 Goal 전 정상 상태이고 안전 위반 증거가 아니다.

**최초 경계/가설:** `tools/p2_g07_ci_moving_goal.py`의 Goal 전 `assert start_pose is not None`에 도달. 새로운 Observer는 `/scan`·`/clock`·DDS publisher graph가 준비된 직후에도 `/odom`을 실제 수신하지 않았을 수 있다. 공식 ROS 2 Jazzy sensor-data QoS는 BEST_EFFORT/작은 큐이며, graph discovery와 새 subscription callback 도착은 별도 사건이다. 참조: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html 및 https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Executors.html.

**RED:** Student `0fc79be43cdb8387571a3912d563f86c8f6b703d`, L0 [#44258289230](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44258289230), 새로운 실 odom 조건 검사 부재로 총 3 테스트, 8 AttributeError (subTest 포함). 누락 odom·1샘플·300ms 초과·미래 수신시각을 모두 fail-closed로 요구.

**GREEN:** Student `a1ef4e72c7de5b440f25258015dc22368954f4c8`, L0 [#44258424215](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44258424215): 기존 Shell 5, Owner CLI 4, Simple TF 6, 신규 Odom 3 = **18/18 PASS**. 변경은 **Goal 전** 새 Observer의 /odom 2회·최근 수신 300ms·두 수신 사이 최대 300ms를 최대 4초 한도에서 실제 callback으로 확인하는 것뿐. 이후 안전 TTL/Watchdog, 센서 주기, 공식 Nav2는 불변.

**실제 L2 영향 확인:** [#44258495534](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44258495534). 이전 AssertionError가 재발하지 않고 `AXIA_G07_TASK04_REAL_OBSERVER_ODOM_READY_BEFORE_GOAL` 출력. 실제 Goal UUID `8e31774bb826458d898429f3f37e5e4a` 전송, CLEAR→SLOW→STOP, Gazebo obstacle ACK, odom 이동 `0.2024m`, STOP 후 ZERO `1.034s`, ActionStatus `CANCELED(5)` 및 소스/Observer/Guard/Scan/Odom/Clock 안전 주기 계측 성공. **하지만 정식 Nav2 종료에서 Navigation ACK 이후 Localization SERVICE_TIMEOUT 발생했으므로 전체 통합 L2=HOLD.** 마지막 전체 프로세스 rc=3만 보고 Goal/Stop 실패로 잘못 진단하지 말 것.

## 사이클 4: 정상 Goal 이후 Localization 종료 ACK 손실

**원본 최초 종료 경계:** 위 [#44258495534](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44258495534) `G07_NAV2_ORDERED_SHUTDOWN status=BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT, navigation_ack=true, localization_ack=false`. 기존 Task03에서는 오래된 13s 응답 한도 실패를 확인해 Nav2 절차용 30s 내부 한도를 이미 확정했다. 이 타임아웃을 추가로 무제한 증가시키거나 응답 없이 ACK를 조작하지 않는다.

**단일 가설:** 신규 GUI 경로가 먼저 `gz sim -g` 및 `rviz2` 클라이언트에 SIGINT를 보내고 `wait`한 뒤 공식 Nav2 두 Lifecycle Manager를 종료한다. GUI 선종료가 종료 DDS/시뮬레이션 진행에 불필요하게 간섭할 가능성이 있으므로 **동일 세션의 관리형 Nav2 ACK와 CM 아동 프로세스 종료가 끝날 때까지 GUI를 유지한다.** 이것은 조사 가능한 가설이지, 해당 서비스 timeout의 유일한 원인으로 확정한 사실이 아니다.

**RED:** Student `cebdfb8049630420a7ca606672404fcd2bba4c93`, 공개 [#44259363216](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44259363216): 원본 정리 함수의 `gui SIGINT`가 `p2_g07_ordered_shutdown.py` 및 `p2_g07_owner_shutdown_audit.py`보다 앞에 있음. 2개 중 순서 회귀 1 FAIL.

**GREEN:** Student `b274d7c075a570c649697ed5fe55166f2296f8f6`, 공개 [#44259506174](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44259506174) L0: Shell 5 + Owner 4 + Simple TF 6 + Odom 3 + GUI 종료 2 = **20/20 PASS**. 변경 파일은 `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh`. GUI client 종료 코드를 Nav2 Lifecycle/CM process audit 이후로 이동한 것뿐이며, PID가 명확한 이 세션의 GUI만 종료한다. 프로세스 전역 종료, Goal 중복, watchdog·TTL 완화 없음.

**실제 L2 검증:** 공개 CI [#44259558479](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44259558479), Student `b274d7c075a570c649697ed5fe55166f2296f8f6`. 결과 확인 전까지 PASS로 표기하지 않는다.

Nav2 공식 근거: https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/configuring_lifecycle_manager/ ; lifecycle shutdown과 관리 서비스의 구조는 https://api.nav2.org/nav2-jazzy/html/md_nav2_lifecycle_manager_README.html. 서비스 호출 timeout이 반드시 실제 lifecycle 전이 미완료를 의미하는 것은 아니라는 upstream issue https://github.com/ros-navigation/navigation2/issues/6556 은 **해석상의 주의 사항**이며, AXIA는 여전히 실제 ACK 없이 PASS를 허용하지 않는다.

## 공통 REVIEW 체크

- 동작 변경은 새 구독자의 Goal 전 odom 수신 gate와 GUI teardown ordering, 두 곳에 국한.
- 단일 Goal UUID는 Supervisor 발행, 정확한 취소는 원래 `_task03_exact_goal_terminal`에서 ActionStatus=5 요구.
- 공식 Nav2, sensor 구독 QoS, Collision Monitor, Guard TTL=150ms, source↔observer 120ms, Scan/Odom/Clock 300ms 경계 불변.
- ROS graph/GUI window는 실제 odom·Contact·Action의 대체 증거가 아니다.
- 오래된 단일 성공을 새 소스 통합 PASS로 승격하지 않는다. CI Xvfb는 WSLg GPU L3와 다르다.
- 원본 시연 전체 archive/SHA256은 강사 WSL2 HOME 아래에만 보존한다. 원본 제출 및 육안 검수 전 MVP=HOLD.

## 후배 개발자에게 주는 재현용 프롬프트

> 다음 실패는 최종 `AssertionError`가 아니라 최초 수신 누락을 찾아라. 새로운 ROS 2 Observer가 DDS publisher를 발견한 시각과 실제 /odom callback 2회를 별개로 확인하고, Goal 전 실제 수신 timestamp가 300ms 이내라는 최소 RED를 작성하라. 통과하더라도 Nav2 lifecycle ACK를 포함한 단일 Gazebo 통합 테스트가 실패하면 전체 PASS로 승격하지 말라.

> 실제 안전주행이 성공한 뒤 Localization service timeout이 발생하면, 우선 SLOW/STOP/Guard 내부 나이를 재진단하지 말고 서비스 호출 순서와 GUI 자식 프로세스의 종료 순서를 비교하라. ACK 없이 성공으로 오인하지 말고 테스트로 순서를 고정해 단일 L2에서 검증하라.

현재 상태: `AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`, `MAIN_MERGED=false`.
