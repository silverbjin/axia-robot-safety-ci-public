# AXIA D08 Task02 — 공식 Nav2 한 World / AMCL 첫 Path L2 성공 중간보고서

## 작업 기준
- Public CI repo: silverbjin/axia-robot-safety-ci-public; development branch feat/d08-unified-sensor-cm-path-20261118; base main SHA 62e366b51c64da25ad0216328fe1e019b78e0bef; PR #166.
- 실제 공개 Run #44210297492 (job #134486722728), PR source HEAD ffff73105abb05290d618d6f912ac4fb7af8a404, **실제 Actions checkout/runtime SHA** 098dba8081371adfa80d349454849c343d19b308 (PR merge checkout). 실행 source와 PR commit을 구분해 기록.
- Scope: NO_GOAL, official Jazzy one-world Waffle RGBD + physical human proxy + AMCL/TF + first ComputePathToPose only. Excluded: Task01 real 2 VALID+UNKNOWN, Task02 3 Path phases/native CM /scan cadence, Owner WSLg, Moving E2E.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- PLAN v1.2 commit 52406e259c99e17abf2af529de3ab6940ed5ba60.
- Actual RED: Run #44208629430 (HEAD 94b5cc892041116192f50c63b279c3ddf234062c), official Action STATUS_ABORTED(6). Native log AMCL not initialized and no map→base TF; upstream GridBased could not get a start pose. Exit2. Post-shutdown planner SIGABRT is not first failure.
- GREEN minimal source: d08/harness/d08_amcl_initial_pose.py; d08/harness/d08_nav2_path_preflight.py; opt-in d08_public_gazebo_l2.py with official Nav2. Original Waffle /scan + RGBD and manually managed independent test untouched. Tests: test_d08_amcl_initial_pose.py, test_d08_job_independence.py and existing heredoc regression. At HEAD ffff731 L0 actual output: "44 passed in 0.25s", "D08_PUBLIC_MAIN_NO_GOAL_L0_PASS". Independent native official L2 job SUCCESS.
- Actual L2 log:
  D08_OFFICIAL_AMCL_REAL_TF_READY_NO_GOAL {"amcl_service_ack":true,"localization_verified":true,"free_checked_cells":16,"map_frame":"map","scan_frame":"base_scan","odom_frame":"odom","scan_stamp_ns":4800000000,"odom_stamp_ns":4824000000,"amcl_pose_stamp_ns":4902000000,"map_base_link_tf_stamp_ns":5904000000}
  D08_LIVE_NAV2_PATH_CANDIDATE {"path_points":14,"path_length_m":0.4,"start_xy":[-1.99999988,-0.49999986],"end_xy":[-1.6,-0.5]}
  D08_REAL_GAZEBO_WAFFLE_RGBD_NO_GOAL_PASS
  D08_OFFICIAL_NAV2_SAME_WORLD_FIRST_PATH_L2_PASS_NO_GOAL
- Source run: World default; robot spawn axia_d08_ci_waffle (-2.0,-0.5), physical+visual same proxy axia_p2_g07_obstacle; ROS_DOMAIN_ID=69, GZ_PARTITION=axia_d08_ci_9968, same generated SDF / optical frame. Real /map OccupancyGrid 384x384, resolution .05m; 16 free spawn cells. No moving Goal, no Twist publisher in our read-only runner.
- Public raw evidence: artifact d08-official-nav2-oneworld-l2-evidence (#14385084779) includes verdict.json, official_nav2_before_path.json, native launch logs, generated actual World/robot SDF, runtime_provenance.json and SHA256SUMS, retained 7d by workflow.
- REVIEW: official Navigation2 Planner/Controller/CollisionMonitor unmodified; only official AMCL SetInitialPose service used; not a certified E-Stop. Real CM source→observer first-gap and map Costmap before/after physical change NOT_VERIFIED. WSLg pixels NOT_RUN.
- This report included in subsequent commit; exact report SHA recorded in PR comment after commit.

## 판정 및 다음
- Task02 official same-world first Path subset: **actual Gazebo L2 PASS** on above SHA only. Task02 full NO_GOAL sensor+CM+three Paths: HOLD. Task01 two actual VALID+UNKNOWN: HOLD. Task03 G07 MOVING: HOLD. Task04 release: HOLD.
- Next: reuse D07-H01 public physical route reference goal(-1.7,0.7), stage far(-0.58,-0.5)→real obstacle(-1.979118934,0.171291396)→restore far in SAME D08 run. Capture /scan stamps, native global Costmap epoch/Path original; fail closed on no path change. Camera can lose visible person at side obstacle; do not call that clear. Add actual native CM /scan graph/QoS evidence and YOLO read-only measured distance separately.
- Main branches unmerged; Owner WSL2 only after exact-SHA full L2 and classroom one-shot pass.
