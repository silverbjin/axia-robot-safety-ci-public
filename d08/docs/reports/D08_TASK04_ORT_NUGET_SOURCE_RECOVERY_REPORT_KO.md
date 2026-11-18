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

## 추가 최초 실패 (Run #44205408900; SHA 452b61db1ed4)

- L0 실제 로그: `1 failed, 33 passed in 0.37s`. 오류 위치: `d08/tests/test_d08_yolo_archive_gate.py:12`, **오래된 GitHub .tgz filename을 필수로 고정한 source-only test**, 신규 NuGet 방식과 모순. Gazebo/ROS 실행 전에 종료.
- 동일 소스 변경의 사전계획은 상단 마스터 계획 v1.1로 기록되었으며, 새 코드 실패가 아닌 **이전 검증기 계약 잔존** 문제다.
- RED: public CI 실제 L0 실패 Run #44205408900; GREEN 최소 수정: 이전 테스트 파일을 공식 NuGet 1.20.0 ZIP/ID/version/ELF/header 검증 계약으로 대체. 새 C++ / ROS 성공은 새 exact-SHA CI 완료 전까지 NOT_VERIFIED.
- 새 테스트 실행 명령: `python -m pytest -q d08/tests/test_d08_yolo_archive_gate.py d08/tests/test_d08_official_ort_nuget.py` 및 전체 D08 CI L0.
