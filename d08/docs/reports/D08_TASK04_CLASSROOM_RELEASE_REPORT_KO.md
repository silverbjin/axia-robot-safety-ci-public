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

## 2026-11-18 최종 공개 코드 인수 후보 보강

- [정확한 Public #44245796892](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44245796892), source=runner HEAD `910d3a22291f0ab8a4585f8dab5501219408171b`: 실제 세계 3 Path와 Live YOLO/D05 2 VALID+UNKNOWN L2 PASS. Owner WSLg 픽셀 NOT_RUN, 안전 CM 내부 timing NOT_VERIFIED.
- Task04 runner `d08/scripts/d08_owner_no_goal_bootstrap.sh`는 public exact SHA clone, pinned official YOLO/ONNX 모델, ROS nounset-safe, 고유 로그 폴더, `--self-check|--doctor|--run` 제공. WSL2를 실제 실행하지 않았으므로 시연 출고 HOLD.
- Latest native CM graph에서 unknown consumer를 발견, 실제 lifecycle active와 `scan.topic` 서비스 조회를 Task02 마지막 최소 회귀로 반영. CM 내부 수신 gap과 Guard age를 이 조회로 대체하지 않음. 새 exact SHA L2 결과는 PR #166에 별도 보고.
- 사용자 승인 전 Student #43/Instructor #212/Public #166의 main 병합은 모두 NO, Moving G07 strict HOLD 유지.

## 2026-11-18 Task04 최종 PUBLIC L2 범위 확정 — 기존 기록에 대한 최신 판정

이 절은 이전의 임시 HOLD·개발 중 PENDING 표기를 최신 사실로 대체합니다.
- Source `a83629edd71ce51567e184451f2a76bafcf1318b`, [Public Run #44248098353](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44248098353) **전 job SUCCESS**, 실제 `103 passed in 0.33s` + 물리 Gazebo L2 + 원본 C++ YOLO L1 + 한 World Nav2/CM/D05 L2 성공. SHA는 PR 기능 HEAD와 실제 checkout 모두 동일.
- 원본 native CM lifecycle `active` / observation_sources `["scan"]` / scan.topic `scan` 직접 조회 GREEN, `D08_OFFICIAL_CM_NATIVE_ACTIVE_SCAN_SOURCE_NO_GOAL`. 실제 CM 내부 receive gap/Guard TTL/출력 감속은 **NOT_VERIFIED**; Robot Goal 및 cmd_vel 미발행.
- 동일 World RGBD/Yolo/Depth 사람 거리 0.704022m/0.534589m, 원인 있는 UNKNOWN; 공식 3상 Path + 실측 Scan 1.866673/0.567960/1.869093m, lethal 0/66/0; observer max Scan callback gap 0.228737s(정지 중 관측자 값, CM age 아님).
- Student PR #43 commit `2db53d55c4f3640e0fb5d73c94f21fc4a512bf04`, Instructor PR #212 commit `61dc409a55529108e2a64aecc9ba793522ec7810`에 동일 Public SHA Owner 원샷/3계층 수업 가이드 존재. 강사 정답·hidden tests는 공개 저장소에 미배포.
- 정확한 공용 Owner script `d08/scripts/d08_owner_no_goal_bootstrap.sh` 옵션 `--self-check|--doctor|--run`; 검증 SHA `a83629edd71ce51567e184451f2a76bafcf1318b`; 수업 화면은 공식 Gazebo+RViz2/원본 Planner Path 표시; 종료 Ctrl+C/소유 그룹 정리. 이 script의 실제 WSL2 `--run`과 WSLg pixel/권한/렌더는 아직 **NOT_RUN/NOT_VERIFIED**. 타 GUI 기본 설정은 설치된 공식 Nav2 config에서 read-only Path 토픽만 임시 overlay로 변경.
- Task04 **Public CI release candidate PASS**, 사용자 Owner L3 시각 인수까지 `D08_LIVE_NO_GOAL_ACCEPTED=NO`. Task03 Moving/CM Guard safety TTL 별도 HOLD. main 병합 3건 모두 사용자 승인 대기.
- 최종 정확한 증거와 현재 범위는 `d08/docs/reports/D08_INTEGRATION_FINAL_ACCEPTANCE_KO.md` 참조. 지난 RED→GREEN 원본 CI 번호·최초 원인 분석은 각 Task 보고서 및 PR #166 이력에 보존했습니다.
