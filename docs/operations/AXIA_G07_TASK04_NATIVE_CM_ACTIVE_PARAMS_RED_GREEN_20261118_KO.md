# AXIA G07 Task04 — 실제 CM 파라미터 서비스 재발견 실패 최소 수정 (2026-11-18 KST)

이 문서는 Task04 공개 CI Moving Goal 개발에서 **가장 먼저 실제로 실패한 계약**을 기준으로 한 교육용 인과관계 보고서다. 원본 CI에 없는 내용을 성공한 것으로 보태지 않는다.

## 1. 증명된 이전 성공과 최신 실패

- Task03 공식 Gazebo/Navigation S02 단일 실행 성공: [#44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904). 코드/증거 보존.
- Task04 NO_GOAL GUI 별도 성공: [#44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061). 강사 WSL2 NO_GOAL 육안 수용은 Moving Goal L3를 의미하지 않는다.
- Task04 실제 Moving Goal + Gazebo/RViz Xvfb 단일 성공: [#44259558479](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44259558479), Student `b274d7c075a570c649697ed5fe55166f2296f8f6`, 당시 22개 L0 및 실제 L2 PASS. 이후 소스 변경으로 새 SHA의 통합 PASS를 뜻하지 않음.
- 이후 Owner용 S02 Contact witness 분리 + GUI 저우선순위 + 라이프사이클 응답 원시 계측을 반영한 새 Student `14cb3dbacd134d180e78778a0b75e6a4fbc8bd41`: 실제 L2 [#44263077295](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44263077295) **실패**. S02/Goal/주행 이전에 중단.

## 2. 원본 로그의 실제 최초 실패 경계

같은 실행에서 **순차적으로** 확인된 원본 출력:

```text
P2_NO_GOAL_STATIC_AND_RUNTIME_READINESS_OBSERVED
AXIA_G07_TASK04_GAZEBO_SERVER_SINGLE_GUI_CLIENTS_ATTACHED
Double value is: 5.0
AXIA_G07_CI_REAL_CM_STOP_ZERO_WINDOW_5S_GUARD_TTL_150MS_UNCHANGED
Wait for service timed out waiting for parameter services for node /collision_monitor
AXIA_G07_TASK02_SIMPLE_TF_TIMEOUT_READBACK_MISSING_NO_GOAL
P2_L2_SMOKE_RC=2
```

여기서 **최초 실패는 두 번째 /collision_monitor 파라미터 CLI의 서비스 발견/응답 대기**다. `G07_CI_MOVING_GOAL_ACTUAL_NAV2_BLOCKED` 같은 최종 Goal 오류가 아니며, Goal 자체가 발행되지 않았음. 동시에 이 증거만으로 CM 노드 사망 또는 Guard 150ms 위반을 주장할 수 없다. 첫 번째 CM `stop_pub_timeout=5.0` 실제 서비스 답변은 도착했다.

원본 전체 ROS log/SQLite는 GitHub Actions 일시 실행 환경에 있고 공개 artifact에는 허용된 수치/빌드 SHA만 올라간다. 이전 실행의 원본 파일 해시가 없는 곳에 SHA를 꾸며 기록하지 않는다. 해당 실패의 공개 GitHub Actions artifact [#44263077295](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44263077295/artifacts/14408828199) ID 14408828199는 수치 증거 **부분본**이며 ROSBag 원본이 아니다.

## 3. 시니어 가설 및 공식 근거

실패한 `scripts/p2_no_goal_smoke_ci.sh`는 `ros2 param get /collision_monitor` 호출을 4번 순차 실행하도록 되어 있었다. 매번 새 CLI 프로세스/그래프 discovery를 거치기 때문에 GUI·로봇 시뮬레이션이 동시 실행되는 환경에서 일시적으로 발견이 지연될 가능성이 있다. 이 가설은 **원본 첫 응답 성공 + 두 번째 서비스 대기 실패**를 설명하지만 원인을 유일하게 입증하지 않는다.

- ROS 2 Jazzy 공식 파라미터 문서: `ros2 param`은 각 노드의 서비스 API를 사용한다. https://docs.ros.org/en/jazzy/Concepts/Basic/About-Parameters.html
- 공식 ROS 2 Python 서비스 클라이언트: `create_client`, `call_async`, `spin_until_future_complete`로 단일 클라이언트 응답을 수신한다. https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Service-And-Client.html
- upstream 유사 경험: CLI의 노드 발견 타이밍 때문에 FastDDS 환경에서 false-negative가 발생할 수 있다는 https://github.com/ros2/ros2cli/issues/799 . 단, 본 Task04와 완전히 같은 현상이라고 단정하지 않는다.

## 4. 최소 RED → GREEN

**RED**: Student `13153a104d8cda725a2bdab476130405d4fd4ba8`; 공개 CI [#44263912062](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44263912062)에서 신규 모듈 부재로 `ModuleNotFoundError: p2_g07_cm_active_param_readback` 1건을 포함한 실패 확인.

**GREEN**: Student `637555b9871091c4adbe5a5f9b218e689666a9e5`에서 단일 네이티브 `rcl_interfaces/srv/GetParameters` 구현. Student `486ec02e8e0762e9abefd3063b5d25b2ff5f1fb8`에서 기존 Shell의 네 CLI 프로세스를 한 Python 서비스 요청으로 대체. 공개 L0 [#44264145131](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44264145131) GREEN: 신규 정확 값/타입 검사 3/3 및 기존 계약 통과.

단일 요청은 `stop_pub_timeout=5.0`, `base_shift_correction=false`, `transform_tolerance=0.2`, `source_timeout=1.0`의 실제 런타임 응답 타입·값이 **모두 정확할 때만** 통과한다. 비정상 ACK·서비스 미발견·데이터 누락 시 Goal 전 fail-closed. 스케줄러·소프트웨어 E-Stop·CM120/Guard150/Scan300 안전 TTL을 변경하지 않는다. 각 실제 조회 원본은 `g07_active_cm_native_parameters.json`, `g07_active_cm_native_parameters.log`로 보존한다.

**REFACTOR/REVIEW**: 동일 조건 반복 코드만 제거. 공식 Nav2/CM/Guard 및 안전 FSM 변경 없음. 한 번의 네이티브 서비스 ACK가 실제 CM/Guard 전달 주기의 증거를 대체하지 못하므로 반드시 같은 L2에서 후속 안전 주기를 검증해야 한다.

## 5. L2와 Owner 미검증 범위

출고 후보에 대한 공개 CI 실제 Jazzy/Gazebo/Nav2/Waffle+Xvfb 단일 L2: [#44264236859](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44264236859), Student SHA `486ec02e8e0762e9abefd3063b5d25b2ff5f1fb8`. **본 문서 작성 시 실제 종료 판정은 미기입, PASS 승격 금지**.

Owner WSL2/WSLg는 실제 이른바 GUI 최초 실패의 후속 성능 경계, 사람의 controlling-TTY Goal 승인 및 동일 세션의 Contact·rosbag·Lifecycle 증거를 확인해야 한다. 새 SHA의 공개 L2와 원샷 L0가 모두 통과하기 전에는 실행기를 배포하지 않는다.

```text
AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

## 6. 주니어 개발자 프롬프트 예시

> 실제 Gazebo와 RViz가 동시에 실행 중이고 공식 CM Lifecycle가 정상인 상태에서 첫 번째 `ros2 param get`은 성공했으나 두 번째 실행의 DDS service discovery가 timeout했다. 최종 shell rc만 보지 말고 최초 서비스 미응답을 원본으로 고정하라. Node 탈락·TTL 초과라고 단정하지 말고 네이티브 GetParameters 서비스의 **한 번의 실제 응답으로 4개 정확한 현재 값**을 검사하는 L0 RED를 만들고 GREEN 후 같은 소스 SHA로 실제 Gazebo L2의 CM120/Guard150/odom/Goal UUID/Localization ACK를 검증하라. 어떤 ACK도 꾸며내지 말 것.
