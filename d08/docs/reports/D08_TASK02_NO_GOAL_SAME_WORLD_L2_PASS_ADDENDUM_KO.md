# AXIA D08 Task02 — 실제 한 World 센서/공식 Nav2 3 Path/CM 구독 증거

## 작업 기준
- Public CI Repo silverbjin/axia-robot-safety-ci-public, branch feat/d08-unified-sensor-cm-path-20261118, base main 62e366b51c64da25ad0216328fe1e019b78e0bef, PR #166.
- Actual #44236129868 (feature source `16c1bdadf2312f31e639125b75a3b7b0ab634e18`, checkout source `b632d787bbaf062f6327d5e2dc53f1ae354586d4`), real Gazebo Harmonic L2 all SUCCESS.
- Original same-run raw artifact #14397906766; world default/robot axia_d08_ci_waffle/person axia_p2_g07_obstacle; ROS_DOMAIN_ID=69/GZ_PARTITION=axia_d08_ci_12493; World SDF SHA256 d70a7773cf13c5ea5678279e36ef719603010fefe9cce90761ddd06b8131a461.
- No direct motion Goal or Twist published. Distinct from earlier #44227457087 prior-source Path-only L2 success.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- Reuse official Jazzy Nav2 Planner/Costmap/AMCL/Collision Monitor and Waffle Gazebo, public D07-H01 verified person candidate coordinates but remeasure all actual ROS values. Original Task02 Path deficiency RED #44226134951 `ModuleNotFoundError` and AMCL/TF first failure #44231766775 `AMCL_POSE_STALE`. Captured native logs and targeted public L0 red/green, no repeat field retry.
- Task02 GREEN part `d08/harness/d08_same_world_replan.py` + `d08/harness/d08_amcl_initial_pose.py` reused source-only official `ComputePathToPose` three actions for the existing one physical Proxy. AMCL first Pose/TF gate aligned with actual Jazzy stationary AMCL source; live scan/odom 0.5s age preserved. No new Planner/fake scan/TF/cmd_vel.
- Actual run prints:
  `D08_AMCL_FIRST_REAL_POST_REQUEST_POSE` stamp 5.901s, source age .024s;
  `D08_AMCL_REAL_FIRST_POSE_PLUS_LIVE_TF_READY` TF stamp 6.912s, current scan receive age 0.006242s, odom 0.001209s;
  `D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL`.
- Official original Path/Scan/Costmap stage:
  - before /scan 1.867162m, lethal 0, Path-to-proxy .033206m; native source scan stamp 10.101s, costmap 10.122s, Path 10.206s.
  - intrusion /scan .546053m, lethal **66**, Path-to-proxy **.325576m**; source stamps 12.000/12.024/12.081s.
  - restored /scan 1.884932m, lethal **0**, Path-to-proxy **.003006m**; source stamps 13.902/13.923/13.983s.
  - Actual 67 scan callback samples, host receive max gap **.371009s**; first >0.5s gap NONE. This is D08 observer first gap, NOT official CM RMW-source or CM→Guard age.
- Actual CM `/scan` subscription discovered in ROS Graph with /global_costmap, /local_costmap and AMCL. Official CM default `state_topic` empty and action processing linked to input Twist (`nav2_collision_monitor/src/collision_monitor_node.cpp` Jazzy blob 41495890e0c268de98619bb17875a1efb25cc28b): **NO_GOAL real CM state/slowdown NOT_RUN**, CM internal receive-gap/Guard age NOT_VERIFIED; no synthetic velocity fed to final command.
- Actual registered RGBD and live C++ YOLO+D05 two VALID/one UNKNOWN also succeeded inside that exact Gazebo World (Task01 report). Same scene but no proved YOLO->CM input and no claimed actual robot motion/Contact-free driving.
- Reused L0/ROS L1 evidence not promoted across SHA; raw ROS/GZ logs, source SHA, original Path JSONL and SHA256SUMS preserved.
- REVIEW: no Nav2 source fork, Planner/Controller replacement, /cmd_vel pub duplication, CM/Guard TTL increase, certified E-Stop claim or private answer leak.

## 판정·다음
- D08 Task02 same World physical /scan + official Costmap + 3 Path and registered RGBD+live YOLO/D05 observation: **actual Gazebo L2 PASS** (NO_GOAL educational scope).
- CM internal actual SLOW/STOP and actual velocity ratio/odom dwell/Guard safety evidence: NOT_RUN / NOT_VERIFIED and explicitly outside NO_GOAL.
- Owner WSL2/WSLg actual GUI pixels NOT_RUN; Moving G07 strict HOLD. Task04 public pinned GUI runner code/CI, Student/Instructor guides and Owner L3 pending before `D08_LIVE_NO_GOAL_ACCEPTED=YES`. main branches NO merge without approval.
