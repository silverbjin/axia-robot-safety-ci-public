# AXIA D08 — Task04 official Microsoft NuGet 1.20.0 fix / RED→GREEN candidate

## Baseline
- Repo Public CI; branch feat/d08-unified-sensor-cm-path-20261118; base main 62e366b51c64da25ad0216328fe1e019b78e0bef; PR #166.
- Exact previous CI HEAD a538c15a956f4bf4ff651c306a0bdafba113ce48, Run #44202916170.
- Actual RED: the Gazebo real RGBD/scan/physical obstacle test PASSED; upstream yolo_ros build failed *before compilation* because official Microsoft GitHub ONNX Runtime 1.20.0 tarball requested URL returned HTTP 404, exit2. The four occurrences are evidence, not guesses.
- First failure boundary: external source artifact acquisition; not Nav2, Gazebo, sensor or safety timing.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- New plan revision before code: 672d16bdd7ba4d6151f8ec3fe37f28306332ac7b.
- Version remains exactly 1.20.0. Source changed to **Microsoft-published NuGet** Microsoft.ML.OnnxRuntime 1.20.0, not a third-party recompiled fork and not a new YOLO engine.
- New d08/scripts/d08_prepare_official_ort_nuget.py validates ZIP, package ID/version, same-package C++ headers, ELF64/x86_64 lib and SHA256; prepares original yolo_onnxruntime_vendor's documented -DONNXRUNTIME_ROOT input. Exact official LICENSE and ThirdPartyNotices.txt retrieved at v1.20.0 tag, otherwise BLOCKED.
- d08/tests/test_d08_official_ort_nuget.py L0 RED/GREEN fixtures (NOT real ONNX inference). Workflow retains pinned yolo_ros SHA 94d2dd500cb26027ee9c019f4d3a02029ac615cc and original generated real Gazebo RGB frame ROS DetectionArray replay test.
- Actual new SHA CI L0 and C++ L1 result pending. Do not declare GREEN until same SHA build and DetectionArray run; no fabricated pass.
- REVIEW: no change to Nav2/CM/Guard/TTL/robot command path. No private instructor answer used.

## Known limits
- Even successful C++ replay of an actual captured RGB frame is not a same-world continuously synchronized YOLO/Depth sample. Task01 2 REAL VALID + UNKNOWN and Task02 native /scan → official CM and Nav2 3 Path states still HOLD.
- Prior scan host-receive first gap 519.095ms > 500ms; other safety timing layers NOT_VERIFIED. G07 MOVING HOLD, Owner L3 NOT_RUN.
- All main branches unmerged, approval pending later.
