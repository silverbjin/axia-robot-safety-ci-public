# AXIA D08 Task02 — 실제 AMCL 초기위치 실패·P0 최소 결선·CI 분리 보고

## 기준
Public CI silverbjin/axia-robot-safety-ci-public, feat/d08-unified-sensor-cm-path-20261118, main base 62e366b51c64da25ad0216328fe1e019b78e0bef, PR #166. Main 미병합.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- PLAN revision 52406e259c99e17abf2af529de3ab6940ed5ba60.
- Actual RED HEAD 94b5cc892041116192f50c63b279c3ddf234062c, Run #44208629430, job #134481075887: 기존 Gazebo actual person/RGBD/scan 및 isolated official CM L2 통과. 이어 실제 공식 Nav2 '/compute_path_to_pose' STATUS_ABORTED(6), exit2.
- 원본 d08-official-nav2-sameworld/d08_official_nav2_one_world.log: "[amcl] AMCL cannot publish a pose or update the transform. Please set the initial pose"; map frame absent; GridBased "Unable to get start pose". First safety/initialization boundary AMCL SetInitialPose and real map→base_link TF. Shutdown SIGABRT -6 is downstream after that failure; do not treat as first cause.
- Candidate GREEN: d08/harness/d08_amcl_initial_pose.py reuses public D07-H01 P0 official API (real /map OccupancyGrid free-cell /clock /scan /odom, one nav2_msgs/srv/SetInitialPose, then actual /amcl_pose and TF2 map→base_link). d08_nav2_path_preflight only calls this when opt-in same-world official Nav2. No invented TF/odom and no command/Goal.
- CI design: independent gazebo-official-nav2-oneworld job (new actual single world) separate from existing gazebo-contact-positive-once and upstream YOLO replay. Thus Nav2 failure does not SKIP independent diagnostic YOLO job; do not stitch results into one actual D08 E2E.
- RED L0 2 tests inspect real-map free/unknown and CI job separation. GREEN exact-SHA public L0/actual Nav2 Gazebo L2 PENDING; do not assert success.
- REVIEW: no modification to ROS/Nav2/CM official sources, no Safety/Guard TTL change, no /cmd_vel or Moving Goal publisher, student TODO and sealed instructor unchanged.
- Source/workflow/report commit SHA to be recorded in PR after write.

## 판정
Task02 official first path: HOLD pending new exact SHA. Task01 2 real person VALID + UNKNOWN HOLD. Same-world real CM native /scan and before/near/restore Path HOLD. G07 MOVING HOLD. Owner WSLg L3 NOT_RUN.
