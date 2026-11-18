# AXIA D08 Task02 — 실제 CM Lifecycle/Scan Source read-only 원본 확인 중간보고서

## 작업 기준
- Public repo silverbjin/axia-robot-safety-ci-public; branch feat/d08-unified-sensor-cm-path-20261118; base main 62e366b51c64da25ad0216328fe1e019b78e0bef, PR #166.
- Last exact-source actual public [Run #44245796892](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44245796892), HEAD=checkout `910d3a22291f0ab8a4585f8dab5501219408171b`: L0 97 PASS, real Gazebo/ROS YOLO/Depth two VALID+one UNKNOWN, official Nav2/Costmap three physical Path L2 SUCCESS. Original artifact #14401772249.
- SAME run raw `official_path_phases/verdict.json`: `official_cm_scan_subscription_discovered=false`, `real_scan_consumers` contains 2 `_NODE_NAME_UNKNOWN_`. Native `d08_official_nav2_one_world.log`: genuine official CM PID, `[scan]: Creating Scan`, `Activating` and clean lifecycle shutdown. Unknown graph is NOT a verified sensor input age or action output.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- PLAN v1.13 committed in `ec871a54451f0ce4d7b5109cbf0f3099b66ba1a1`.
- Actual L0 RED `613e40bb95f0eb8691d9c68105bb2ecdb57e91d4`, [Run #44247821804](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44247821804): `ImportError: cannot import name 'assess_official_cm_native_scan'`, actual Gazebo jobs skipped. Original real L2 gap still preserved separately.
- GREEN minimum: `d08/harness/d08_same_world_replan.py` pure fail-closed scoped validator + **real native** `lifecycle_msgs/srv/GetState` `/collision_monitor/get_state` and `rcl_interfaces/srv/GetParameters` `/collision_monitor/get_parameters` in SAME actual ROS node/Domain. Require lifecycle ACTIVE state id3, `observation_sources` contains `scan`, `scan.topic` equals `/scan` or `scan`. Read only; no `SetParameters`, no alternative model/ROS CM fork, no Twist or Controller/Planner change.
- New exact HEAD CI L0 and true Gazebo L2: NOT_RUN until Actions job ends, no PASS assertion yet. Native evidence fields `official_cm_active_scan_configured`, `cm_native_state_service`, `cm_native_param_service`, `scan_graph_anonymous_subscriber_count`, original topic graph remain separate and auditable.
- Commands: `python -m pytest -q d08/tests/test_d08_official_cm_native_readonly.py`, public workflow `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml` exact HEAD; `python3 -u d08/scripts/d08_public_gazebo_l2.py --actor /tmp/axia-d08-live-assets/walk.dae --out results/d08-live-person-nav2-e2e --official-nav2 --official-path-phases --live-person-range` while pinned C++ YOLO remains in same job.
- REVIEW: native CM lifecycle+configuration **is not internal receive gap**. `native_cm_scan_receive_gap_verified=false`, `safety_cm_state_verified=false`; no synthesized safety command to produce CM Twist, no Guard TTL modifications. Perception/Planner original fixed frame/stamp/0.5s host Scan age gate unchanged. No private teacher answer/hidden tests leaked.
- Existing success sensor/Path L2 on exact old SHA preserved. WSLg 3D GUI Owner L3 NOT_RUN, Moving G07 strict HOLD, Public/Student/Instructor main all unmerged. Correct same-source new CI outcome and final SHA will be recorded in PR #166 comment.

## 후속
- If lifecycle ACTIVE or `scan.topic` does not match, FAIL and inspect actual response/first boundary only. Do not infer CM unknown publisher names are CM; no repeated field retry.
- If exact-source L2 PASS, Owner will run ONE pinned public GUI/no Goal script to visually confirm Gazebo/RViz. Source/GUI/physical evidence cannot be inherited from Xvfb.

## GREEN actual native L2 판정 추가 — 2026-11-18

- Source HEAD/actual checkout `a83629edd71ce51567e184451f2a76bafcf1318b`; [Run #44248098353](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44248098353), 전체 SUCCESS; L0 `103 passed in 0.33s`, 원본 artifact `d08-same-world-live-person-range-cm-nav2-evidence` #14402713171.
- 원본 stdout:
```text
D08_OFFICIAL_CM_NATIVE_ACTIVE_SCAN_SOURCE_NO_GOAL {"cm_actual_configured_scan_topic": "scan", "cm_native_lifecycle_state": "active", "cm_native_observation_sources": ["scan"], "native_cm_scan_receive_gap_verified": false, "official_cm_active_scan_configured": true, "safety_cm_state_verified": false}
D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL
D08_LIVE_D05_TWO_VALID_ONE_UNKNOWN_L2_PASS {"distance_far": 0.704022, "distance_stop": 0.534589, "delta": 0.16943, "unknown": "NO_PERSON_CLASS_IN_ACTUAL_YOLO"}
D08_REAL_LIVE_RGBD_YOLO_D05_NAV2_THREE_PATHS_L2_PASS_NO_GOAL
```
- `official_path_phases/verdict.json`: `official_cm_active_scan_configured=true`, `cm_native_lifecycle_state=active`, `cm_actual_configured_scan_topic=scan`; 해당 CM 설정은 native ROS 상태·파라미터 서비스 응답으로 검증. `official_cm_scan_subscription_discovered=false`인 ROS 그래프 이름 탐색만으로 CM 수신을 단정하지 않았습니다.
- D08 observer `scan_sample_count=60`, 최대 Scan receive gap `0.228737s`, 첫 500ms 위반 없음. **official CM 내부 RMW-source 갭, Guard TTL, 실제 STOP/SLOW 출력은 NOT_VERIFIED**. 새 Goal/Twist/CM TTL 우회 없음.
- L0/ROS L1/실제 Gazebo L2의 YES는 위 실제 확인 범위에만 적용. Owner WSLg 픽셀·실제 moving E2E NOT_RUN/HOLD.
