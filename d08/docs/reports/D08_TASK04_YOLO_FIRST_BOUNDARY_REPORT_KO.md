# AXIA D08 Task04 — YOLO real ROS DetectionArray first-boundary diagnostic

Public PR #166, base main 62e366b51c64da25ad0216328fe1e019b78e0bef. Pinned upstream yolo_ros and official Microsoft NuGet 1.20.0 code unchanged.

Actual failure: public Run #44206496600 at source 741b0d98461e453d9450a8a01570e03a16cc59c2. Source integrity passed; upstream C++ build printed UI9_PINNED_UPSTREAM_YOLO_BUILD_PASS. Actual ROS DetectionArray replay failed: UI9_REAL_YOLO_ROS_PERSON_DETECTION_L1_BLOCKED {"person_count":0,"detection_array_count":0}; exit2. **No native YOLO runtime log was uploaded**, so precise cause (process load, missing shared library, YAML params, DDS input) NOT DETERMINED.

New minimal RED diagnostic L0: d08/tests/test_d08_yolo_first_boundary.py. GREEN change does NOT fake detection: on first absent launch process / bounded replay failure, emit 140-line native yolo_ros log, ROS graph nodes/topics and executable ldd, upload log as artifact. Keep no Goal, no cmd_vel, no safety timeout alteration.

Exact-HEAD new CI pending. Do not label native YOLO success, Task01 or Task02 accepted until actual same-world evidence. Student and Instructor docs draft only; main merge not approved.
