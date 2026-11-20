# AXIA D08 Task04 — 실제 C++ YOLO ELF SONAME 1st failure / 최소 공급 수정

## 작업 기준
Public CI repo silverbjin/axia-robot-safety-ci-public / branch feat/d08-unified-sensor-cm-path-20261118 / main base 62e366b51c64da25ad0216328fe1e019b78e0bef / PR #166.
Actual RED source HEAD ffff73105abb05290d618d6f912ac4fb7af8a404, Run https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44210297492, native YOLO job #134488654325.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- Prior official Microsoft NuGet package ID/version/hash/ELF x86_64, private-free C++ pinned yolo_ros BUILD all PASS, model SHA256 PASS.
- **Earliest real runtime failure**: 2026-11-18 00:51 UTC: yolo_node launched PID 5479, dynamic loader emitted exactly "libonnxruntime.so.1: cannot open shared object file: No such file or directory", child exit127. Consequently DetectionArray=0; it is NOT a YOLO inference accuracy error, missing model, Gazebo camera or DDS regression.
- Plan v1.4 committed before code in d5e65dbf9efc95de1b69e0fde05effad6a117304.
- Minimal GREEN candidate: existing d08_prepare_official_ort_nuget.py, after actual package hash/ELF verification, makes one relative symlink libonnxruntime.so.1 -> libonnxruntime.so (same unmodified Microsoft ELF). Existing upstream yolo_onnxruntime_vendor's -DONNXRUNTIME_ROOT installs both names. Public workflow requires actual readelf SONAME to be exactly libonnxruntime.so.1; ROS environment ldd must resolve native yolo_node SONAME before launch. No new binaries/versions/forks, no extra runtime fallbacks.
- L0 RED regression: existing d08/tests/test_d08_official_ort_nuget.py asserts same-file symlink and documented loader alias. Actual native C++/ROS DetectionArray replay GREEN requires next exact SHA CI SUCCESS. NOT VERIFIED before next run.
- REFACTOR/REVIEW: only official package loader alias and fail-closed source check; no ROS/Nav2/CM/Guard mutation, no velocity or Goal, no TTL change. Original Gazebo physical RGBD L2 and independent official Path L2 were PASS in prior source; a new commit must be verified for changed behavior.

## 판정
New L0/L1: NOT_RUN. Real same-world simultaneous RGBD+YOLO/Depth distance 2 VALID+UNKNOWN remains HOLD. Task02 official first Path L2 verified separately at ffff731; three official Path phases and real /scan CM subscription not yet; Owner WSLg NOT_RUN, Moving G07 strict HOLD. Main branches NO.
