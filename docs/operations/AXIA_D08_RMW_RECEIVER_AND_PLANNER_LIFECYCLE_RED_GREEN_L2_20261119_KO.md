# AXIA D08 — 첫 Scan 장애 원인 추적 중 발견한 Planner Lifecycle 초기화 경쟁과 RMW 수신자 식별

**2026-11-19 KST / RED→GREEN→REFACTOR→REVIEW→COMMIT / NO_GOAL 실증 범위**

## 1. 변경 전 보존

- 공개 Draft PR [#187](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/187), 코드 `diag/d08-live-rcl-publish-take-20261119`. 기존 성공 #44458214774, SHA `b33e6c43656ec4e2030884795a71b186896e14f6`은 그대로 보존.
- 원래 문제는 #44312306299 `cycle_0000` 최초 ROS Scan callback gap `505.365ms > 500ms`(sim header delta `102ms`). 과거 Owner 518.394ms 첫 위반도 별도로 HOLD.
- RMW source timestamp 6,464건 매칭 및 최대 `0.543278s`은 이미 실측했지만 구독 Node 미식별, CM/Guard 내부 TTL 및 WSL2 L3 미검증. 최초 위반을 나중 정상 시연으로 소급 PASS하지 않는다.

## 2. 수신 노드 신원 추적 RED→GREEN

- 기존 RMW `rmw_take`에 subscription handle만 있어 해당 543ms가 실제 D08 observer인지 다른 프로세스인지 불분명했다. 공식 `rcl_node_init`으로 node_handle→node_name, `rcl_subscription_init`으로 node_handle→rmw_subscription_handle를 연결한다.
- **RED** 새 `d08/tests/test_d08_rmw_scan_receiver_node_identity.py`: 실제 익명 PID와 subscription 단서만 있으면 UNKNOWN이어야 하고 노드 초기화 관측이 있을 때만 이름을 인정. 공개 #44459231423 L0 `3 failed, 209 passed`.
- **GREEN** 기존 `d08/scripts/d08_rcl_trace_summary.py` 파서의 node 매핑과 `d08/scripts/d08_ros_trace_live_ci.sh`의 `ros2:rcl_node_init` 이벤트 1개만 추가. 신규 ROS 노드/센서/제어 publisher 없음. 같은 소스 후속 L0 `212 PASS`.

## 3. 최초 실제 Gazebo 실패 경계 — Planner (독립 원인)

- 공개 실제 [Run #44459386016](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44459386016)에서 Gazebo native scene, Waffle RGB-D, AMCL 첫 pose, map→base_link TF까지 정상. 초기 0.65초 executor pause 이후 실제 Scan/Odom/Clock 연속 1초 회복 증명도 보존.
- 하지만 **첫 Path 요청 이전** `D08_PLANNER_REFUSED_PATH_REQUEST`. 실제 공식 Nav2 로그: `planner_server` 구성은 완료되었으나 `lifecycle_manager_navigation`의 전체 활성화 중, **Action server is inactive. Rejecting the goal.**
- 기존 `ActionClient.wait_for_server(timeout_sec=10)`은 action endpoint 존재 확인이지 Planner Lifecycle ACTIVE 증명이 아니었다. GUI 종료 중 SIGINT/다른 프로세스 종료 메시지는 후속 증상.
- 해당 Run의 RMW trace는 FAIL 뒤에도 정상 종료·압축되었고, 유일한 source timestamp 매칭 322건, 최대 `0.461114s`의 수신 노드 `axia_d08_readonly_nav2_path_preflight`를 정확히 확인. 이 read-only Path 노드의 관측을 CM 내부 안전 수신으로 오분류하지 않음.

## 4. Planner 준비 순서 최소 수정

- 다른 작업 브랜치에서 이 정확한 Planner ACTIVE 선행검사를 이미 해결했는지 먼저 검색했으나 해당 재사용 후보가 확인되지 않았다.
- **RED** `d08/tests/test_d08_planner_lifecycle_action_ready.py` 신규. 코드 SHA `1f6639f1cb49cbd4d9bafa02ff40a2a616f22907`, 공개 [#44460301609](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44460301609): `ImportError: assess_planner_lifecycle_observation`. 실제 L2 SKIPPED.
- **GREEN** 기존 `d08/harness/d08_nav2_path_preflight.py`만 수정: 기존 AMCL 및 TF 검증 후 공식 `/planner_server/get_state`를 읽기 전용 GetState로 확인, `active`일 때만 기존 `ComputePathToPose`를 호출. 제한된 준비 대기, 실제 응답 시각과 상태 기록. 임의 고정 sleep, Planner/Controller/Nav2 fork, Goal/Velocity 생성 없음.
- 정확한 검증 SHA **`6cfc076894fb5747931ecebf1bc3eb0838bc5bac`**, 공개 [Run #44460443303](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44460443303):
  - L0 `215 passed in 0.99s`.
  - 실제 `gazebo-official-nav2-oneworld` job SUCCESS, 본래 Gazebo World·공식 Nav2·AMCL·TF·Costmap/Plan, 반복 NO_GOAL **8/8 PASS**.
  - `official_nav2_before_path.json`: `planner_lifecycle.official_planner_active=true`, `observed_states=["active"]`, `wait_wall_sec=0.780997`, `native_service="/planner_server/get_state"`.
  - 8-cycle Scan callback wall max [0.243953,0.243534,0.404020,0.235078,0.242570,0.363134,0.241189,0.236316]초; 첫 >500ms 위반 0.
  - Contact와 YOLO 별도 작업은 변경 범위 밖이므로 **SKIPPED**. 전체 4-job 통합 PASS 아님.
- 실제 Run 원본 증거: L2 artifact `14500071614` (113 entries, ZIP CRC PASS), RMW trace artifact `14500390622` (7 entries, ZIP CRC PASS). RMW 동일 source timestamp 6,285건 매칭, 최대 `0.480625s`, 수신 노드 **`axia_d08_independent_rx_no_goal`**로 식별. 이 값 역시 관측 노드의 계측이지 CM/Guard 안전 TTL 자체를 직접 측정한 값은 아님.

## 5. 검증 경계와 후속 인수

```text
D08_NODE_IDENTITY_L0=PASS
D08_PLANNER_LIFECYCLE_RED=REPRODUCED
D08_PLANNER_LIFECYCLE_L0=PASS_215
D08_REAL_NO_GOAL_NAV2_EIGHT_CYCLE_L2=PASS_SCOPED
D08_RMW_SOURCE_MATCH_COUNT=6285
D08_RMW_MAX_PUBLISH_TO_TAKE_SEC=0.480625
D08_RMW_MAX_RECEIVER_NODE=axia_d08_independent_rx_no_goal
D08_HISTORICAL_505365MS_CAUSE=UNDETERMINED
D08_OWNER_WSLG_L3=NOT_RUN
D08_CM_INTERNAL_RX_GUARD_TTL=NOT_VERIFIED
D08_MOVING_GOAL_E2E=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

다음 작업은 기존 Owner WSL2/WSLg에서 **정확한 코드 SHA**를 고정한 실제 GUI·Scan/Odom/Clock·RMW timing 통합 증거로 인수하는 것이다. 새 오류가 발생하면 첫 안전 전이·첫 주기 위반의 재현 가능한 부분을 공개 CI RED로 먼저 추가한다. 실제 WSL2에서 로봇/화면을 실행한 사실이 없으므로 최종 합격이라고 보고하지 않는다. 현재 공개 source PR #187은 Draft, 사용자 승인 전 `main` 병합 금지. 신규 코드 범위는 오직 trace parser/trace script, Planner preflight 및 회귀 테스트·워크플로에 한정했다.
