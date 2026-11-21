# AXIA G07 — G20 실제 Nav2 경로·G25 Guard SIGINT 최초 종료 예외 RCA (2026-11-21)

**최종 릴리스 상태:** HOLD. 이 문서는 한 번의 Native 실제 계측과 좁은 코드 회귀를 기록하며, G30 2/2 또는 강사 WSL2 G50 인수 PASS가 아니다. SW STOP은 인증된 E-Stop이 아니다.

## 1. 검증 원본과 재사용 제한

- 기준 `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`; 공식 TurtleBot3 Waffle, Nav2 Jazzy, Gazebo Harmonic 재사용. Planner/Controller/CM 안전 로직, 기존 Goal, 120/150/300ms 안전 TTL 수정 없음.
- Student Draft [#94](https://github.com/silverbjin/axia-robot-safety-student/pull/94) `fix/g07-g50-first-boundary-student-20261121`; Public Draft [#221](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/221) `fix/g07-g50-first-boundary-ci-20261121`. main 미병합.
- G20 실제 Native [#44881017415](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44881017415), Public SHA `8a138788511963beba90cc999411947ab5f4ec17`, Student SHA `fadb216a55db11301562a93eecf848bdb6688073`; artifact ID `14697692120`, 15,780 bytes, 14일 보존. 절대 시각 clock epoch와 host monotonic 시각 직접 차감하지 않음.
- 기존 Nav2 Jazzy PlannerServer `/plan` (`nav_msgs/Path`)은 **전역경로 시각화**이며 PlannerServer가 구독자가 있을 때 발행한다. 소스: https://api.nav2.org/nav2-jazzy/html/planner__server_8cpp_source.html ; 이 토픽만으로 Nav2 **국소 Controller 궤적**, publisher DDS GID 또는 실제 장애물 충돌은 입증되지 않는다.

## 2. RED→GREEN→실제 L2

- RED pure G20 [#44880654425](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44880654425) → GREEN [#44880779914](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44880779914), **Ran 5 tests / OK**. Student `block_B/day07/h01_runtime/tools/p2_g07_g20_nav2_plan_witness.py` (순수 수치 + thread lock)와 `tools/test_g07_g20_nav2_plan_witness.py`. ROS 노드가 아닌 기존 G07 Observer 같은 노드에 **CI_ONLY** `/plan` subscriber만 추가, 새로운 Publisher/Goal/Fault/Collision Monitor 수정 없음.
- Real Jazzy L1 [#44880894271](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44880894271) **PASS**: 독립 DDS 프로세스에서 nav_msgs/Path 10회 수신, points=6. **L1은 시험용 Path Publisher**이므로 실제 PlannerServer 인수는 아니다. 종료 직전 시험용 publisher의 `ExternalShutdownException` traceback이 로그에 있으나 L1 job 결론 success; clean-exit 검증으로 확대 해석 금지.
- Native L2 Run #44881017415: 내부 Moving runner `AXIA_G07_TASK04_NATIVE_ONE_MOVING_RUNNER_RC=0`, RViz/Gazebo 창 모두 확인, 처음 12초 preGoal Scan `PASS_SCOPED_RECEIVED_SCAN_ONLY`. 그러나 외부 엄격 CI **FAIL**, 원인은 이하 G25 Guard exit1.

## 3. 실제 G20 경로·물리 장애물 동일 시점 수치

Artifact `public_evidence/g20_nav2_global_plan_numeric.json`의 3 phase:
- `PRE_FIXTURE`: 실제 Nav2 전역경로 **42 점**, Path age=0.061599초, 현재 odom→map robot=(-1.87574,-0.49439), yaw=0.143972rad, 가장 가까운 전역경로 접선=1.201353rad, goal 직선방위=1.424705rad. **전역경로와 목표 직선의 방위 차이 0.223352rad**.
- `AFTER_FIXTURE_ACK`: Plan age=0.588997초, 로봇 yaw=0.157174rad, 장애물 중심에서 전역경로 폴리라인까지 **0.567462m**, robot nearest path distance=0.022705m, 전방 실제 LiDAR=1.862432m, Supervisor vin=0.044m/s.
- `SLOW_OBSERVED`: Plan age=0.698507초, 실제 LiDAR front=**0.679519m**, vin=**0.045303m/s**, 로봇 yaw=0.158802rad, 경로 접선 1.201353rad, 경로에서 장애물 중심까지 **0.567462m**. 즉 엄격한 원래 `rows["slow"]=wait(phase("slow"),35,"SLOW")` 단계에서 실제 관측 성공. 이 수치만으로 국소 Controller 경로 위 장애물이라 단정하거나 G20 전체 인수 PASS 승격 금지.
- 이전 actual #44871515361의 회전 중 음수/무전진과 새 Native의 SLOW 성공은 서로 다른 실행. 전역경로 접선과 로봇 yaw의 ~1.04rad 차이는 사실이지만 실제 controller의 추종 방식은 아직 미측정.
- 이번 Run G10 유효 수신 간격 (ms) `scan=202.707616, odom=133.990026, clock=102.645724, pre_guard=63.652148, guard=61.674819, supervised=63.490723, supervisor=63.541949`, **이번 관측 창에서만** 최초 timing breach 없음. 이전 600.502826ms Scan 문제의 root/해결을 뜻하지 않는다.
- 첫 관측 Supervisor 전이 `BOOT_SAFE→NORMAL`, 악화 전이 아니며 Guard latch 없음. 스캔 preGoal `scan=116.700268ms`, `safety_scan=114.52154ms`, max header sim 102ms. E-Stop 인증 없음.

## 4. G25 최초 종료 위반 — 실제 원인 증거

같은 Native #44881017415 외부 CI 최초 실패:
```
AXIA_G07_TASK04_NATIVE_ONE_MOVING_RUNNER_RC=0
AXIA_G07_NATIVE_STRICT_PREG0AL_12SEC_SCAN_WALL_PASS
AXIA_G07_NATIVE_L2_CHILD_DIED_DURING_TEARDOWN=p2_base_guard_node
[p2_base_guard_node-21] p2_base_guard_node.py:158 self._status.publish(status)
rclpy._rclpy_pybind11.RCLError: Failed to publish: publisher's context is invalid,
    at ./src/rcl/publisher.c:423
[ERROR] [p2_base_guard_node-21]: process has died [pid 2374, exit code 1 ...]
```
- 기존 `ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_supervisor_node.py`는 `is_context_waitset_shutdown` **와** `is_context_publish_shutdown`을 모두 사용, 하지만 Guard는 WaitSet 분류만 호출. 기존 `p2_shutdown_context.py`에 정확한 Jazzy SIGINT-invalid-context publish classifier가 이미 존재한다. **새 알고리즘 작성 없이 기존 검증 함수를 Guard 종료 경로에 재사용**한다.
- 소스 변경: `ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_base_guard_node.py`의 `main` 예외 경로만 수정. _tick, Guard ZERO/TTL, ROS Publishers/Topics, Goal, Nav2, DDS 변경 없음.
- Live context에서 `RCLError`가 발생한 경우는 그대로 **fatal**. `rclpy.ok() is False`이고 정확한 `Failed to publish: publisher's context is invalid` 패턴만 종료 중 허용. Guard 자체가 죽거나 ROS context가 이미 파괴된 이후의 물리 안전을 보증한다는 뜻은 아니다.
- Student RED test `tools/test_g07_g25_guard_shutdown_publish_race.py`; Public RED [#44881564217](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44881564217) 첫 실패 Guard import 누락 → Student GREEN source `c0a2b4d727383fd97c1541b22238ba67026d70e0`, Public GREEN [#44881623133](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44881623133), **3 새 tests + 4 기존 tests PASS**.
- 변경된 동일 Student SHA로 실제 Native [#44881683566](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44881683566) Public SHA `e7c9716eacd4ed2807930d467fd76664b7eab798` 실행 제출. **최종 실제 L2 verdict 확인 전 G25=HOLD.**
- 이전 #44865087050의 *26초 launch alive* 원인과 이번 context-invalid Guard exit1은 별개의 최초 사건이다. 새로운 수정만으로 이전 26초 사건까지 해결됐다는 증거는 없다.

## 5. CI 실행 경로·명령·미검증

- Public L0: `python3 -m unittest discover -s tools -p 'test_g07_g20_nav2_plan_witness.py' -v`; `python3 -m unittest discover -s tools -p 'test_g07_g25_guard_shutdown_publish_race.py' -v`; `python3 -m unittest discover -s tools -p 'test_g07_context_publish_shutdown.py' -v` (각각 Student `block_B/day07/h01_runtime`에서).
- Public workflow files `.github/workflows/axia-g07-g20-nav2-plan-first-fixture-l0.yml`, `...-wire-l1.yml`, `...-first-fixture-native-l2.yml`, `axia-g07-g25-guard-publish-shutdown-l0.yml`. 최근 Native는 상기 기존 first-fixture-native-l2를 G25 trial로 갱신.
- Native 1회 성공으로 G30 독립 cold-run 2/2 PASS 판정 금지. G10 이전 Native 첫 600ms failure, G20 로봇 실제 path tracking, G25 최종 Guard/Supervisor clean exit 및 이전 26초 launch root 모두 별도 HOLD. 신규 SHA-pinned WSL2 G40 실행기 미출고, 강사 G50 실제 WSL2 NOT_RUN, main 미병합, 인증 E-Stop 아님.
