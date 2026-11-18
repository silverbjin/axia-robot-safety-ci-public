# AXIA D08 Task02 — 동일 Gazebo 공식 Nav2 3상 경로 L2 인수 중간보고

## 기준
- Public CI repository: silverbjin/axia-robot-safety-ci-public
- Development branch: feat/d08-unified-sensor-cm-path-20261118 / PR #166
- Base main SHA: 62e366b51c64da25ad0216328fe1e019b78e0bef
- Tested feature HEAD: d37d1a36507cfe5c99cd41f4384cc9c7cac3c5ca
- Actual Actions checkout merge SHA: 37116c0780693bb878fbb6ada18763959eeb0c3b (separate from feature HEAD)
- Actual L2 public Run: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44227457087
- Raw artifact d08-official-nav2-oneworld-l2-evidence, ID 14392504703 (7-day CI retention).
- Same World: default, SDF SHA256 e83682c1a79b15a190d93b8357eda469109ece69e947cf223c6a1fad550f9c86
- Robot axia_d08_ci_waffle, physical person axia_p2_g07_obstacle, ROS_DOMAIN_ID 69, GZ_PARTITION axia_d08_ci_9968.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- PLAN commit 18c4eb448b503ba96f98d3851412ac9d29e1284e: D07-H01 real Gazebo goal (-1.7,0.7) and physical person coordinates treated ONLY as candidates, not D08 acceptance evidence.
- Initial RED #44226134951 at 1c3dc3e0ce90455effe1126b29084e96df538bcf: missing read-only same-world phases module; L0 import failure.
- Candidate #44226367924 at 339f92df043f0b5e22212812428555ec8ee682ba: L0 57 passed in 0.28s, real Nav2 first Path blocked BEFORE phases by D08_AMCL_REAL_MAP_BASE_TF_NOT_READY:AMCL_POSE_STALE. Original artifact 14393167386.
- Cause hypothesis: TF2 listener constructed after official AMCL SetInitialPose ACK, potentially misses first dynamic transform from stationary Waffle. PLAN revision 4ffbda05c932a2e15af2ea426ebd6b296e44317a, official Nav2 Jazzy AMCL docs https://ros-navigation.github.io/mkdocs.nav2.org/jazzy/configuration_and_development/configuration_guide/others/configuring_amcl/.
- Actual TDD RED #44227259173 source ef2a152324a54ccb71e472a297ead471d56e0b8f: 1 failed, 58 passed in 0.34s; failed test_tf_listener_is_ready_before_initial_pose_service_can_broadcast.
- GREEN source d37d1a36507cfe5c99cd41f4384cc9c7cac3c5ca: pre-subscribe real TF2 listener BEFORE SetInitialPose service; preserve ALL original AMCL 1.0s, scan/odom 0.5s ages, CM/Guard safety TTL. New L0 #44227457087: 59 passed in 0.35s; real Gazebo official Nav2 three-phase job SUCCESS.
- Paths: d08/harness/d08_amcl_initial_pose.py, d08/harness/d08_same_world_replan.py, d08/scripts/d08_public_gazebo_l2.py, d08/tests/test_d08_amcl_tf_subscription_order.py, d08/tests/test_d08_same_world_replan.py, .github/workflows/d08-main-no-goal-real-gazebo-l2.yml.
- Commands: python -m pytest -q d08/tests/test_d08_amcl_tf_subscription_order.py d08/tests/test_d08_same_world_replan.py ; python3 -u d08/scripts/d08_public_gazebo_l2.py --actor /tmp/axia-d08-nav2-assets/walk.dae --out results/d08-official-nav2-sameworld --official-nav2 --official-path-phases.
- REVIEW: official Nav2/CollisionMonitor/Planner untouched; no new command velocity publishers; no moving robot Goal; no private Instructor answer or hidden tests; no safety TTL changes.

## Actual one-World three-phase evidence
| Stage | Proxy world XYZ (m) | Real /scan sector (m) | Native Costmap lethal | /scan stamp (s) | Costmap stamp (s) | Official Path stamp (s) | Path-to-proxy minimum (m) |
|---|---|---:|---:|---:|---:|---:|---:|
| before | -0.58,-0.50,0.24 | 1.875290 | 0 | 8.700 | 8.685 | 8.760 | 0.003065 |
| intrusion | -1.979119,0.171291,0.24 | 0.552188 | 73 | 10.602 | 10.587 | 10.677 | 0.327008 |
| restored | -0.58,-0.50,0.24 | 1.876234 | 0 | 12.501 | 12.486 | 12.573 | 0.017926 |

- Actual official ComputePathToPose detour delta 0.32394 m (required >= 0.15), restored delta 0.01486 m (required <= 0.12).
- 70 real LaserScan received samples, maximum monotonic receive gap 0.220362 s (below fixed 0.5s), first above-0.5s gap NONE. This measures D08 observer receive gap, NOT official CM internal receive gap.
- Real /scan publisher node ros_gz_bridge, subscriber nodes amcl, local_costmap, global_costmap, collision_monitor, axia_d08_official_physical_replan_no_goal.
- AMCL real /map free 16 cells, real TF2 map-to-base_link, stationary odom, no robot Navigation Goal or Twist issued by this adapter. CM state output/Guard age NOT VERIFIED.
- Files: official_path_phases/path_phases.jsonl and official_path_phases/verdict.json, native set_pose ACK logs, real RGBD captured, runtime_provenance.json, SHA256SUMS.

## Acceptance and limitations
- Task02 same-world actual physical LiDAR -> official Costmap -> official Path three phases: Gazebo L2 PASS at exact source above.
- Task01 live registered RGB/Depth/YOLO 2 VALID distances plus UNKNOWN: HOLD; prior pinned upstream C++ YOLO image-replay ROS L1 is separate and cannot substitute.
- Task02 actual CM internal callback/state -> Guard safety TTL: NOT VERIFIED. No actual slowdown/robot path driving; only graph subscription discovery.
- Task03 G07 moving strict: HOLD independently. Owner WSLg 3D GUI: NOT_RUN; not a certified E-Stop.
- D08_LIVE_NO_GOAL_ACCEPTED=NO until same run live sensor+distance+CM/path and classroom docs/runner verified.
- Main branches Public/Student/Instructor not merged, user approval required later.

## Next
- Reuse official ONNX Runtime 1.20.0 and pinned C++ yolo_ros already built successfully in public CI without duplicating the engine. Integrate real ROS RGBD + DetectionArray + public D05 read-only ROI median into SAME Gazebo/Nav2 no-Goal run. Prove 2 distinct VALID distances and one actual UNKNOWN, and distinguish CM state/subscription/TTL evidence. Keep Owner WSL2 one final run only.
