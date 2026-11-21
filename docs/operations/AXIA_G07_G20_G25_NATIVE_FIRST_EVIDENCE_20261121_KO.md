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

## 6. 재개 후의 두 실제 Native 실패 비교와 최초 글로벌 경로 변화

- 현재 G20 수정 후보가 아니라 **실제 경로 관측 진단**이다. 원래 Planner/Controller·Goal·CM/Guard·Scan300/CM120/Guard150ms는 변경하지 않는다.
- #44881017415 (실제 주행 단계 rc0, 전체 CI Guard SIGINT exit1): `PRE_FIXTURE` plan 42pts, tangent1.201353rad, robot yaw .143972rad. `AFTER_FIXTURE_ACK` plan 42pts, tangent1.201353rad 유지, cylinder center↔global plan .567462m, supervised 0.044m/s. `SLOW_OBSERVED` front .679519m, supervised .045303m/s. 물리 SLOW 관측은 PASS이나 **G25 Guard 종료 실패 때문에 전체 FAIL**.
- #44881683566 (Student `c0a2b4d727383fd97c1541b22238ba67026d70e0` Guard 수정 적용): 원래 CLEAR/Goal EXECUTING/odom0.12032m 후 물리 SLOW fixture ACK. **최초 실패** `CI_MOVING_GOAL_TIMEOUT_SLOW`, `front` 0.6674m 때 `vin=-0.0142206m/s`, 96 샘플 SLOW zone 최대 vin **0.00058916m/s** (< .005 요구), Guard reason `FORWARDING_MONITORED_CM`. 이후 yaw 2.0221rad, front1.248m, vin.175m/s — SLOW 유효 창에서는 양의 전진이 없음. 전체 L2 **FAIL**, 따라서 Guard 수정이 실제 clean exit를 입증하지 못함.
- 그 실행 Artifact #14697869457의 **실제 global /plan 변화**: `PRE_FIXTURE` 41pts, plan tangent **1.168522rad**, robot yaw .148064rad → `AFTER_FIXTURE_ACK` 66pts, tangent **2.525772rad**, yaw .154047rad, fixture center↔plan **.711331m**, vin.000498 → `SLOW_OBSERVATION_FAILED` 43pts, tangent2.185558rad, robot yaw2.109304rad, fixture center↔plan .6691m. Global plan의 1.35725rad 방향 변경은 실제 관측이며, 이것이 Nav2 Controller **국소 궤적의 원인이라는 인과관계는 미검증**.
- 같은 두 쌍의 최초 글로벌 경로 변화 제한 분류 회귀: Student `tools/test_g07_g20_first_plan_reorientation_native.py` / `tools/p2_g07_g20_nav2_plan_witness.py::assess_first_plan_change`. Public RED #448823... (정확한 ID 확정 시 명시), GREEN [#44882415060](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44882415060) **3/3**, Student SHA `a78be7e2a29c9bb022cbe601607b945c4c191e5e`, Public SHA `2ed2d043deee9e8279ad6dbf133899e200d9c73d`. 이름 `AFTER_FIXTURE_GLOBAL_PLAN_REORIENTATION_CANDIDATE_HOLD`, release HOLD/root false.

## 7. G25 NO_GOAL 종료 전용 재검의 최초 실패가 '종료'보다 앞섬

