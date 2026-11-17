# AXIA G07 CM120 — 두 단계 원인 우선 리뷰·실행 증거 (기능 Cycle08 아님)

## Step 1: 최초 아키텍처 리뷰로 회귀, CI·Owner 원본 구분
- C05 exact private baseline `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public tracer snapshot `202b66eb49001e59a06adecb70dde67a457f0780`, real [Public Run #43995793080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995793080).
- **같은 첫 CM source gap:** RMW SYSTEM source 차이 120.172578ms; CM Observer callback gap120.523837ms; exact official C++ `/cmd_vel_supervised` subscription→handle verified, callback wall elapsed81.972669ms and overlap first gap81.972669ms, metadata callback count2, upstream Supervisor 2 publishes, original release margin120ms FAIL.
- C05 trace scope LTTng only `ros2:rcl_subscription_init` → `ros2:rclcpp_subscription_init` → `ros2:rclcpp_subscription_callback_added` and CM-procname filtered `ros2:callback_start/end`. Missing **per-function** `nav2_collision_monitor::Source::getTransform` entry/exit, `nav2_util::getTransform` or tf2 lookup time, kernel schedule/wait exact first vtid. C05 report itself `tf_lookup_causality_proven=false`, `scheduler_causality_proven=false`.
- Official Jazzy source paths: `nav2_collision_monitor/src/collision_monitor_node.cpp::cmdVelInCallbackStamped → process() → Source::getData()`; `nav2_collision_monitor/src/scan.cpp::getData() → Source::getTransform()`; `nav2_collision_monitor/src/source.cpp::getTransform()` selects advanced time-interpolated transform with `base_shift_correction=true`. Control path known **statically** ≠ that function's runtime duration.
- Official Nav2 docs note advanced base-shift costs compute/TF time but also spatial safety precision. C07 NO_GOAL #43999183495 source_timeout1.0, base_shift true, tolerance.02 provenance only; entire L2 shutdown failed lifecycle service timeout. C06/parallel C07 `base_shift=false` / `source_timeout=.3` was **not actually tested on Moving Goal**; cannot claim fix.

## Minimal new evidence: NOT a product change
- Read-only pinned `ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df...` inspection workflow `.github/workflows/axia-g07-cm120-tf-direct-capability-l0.yml` (public dev source from immutable C05 commit) checks installed official CM ELF symbol visibility and Linux perf/tracefs uprobe capability **without ROS, simulator, Goal, or new publisher**.
- Need **both** exact TF function entry/exit and the same caller CM callback vpid/vtid, plus host clock anchor and first RMW source gap to prove cause. An exported symbol alone is not sufficient. Kernel uprobe device unavailable ≠ no technical tracing possible anywhere; classify as **current CI noninvasive capability constraint**.
- Do not enable privileged CI, fork official Nav2, change `base_shift_correction`, source_timeout, CPU affinity, 120/150/300ms TTL or stop polygons simply to obtain traces. If direct function boundary cannot be obtained with existing tools, Step 1 verdict `CAUSE_UNPROVEN`, Step 2 **NOT_STARTED**, no additional Moving Goal.

## RED→GREEN→REFACTOR→REVIEW→COMMIT fit for non-functional review
No production code changed in this review: RED/ GREEN implementation contract **not applicable yet**. Existing C05 tests and actual Run preserved. Read-only capability smoke test is infrastructure evidence, **not** a new product regression, release-green, or motion capability. If a single-root-cause product fix becomes justified, it must then follow RED→GREEN→REFACTOR→REVIEW→COMMIT exactly and integrate a single original tracer-OFF Moving Goal.

## Immutable output and safety
Plan: `d06/docs/AXIA_G07_CM120_TWO_STAGE_CAUSE_FIRST_PLAN_20261117_KO.md`, report this file, one preflight workflow, single public branch `review/g07-cm120-2stage-cause-gate-20261117`. No private source or any WSL2 script changed.
Moving public CI/Owner L3: **NOT_RUN_THIS_REVIEW**. `CM_120MS_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`. No `main` merge.

## 실제 CI 결과
(아래에 exact Run과 출력 이후 추가: 처음 보고서 작성 시 PENDING)
