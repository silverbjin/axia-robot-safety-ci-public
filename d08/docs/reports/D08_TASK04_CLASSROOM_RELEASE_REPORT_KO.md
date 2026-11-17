# AXIA D08 Task04 — 수업용 통합 배포 준비 보고서 (HOLD)

## 작업 기준
- Public CI repo/branch: silverbjin/axia-robot-safety-ci-public / feat/d08-unified-sensor-cm-path-20261118
- Base main SHA: 62e366b51c64da25ad0216328fe1e019b78e0bef
- PR: https://github.com/silverbjin/axia-robot-safety-ci-public/pull/166
- Student branch: feat/d08-integrated-no-goal-live-20261118; PR https://github.com/silverbjin/axia-robot-safety-student/pull/43 ; guide commit e8f1de9911a90c0f77e085ff8bd13594d55987a4
- Private Instructor branch: docs/d08-unified-teacher-guide-20261118; PR https://github.com/silverbjin/axia-robot-safety-instructor/pull/212 ; guide commit 839da3c3daa3d62bec4e1a9a7b47acf5a026a399
- No teacher private code was copied to student/public CI; Student D06/D07/D08 TODO retained.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- PLAN: use same public one-world exact-SHA runner and three-layer rqt_graph guides; preserve no-moving-Goal and private answer separation. Actual public integrated one-shot still missing, so **release is HOLD**.
- First task-specific RED: public CI Run #44201775704, SHA dfd4ba290807a933ac911dbc8e832f670386b77c, Gazebo native first job PASS; later pinned upstream yolo_ros build FAIL from CMake extraction of downloaded onnxruntime.tgz: "Unrecognized archive format".  Exit 2. The actual HTTP response was not retained by upstream curl -L; cannot claim confirmed HTTP 403/404.
- New minimal GREEN hypothesis/attempt: prior to upstream colcon, curl -fL from official Microsoft ONNX Runtime 1.20.0 release and validate gzip member for libonnxruntime.so, calculate downloaded SHA256, provide local file URL through officially supported upstream CMake -DONNXRUNTIME_URL. No fork, no version/engine changes. A failed download is classified INFRA_BLOCKED. Actual new L2 outcome PENDING.
- L0 regression: d08/tests/test_d08_yolo_archive_gate.py, existing d08-main-no-goal-real-gazebo-l2.yml workflow. The runtime must still pass its original real upstream YOLO engine build and DetectionArray replay; no substitution.
- Existing guides: Student block_B/day08/D08_UNIFIED_NO_GOAL_CLASSROOM_GUIDE_20261118_KO.md, private Instructor training/block_B/instructor/D08_UNIFIED_NO_GOAL_INSTRUCTOR_GUIDE_20261118_KO.md. Both marked draft HOLD. Observations: stage1 RGBD/YOLO/camera-registration, stage2 Nav2 Costmap/Path/CM, stage3 scan/TF/odom/Guard/Contact. rqt_graph filters + ros2 topic info -v and topic hz.
- REVIEW: missing actual D08 native one-world Nav2 Costmap/ComputePathToPose + real-scan Collision Monitor, public ROI 2 REAL VALID + 1 UNKNOWN, exact-SHA published WSL2 launcher. Therefore no classroom release or Owner action. No sensor/CM TTL relaxation and no /cmd_vel.
- Commit SHA to be added in PR #166 after commit.

## 증거 기반 판정
- L0: last observed SHA dfd4ba290807: 28 passed in 0.16s. New exact SHA L0 pending.
- Actual Gazebo L2 at dfd4ba290807: native Waffle + physical person + RGBD/scan first CI job success, but full workflow FAIL in upstream ONNX Runtime extract. Earlier SHA 25d3ed03 had actual scan 519.095ms > 500ms, so whole-run timing stability not proven.
- Real ROS L1: isolated native CM diagnostic, synthetic /axia_ci/scan, NOT native one-world CM /scan; official Planner independent previous CI only.
- Owner WSL2 WSLg L3: NOT_RUN; 3D visual pixels: NOT_VERIFIED.
- D08_LIVE_NO_GOAL_ACCEPTED=NO; D08_MOVING_E2E_ACCEPTED=HOLD.

## 다음 단계
- Await exact-HEAD public L0/L2 and upstream ONNX archive diagnostic. If infra remains blocked, retain evidence; no blind retries.
- Then finish Task01 physical 2 VALID+UNKNOWN and Task02 same-world official CM/Planner, publish exact-source public --self-check/--doctor/--run one-shot, and run Owner WSLg once.
- Once all Task00/01/02+04 pass, request explicit main merge approval for 3 PRs in one message. No main merge performed.