- 기존 `scripts/p2_no_goal_smoke_ci.sh`의 `AXIA_G07_SHUTDOWN_L2_ONLY=1` 분기를 재사용한 별도 실제 Jazzy/Harmonic native CI로 Moving Goal 단계와 종료 계층을 분리하려 했다. Run [#44882490734](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44882490734) 실패 최종 `G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET`, smoke rc3. 후행 종료 메시지만으로 root 확정하지 않음.
- Public 최소 최초 단계 분류 `d06/diagnostic/g07_g25_nogoal_first_stage.py`, `tests/test_g07_g25_nogoal_first_stage.py`: 기록된 단계 우선 판정, 불충분한 로그는 HOLD, raw 경로/UUID/rosbag 비공개. Public Python 계약 RED [#44882719841](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44882719841) (모듈 부재) → GREEN [#44882756718](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44882756718). 
- 추가 실제 noGoal Native [#44882850643](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44882850643) FAIL. 공개 Artifact `axia-g07-g25-no-goal-exit-44882850643`의 첫 사건 `P2_NO_GOAL_BLOCKED:` → `STARTUP_BLOCKED_BEFORE_TEARDOWN_HOLD`; 최종 launch alive, process group 총 **20** roles (ros2_launch1, gazebo1, guard1, supervisor1, collision_monitor1, navigation_stack12, etc), 원인 미확정. 이는 **시작 실패 뒤 종료 정체**이므로 10초/26초 종료 예산 수정의 직접 근거가 아님. `clean_child_exit_proven=false`; real moving scenario G25 L2 미검증.
- 시험 자체에서 ROS2 정지 상태를 얻기 전에 막히므로 Guard에 실제 SIGINT를 보내는 **독립 ROS Jazzy L1** [#44883090731](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44883090731) **SUCCESS (actual Jazzy Guard process SIGINT exit0 only)** 별도 생성, Public SHA `8832ad5bf4236416393cc2eae865b939f84ed35a`. 기존 Guard _tick/TTL 불변, 실제 Jazzy 프로세스 exit0만 검증. 전체 Gazebo Nav2/CM 26s 종료 검증을 대체하지 않음.

## 8. 완료 조건·범위와 계류

| Gate | 검증 상태 |
| --- | --- |
| G00 | 기존 first-safety-transition / first gap audit 완료 |
| G10 | Real Jazzy L1 기존 D08 take hook PASS, 600ms original RMW root UNPROVEN |
| G20 | 실제 physical SLOW 1회 관측, 다른 실제 session은 96-sample timeout. Root는 global planner reorientation 후보, 국소 controller 미검증. **HOLD** |
| G25 | Guard exact post-SIGINT classification L0 7/7 PASS; 실제 native #448810 Guard exit1, Guard 수정 native #448816 first G20 timeout; noGoal first STARTUP_BLOCKED. **HOLD** |
| G30 | same SHA actual independent cold-run 2/2 PASS 없음 |
| G40 | 새 WSL2 One-shot 출고 금지 |
| G50 | 실제 강사 WSL2 NOT_RUN |
- 사용자의 main 승인 없음, 두 Draft PR을 유지. 실제 CLI/Gazebo 검증을 수행하지 않은 범위는 성공 보고하지 않음. SW STOP != 인증 E-Stop.

## 9. G25 실제 Jazzy 단독 종료 PASS 및 남은 L2 정확한 경계

- 실제 Guard SIGINT L1 [#44883090731](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44883090731) Public exact workflow SHA `8832ad5bf4236416393cc2eae865b939f84ed35a`, Student `c0a2b4d727383fd97c1541b22238ba67026d70e0`: 원본 Jazzy 컨테이너에서 `colcon build --base-paths ros2_ws/src --packages-select axia_safety_supervisor`, 원본 `P2BaseCommandGuard` 실제 ROS 프로세스 실행, `kill -INT "$child"`, process `exit0`, Traceback 없음. L0 `Ran 3 tests / OK`, marker `AXIA_G07_G25_ACTUAL_JAZZY_GUARD_PROCESS_SIGINT_EXIT0_L1_PASS_NO_GOAL_NO_GAZEBO_MOVING_UNVERIFIED`. 실 Gazebo·Nav2·CM는 L1에서 실행 안 함. 특히 L1이 타이밍 경쟁으로 invalid-publisher 예외를 직접 재현했다는 주장은 하지 않음. 그 예외의 정확한 분기는 실 L2 #44881017415 원본 로그와 L0 fake Exception 회귀에 의해 분리됨.
- NO_GOAL native CI [#44882850643](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44882850643) 최초 `P2_NO_GOAL_BLOCKED:`이며 시작 단계가 정리보다 우선 실패. 이번 실행은 초기 상태 준비 실패로 인한 20개 process alive 때문에 **G25 관리 대상 종료 인수로 미적합**; `G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET`는 후행 증상으로 분류. raw private PIDs/files 공개 금지. 10s→26s로 무근거 확대하지 않음.
- 실제 멀티노드 G25 필수 인수는 동일 SHA의 성공한 Gazebo Moving Goal→정확한 UUID Cancel→Nav/Loc ACK→Guard/Supervisor/Collision Monitor 정상 exit0·26s manager clean teardown이 포함되어야 함. 이 필수 범위는 현재 **NOT PASS**.
- 공개 유효 계약: [#44882856888](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44882856888) Public Python contracts GREEN; [#44882415060](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44882415060) G20 numeric 3/3 GREEN; [#44881623133](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44881623133) Guard L0 7/7 GREEN. 이후 이 보고서 변경은 문서 전용이다.
- **G00 evidence audited**, **G10 L1 instrument PASS / root HOLD**, **G20 first global route reorientation numeric PASS / physical SLOW unstable HOLD**, **G25 standalone Guard actual Jazzy exit0 PASS / Gazebo integrated HOLD**, **G30 strict independent actual Gazebo 2/2 NOT PASS**, **G40 owner WSL2 new script NOT RELEASED**, **G50 actual instructor WSL2 NOT RUN**, **main not merged**.

## 10. 다음 유효 작업 단위 (실패 현장 재시도 반복 금지)

- **G20**: native 최초 `PRE_FIXTURE→AFTER_FIXTURE_ACK` 전역 경로 1.35725rad 재지향과 Guard/Supervisor 실제 `vx` 반전을 공통 host-monotonic으로 정렬; 필요시 이미 보유한 native artifact와 Nav2 실제 ControllerServer 기존 로그에서 **local plan/tangent**가 확인되는지 먼저 감사. 실제 local plan 증명 없이 Goal 직선/전역 계획 접선=실행 속도 방향으로 단정하지 않음. 실제 Planner/CM/Guard 개발 확장 금지. 고정 fixture가 global route에서 .567~.711m 벗어남을 고려하되, 정량 증거 없는 임계값/장애물 좌표 변경·재시도 금지.
- **G25**: 성공 Moving run 후에만 해당 프로세스 종료를 실제 검증. NO_GOAL 시작 실패는 별도 HOLD로 처리하고 원인 분리 전 시간 예산/종료 예외 범위 확대 금지.
- **G10**: 기존 #44870974857 Scan600.503ms, Header~102ms, RMW receive~599.696ms 및 독립 bag~107.738ms exact-pair first boundary 증거 유지. Observer D08 take-complete L1 기능은 통과했으나 타이밍 위반 원인 미확정; 연결된 CM120/Guard150/Scan300 수신 간격을 같은 native run에서 검증해야 전체 Gate A PASS 가능.
- **G30→G40→G50**: 전 항목 실제 Native strict cold-run 독립 2/2 PASS로 출고 허용된 동일 Student/Public Git SHA에 대해서만 CI PIN/syntax/self-check 후 GitHub one-shot WSL2 실행기 준비, 로컬 강사 WSLg GUI/TTY 실제 1회 인수. 수행하지 않았으면 `L3_NOT_RUN`. private instructor 코드/학생 TODO 분리, main 승인 전 병합 금지.
