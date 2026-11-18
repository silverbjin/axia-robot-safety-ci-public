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
