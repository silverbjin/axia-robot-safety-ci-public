# AXIA D08 — 공개 CI와 강사 WSL2 D05 인수 범위 일치·최초 Scan 증거 보존 보고서

2026-11-20 KST | PR #204 | 브랜치 fix/d08-owner-d05-ci-wsl2-parity-20261120 | main 병합 없음

## 기준선과 최초 현장 오류

- 기준 PR #188 SHA 28c554b1a112499af9f8e1159a77e1f70185ab8b: 공개 L0 221 PASS, 기존 Gazebo/Nav2 NO_GOAL 8-cycle L2 PASS 보존.
- 현장 실행 소스 d6a9c490ffb1430cd49443a2648577459fa667bf. 업로드 파일 D08_LATEST_FIRST_BOUNDARY.zip 및 run_20261120T112307Z_TuitWg.diagnostics.zip, 원본은 공개 저장소에 게시하지 않음.
- 실측 공식 Nav2 경로 before/intrusion/restored 성공, 원본 Observer 최대 Scan 수신 간격 421.998ms (<500ms).
- 이후 D05 farther 별도 ROS Scan 구독 노드의 최초 BLOCKED: RuntimeError:D08_PERSON_FARTHER_ACTUAL_SCAN_CADENCE_NOT_VERIFIED. Native Gazebo 전체 최대 668.993ms와 독립 ROS 전체 최대 620.016ms는 D05 최초 위반과 동일 LaserScan source stamp 쌍으로 입증되지 않았음. 원인 UNDETERMINED.
- 후속 Gazebo -11 / RViz -6 / 임시 SDF 누락은 첫 D05 Scan 위반보다 먼저 발생한 것으로 입증되지 않음. 추후 종료 정리 계층 별도 HOLD.
- 현장 원본 D05 farther_scan.json을 원래 컴팩트 ZIP에서 누락하고 첫 RMW classifier는 공식 path/cycle만 조회하였기 때문에 실제 D05 위반을 NO_FIRST_GAP_IN_AVAILABLE_VERDICTS로 잘못 범위 제한함.
- 과거 공개 CI #44672467833은 실제 Nav2 8-cycle job만 성공했으며 live YOLO RGBD D05 job은 SKIPPED. Owner --owner-gui에서는 live-person-range가 필수인 범위 불일치.

## RED → GREEN → REFACTOR → REVIEW → COMMIT

1. 공개 RED #44733501848: 신규 5/5 실패, 기존 221개 PASS. D05 JSON ZIP 누락, RMW 첫 위반 누락, D05 verdict 시각 증거 누락, mandatory coverage 미검증, skipped job release 허용을 재현.
2. 수정 파일 d08/scripts/d08_compact_evidence.py: D05 farther/stop 실제 Scan JSON, native ACK allowlist 추가; 무제한 원본 CTF, rosbag, ONNX, 빌드 산출물은 제외.
3. 수정 파일 d08/scripts/d08_owner_rmw_first_gap.py: 기존 공식 Nav2와 Owner cycle 외에 D05 farther/stop의 최초 500ms 수신 위반을 같은 Linux monotonic 시간축으로 병합. 동일 헤더 source_stamp가 DDS native send timestamp와 자동으로 일치한다는 주장은 하지 않음.
4. 수정 파일 d08/harness/d08_live_person_range_session.py: 최초 D05 Stage timing violation를 verdict first_scan_timing_boundary와 stage로 보존; Scan 500ms 한계 및 거리 threshold 변경 없음.
5. 추가 파일 d08/scripts/d08_owner_parity_coverage_gate.py 및 .github/workflows/d08-main-no-goal-real-gazebo-l2.yml: 기존 upstream C++ yolo_ros/실제 RGB-D/D05/Nav2 같은 월드 integration job이 SUCCESS가 아니면 RELEASE_HOLD_COVERAGE_INCOMPLETE. SKIPPED를 PASS로 전환하지 않음.
6. 공개 L0 초기 GREEN 과정 #44733954042: 원본 SHA 체크아웃 계약은 새 release gate job 추가로 4→5 checkout 갱신 필요, 225 PASS/1 FAIL. L0 수정 후 실제 #44734102820에서 226/226 PASS.
7. 공개 통합 L2 #44734102820 (https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44734102820), 검증 소스 c3373bbd66c67cc5d59e99a18127ddc6c58a0d3f: Contact 실측/이미지 사전 증거 SUCCESS, real-gazebo-rgb-pinned-upstream-yolo-ros SUCCESS, d08-owner-parity-release-gate SUCCESS. 공식 Nav2 이전 8-cycle은 재실행하지 않고 보존.
8. 같은 실제 Gazebo/Harmonic/Jazzy/TB3 Waffle/C++ YOLO/등록 RGB-D/Nav2/D05 통합 출력:
   - D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL
   - D08_LIVE_D05_TWO_VALID_ONE_UNKNOWN_L2_PASS: farther=0.704022m, stop=0.534589m, delta=0.16943m, unknown=NO_PERSON_CLASS_IN_ACTUAL_YOLO
   - D08_REAL_LIVE_RGBD_YOLO_D05_NAV2_THREE_PATHS_L2_PASS_NO_GOAL
9. 원샷 래퍼 갱신 RED #44735538141: 신규 PIN 미반영을 정확히 재현 (226 PASS, 신규 1 FAIL). 인계 파일 d08/scripts/d08_owner_take_dispatch_wsl2_one_shot.sh의 RUNTIME_SHA를 실증 PASS c3373bbd66c67cc5d59e99a18127ddc6c58a0d3f로 고정.
10. Wrapper SHA 검증: 기존 원본 Owner bootstrap Git blob 1a17ddaab0eac123188e29cf031c819187c4f82d. 종료 시 생성되는 Owner 원본 run_*.diagnostics.zip을 SHA256 검증·8MiB 상한 검사 후 최우선 제출. 기존 최신 extractor는 부팅 전 실패 보조용으로만 유지하며, D05 ZIP이 누락된 경우를 성공으로 처리하지 않음.
11. WSL2 인계 최종 원샷은 wrapper L0/Git blob 검증 후에만 출고. 원본 raw CTF/모델은 WSL2 로컬 보존, 사용자 제출은 첫 실패 ZIP 1개.

## 검증 수준 및 미해결

- 실제 Linux GitHub Actions Xvfb Gazebo+Nav2+upstream yolo_ros+RGB-D+D05 L2 PASS. 이는 NVIDIA WSLg/D3D12 GUI 자원 경쟁 또는 WSL2 로컬 L3 합격을 증명하지 않음.
- 기존 현장 505.365/518.394/534.476ms 및 이번 D05 최초 Scan 간격 물리적 근본 원인은 여전히 UNDETERMINED.
- CM 내부 120ms 및 Guard 150ms, Moving E2E, 인증된 E-Stop은 NOT_VERIFIED.
- 센서 500ms 안전 한계 미완화, 기존 Nav2/Supervisor/Guard/CM 제어 코드 미변경.
- PR #189 Moving GUI는 별도 HOLD. 새 WSL2 오류는 동일 현장 재시도 반복 대신 원본 최초 안전 상태 전이와 최초 타이밍 위반을 기준으로 CI 회귀 RED→GREEN.
- 강사 정답과 학생 TODO 저장소 분리, 비공개 현장 데이터 공개 업로드 금지, main 병합 금지.
