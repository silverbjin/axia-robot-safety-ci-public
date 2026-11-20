# AXIA D08 Task01 — SAME World live D05 two VALID + UNKNOWN / minimum C++ YOLO integration

## Work basis
- Public CI repo silverbjin/axia-robot-safety-ci-public / branch feat/d08-unified-sensor-cm-path-20261118 / PR #166 / base main 62e366b51c64da25ad0216328fe1e019b78e0bef.
- Plan v1.7 committed 734c7c03aca408997984479f833e3bb0eee39138 after successful 3-phase Nav2 L2 #44227457087 (d37d1a36507cfe5c99cd41f4384cc9c7cac3c5ca). This valid three-Path result is for a prior source, not automatic new same-world live YOLO proof.
- Prior pinned C++ original yolo_ros SHA 94d2dd500cb26027ee9c019f4d3a02029ac615cc and official Microsoft ONNX Runtime 1.20.0 package SHA 36dbafacb1bc532e92d02371bd70582a61105872561fc9982314854d1c7ebf72, public RGB replay L1 PASS.
- RED actual public #44228712049 at f2b235de5f20e51c43befdebcb40813b93107c30: missing public live read-only adapter, ModuleNotFoundError:d08_live_person_range, all actual ROS/Gazebo L2 jobs SKIPPED.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- Minimal GREEN candidate: d08/harness/d08_live_person_range.py (existing d08_public_person_range.assess_public_person_range and existing bbox_from_real_detection only), d08/harness/d08_live_person_range_session.py for three native human Proxy set_pose stages and return to far position, without publisher/Goal.
- Existing yolo job REUSES same built official C++ engine and same pinned model. Following separate image replay proof, opt-in -live-person-range executes original same-world official Nav2 runner with actual ROS RGB+Depth, actual /yolo/cam0/detections, same source SHA/Domain/GZ, official 3 Path phases and actual /scan costmap. No screenshot stitching.
- Public strict gate: same optical frame + one generated SDF RGBD registration, 50ms RGB/Depth/Detection stamp skew, 0.5s host monotonic input age, 32FC1 and 4x4 person ROI >=8 valid pixels, two actual distinct distance_m >=0.12m, actual reasoned UNKNOWN with registered RGBD and real no-person DetectionArrays; no UNKNOWN=CLEAR and no cmd_vel.
- Fail closed on native Gazebo pose ACK, actual slow (.4,.75m)/stop (.14,.4m) front scan, new native YOLO detection absence or stale timestamps, no fixed fake depth. always restore human far in finally.
- L0 tests: d08/tests/test_d08_live_person_range.py, d08/tests/test_d08_live_person_range_session.py, d08/tests/test_d08_live_same_world_wiring.py, existing D08 tests.
- L2 exact new source CI output/actual stamps, person count, valid distances, first CM/scan gap PENDING; never infer success from source.
- REVIEW: upstream Planner/Controller/YOLO not modified, instructor sealed answers never exposed, no moving Goal, no synthetic scan, no safety TTL changed; official CM actual subscription ≠ verified CM output/safety, WSLg pixels NOT_RUN.
- Existing Task02 sensor/CM/path three phases was independently SUCCESS at previous SHA, but when live C++ YOLO adds CPU load the real /scan timing has to be measured again; if violation, overall same-world stability HOLD until original first gap resolved.

## Verification and next
- L0: python -m pytest -q d08/tests/test_d08_live_person_range.py d08/tests/test_d08_live_person_range_session.py d08/tests/test_d08_live_same_world_wiring.py.
- L2 public action .github/workflows/d08-main-no-goal-real-gazebo-l2.yml, existing real-gazebo-rgb-pinned-upstream-yolo-ros job: python3 -u d08/scripts/d08_public_gazebo_l2.py --actor /tmp/axia-d08-live-assets/walk.dae --out results/d08-live-person-nav2-e2e --official-nav2 --official-path-phases --live-person-range.
- New exact HEAD L0/ROS/Gazebo L2: NOT_RUN until CI. Owner WSL2 L3 NOT_RUN. G07 strict moving HOLD, all main branch merges NO.
