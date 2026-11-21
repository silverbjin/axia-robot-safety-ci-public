# AXIA D06/G07 — NVIDIA Scan 300ms 최초 인과 계층 확인 및 종료 -11 증거 기반 조치 (2026-11-19)

## 1. 기준 원본 (Owner WSL2 실제 관측; 기존 증거 보존)

- 업로드 `d06-forensic-ab-no-goal-yBT9gFbJ.tar.gz` SHA256 `ba460947ac0415eb539b090d17f21dd056c9cde8fe77db1e497326f21973503e`.
- `NO_GOAL_SENSOR_UNSAFE_HOLD`, Clock RTF **0.913157**, LiDAR simulated source **9.999441Hz**, Safety wall **9.131648Hz**.
- Safety `180/180 CLEAR`, 전방 median **1.414687m**, 측면 **2.520466m**; 이번 NVIDIA 조건에서 이전 전방위 근거리 오류는 재현되지 않음.
- 가장 가까운 실제 안전 차단: Safety max wall-receipt gap **421.172ms >300ms**, first index6; Raw max **427.761ms >300ms**, first index11. 정확히 일치하는 Raw timestamp pair의 observed gaps 약 390.708ms, Safety 387.036ms. **index6/11은 서로 다른 토픽 가입 시점이므로 절대시간 선후 관계를 증명하지 않음.**
- native `launch.log` 427행 Collision Monitor `exit -11` 및 428행 `gz sim -r -s exit -11`, 둘 다 launch shutdown 국면. 별개 failure이며 segfault stack 없음.
- 기존 압축의 `first_stop_and_timing.txt`는 비어 있고 수신시각 전체 trace도 미포함: 최초 안전 STOP 시각, ROS/Gazebo 최초 레이어 인과는 **원본만으로 UNDETERMINED**.
- `P2_L2_GRACEFUL_TEARDOWN` 마커는 자식 -11을 무효화하지 않음. `Goal=false`, `CERTIFIED_ESTOP=false`, `MOVING=HOLD`.

## 2. 구현 — 기존 D08 코드를 그대로 재사용하고 한 번의 Owner 세션에서만 계측

- **공개 branch:** `fix/d06-wslg-lidar-vs-rtf-ci-20261118`; [PR #177](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/177) Draft (main 미병합).
- **기존 D08 Gazebo Transport native receiver 그대로 재사용:** 공개 SHA `30fad621f7916dd8a320489beb46fff8ae0ccf43`, blob `7d5f18c5fd6255c83100e29d651b6f4d52ed000d`, `d08/harness/d08_gz_native_scan_probe.py`. /scan과 /clock host-monotonic timestamp 수신. Gazebo 내부 publisher send 시각은 아님.
- **D06 신규 ROS receiver/classifier:** `d06/tools/d06_g07_scan_rx_witness.py` SHA `1f3effb77e74e89eda048dd8a82ae9567db09f7b`, blob `fd17616ec2a6d9cd7363d078493ed784bded36ba`: read-only ROS `/scan`+`/safety/scan`, 동일 host-monotonic 및 source stamp, **300ms hard TTL 그대로 사용**, 두 토픽의 절대 호스트 시간 중 최초 위반 추출; native source stamp 정확히 대응될 때만 계층 후보 출력. Goal/Twist publisher 없음. 검사 결과가 좋아도 release=HOLD.
- **기존 Owner no-Goal wrapper 기능 연결:** `d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh` Owner SHA `2385dcfb22be9293d4ca161f43c54c535f8c0bcb`, blob `d06c0be29ff0ad6cd0c3dc08f86be9ea17287719`. `AXIA_D06_G07_RX_WITNESS=1`일 때만 pinned D08+ROS read-only child 실행. 기존 Student `e4c2007064bec2103bb743bd27cdbdf0955961b7`, smoke/launch/CM/Guard/Nav2 완전 재사용, 동일 `GZ_PARTITION`과 실제 Gazebo/RViz GUI 한 세션. 센서 probe 완료 시 두 witness를 정지하고 비교 JSON 기록. 실패 시에도 raw archive 저장; 자식 PID 정리. apt 기반 `/usr/bin/python3`만 사용.
- **사용자 배포 원샷:** `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh --nvidia-causal`; 단 하나 NVIDIA no-Goal 세션 + 같은 native/ROS witness. Intel 2차 실험 없이 종료. 기존 `--nvidia-only`, `--analyze-existing`, `--compare` 유지. 실제 Scan TTL 불합격과 native -11은 별도 HOLD. 
- **최소 증거 자동 압축:** `d06-forensic-ab-no-goal-*.tar.gz`+`.sha256`. SHA 검증된 원본 Owner TAR에서 `native/d06_gz_scan_receipts.jsonl`, `native/d06_gz_clock_receipts.jsonl`, `native/d06_ros_scan_receipts.jsonl`, `native/d06_g07_scan_delivery_layer.json`과 Scan/Shutdown/Renderer excerpt/원본 해시만 경량 포함. 원본 대용량 TAR 보존.

## 3. RED → GREEN → REFACTOR → REVIEW → COMMIT

1. **RED:** [공개 CI #44435357054](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44435357054) / commit `d3bef8c097e6b80d5823db9953cc552a8c72104b`, 신규 실제 Owner 숫자 fixture + native/ROS same-stamp 수신 계약이 구현되지 않아 실패. 
2. **GREEN:** [공개 CI #44436206002](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44436206002) / `198dff7d158ee4728b4e70f8923ad6d46be3b858`, **L0 32/32 PASS**, 실제 NVIDIA historical HOLD + paired native fast/slow/unmatched + crash fail-closed + tar SHA 검증/쉘 구문.
3. **REFACTOR:** first Safety index6 vs Raw index11의 인과 선후 추정 제거, 각 토픽의 **host monotonic breach 발생 시각**으로 최초를 계산. 독립 timestamp가 없으면 `INSUFFICIENT` 또는 `UNDETERMINED`; 어떤 후보에서도 이동 허가 없음.
4. **REVIEW:** /usr/bin/python3 ROS2 Jazzy + gz transport13 사용, Git SHA/Git blob 정확한 source pin, Owner/ROS/GZ 자식 PID 및 원본 SHA 보호, CI에서 `--nvidia-causal` 강제 차단, 실제 -11과 Python Traceback 판정 구분. CM120ms/Guard150ms/Scan300ms 무변경.
5. **검증의 한계:** 공개 L0는 fixture 및 contract 검사이며 **현장 WSLg 실제 Gazebo/ROS same-session은 아직 NOT_RUN**. 기존 D08 native L2 성공 [#44355469883](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44355469883)은 D08 선례일 뿐 이번 G07-Waffle 특정 시연 인수가 아님.

## 4. Owner 단일 명령을 위한 필수 실행 전제

- 이미 설치된 `/opt/ros/jazzy/setup.bash`, Gazebo Harmonic, NVIDIA WSLg, ROS2 GUI, `curl`, `git`, `glxinfo`.
- 추가 read-only Python native subscription에 시스템 패키지 `python3-gz-transport13` / `python3-gz-msgs10`이 필요. 배포 명령 블록에서 필요 시만 설치해야 하며, 임의의 ROS2/Gazebo 버전 업그레이드는 금지.
- 단일 NVIDIA `--nvidia-causal`, NO_GOAL_ONLY. **실패해도 증거 TAR/SHA 자동 생성**. 큰 로그를 수동으로 여러 번 추출하지 않도록 `D06_FORENSIC_ARCHIVE` 하나만 공유.
- 다음 실제 행동은 새 native timing layer가 `AT_OR_BEFORE_NATIVE_TRANSPORT_RX`인지 `AFTER_NATIVE_TRANSPORT_RX`인지부터 분리하고, 그 후 별도의 child `-11`을 Nav2 ordered shutdown/Gazebo 렌더러 폐기 순서에서 좁혀 RED→GREEN. 리스크 조사가 되기 전 기능 코드 임의 변경 금지.
- 다음 단계에도 `D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`, `MAIN_MERGED=false`.


---

## 6. 2026-11-19 Owner UCMOonHr: 실제 native Scan+Clock 첫 실패 재현과 최소 수정

### 증거 / 검증 수준
- 사용자 제출 d06-forensic-ab-no-goal-UCMOonHr.tar.gz SHA256 4d374b1caf58ffe113dcecffd315a84356834cd4c8bac2a3143251ae03d4ed3e. 체크섬 사이드카 직접 일치. 원본 provenance Student SHA e4c2007064bec2103bb743bd27cdbdf0955961b7.
- NVIDIA, NO_GOAL, 실제 Safety 172/172 CLEAR, 전방 median 1.415538m / 측면 median 2.520587m, 전 구간 Clock RTF 0.873921.
- 원래 NO_GOAL probe Safety max wall receipt gap 336.166ms (첫 index 14), Raw max gap 322.090ms (첫 index 17), 300ms safety TTL FAIL. 인덱스가 다르면 절대시간 선후를 증명하지 못함.
- 추가 동일 세션 timestamp pair Gazebo native /scan host 104.837286→105.151753s = 314.467ms, ROS /scan 312.642ms, ROS /safety/scan 322.424ms. Scan source timestamp 51.300s→51.402s 정확히 일치. 그러므로 ROS-only subscriber 지연이 아니라 Gazebo Transport 수신 이전 또는 해당 수신 경계에도 최초 위반이 있음.
- /clock 독립 host receipt 근접 구간 104.822859s sim51.300s→105.161897s sim51.435s. Sim advance 0.135s / host 0.339038s = 순간 RTF 약 0.398. Clock 콜백 최대 간격은 약 68ms; 시뮬레이션이 완전히 멈춘 현상과는 구분. 전체 평균 RTF만으로 이 감속을 발견할 수 없음. 이것은 짧은 관측 구간의 Clock 진전이며 Gazebo 내부 publisher 원인/스케줄러 CPU GPU 원인은 아직 UNDETERMINED.
- 런치 로그 429행 Collision Monitor exit -11, teardown P2_L2_FORCED_TEARDOWN. 이번 증거에는 Gazebo 서버 -11 증거가 없음. ros witness는 ExternalShutdownException 이후 rcl_shutdown already called 때문에 exit 1, native witness exit 0. 서로 다른 실패 세 가지(Scan TTL, CM 종료, 진단기 종료)를 합치지 않음.
- 최초 Supervisor 안전상태 전이의 절대 시각은 first_stop_and_timing.txt에 증거가 없어 미확정.

### 실제 코드 작업
- 새 공개 fixture: d06/fixtures/g07_owner_nvidia_native_scan_clock_first_gap_20261119.json (실측 timestamp / Clock / CM-only SIGSEGV, 원본 사용자 경로 제외).
- 회귀: d06/tests/test_d06_g07_native_clock_and_rclpy_shutdown.py. 실제 native+ROS TTL, 순간 Clock slowdown/정상 Clock/누락 Clock, CM-only -11, ROS context 중복 shutdown 모의.
- 실제 수정: d06/tools/d06_g07_scan_rx_witness.py. native Clock window를 최초 native Scan 간격과 호스트 monotonic 근접 표본으로 계산하고 native_clock_progress / native_clock_window_rtf / native_clock_max_host_gap_sec 진단 출력. 진단용 RTF 0.6 경계는 원인 분류에만 사용, Scan 300ms/CM120ms/Guard150ms 및 Goal 승인 조건 변경 없음; cause UNDETERMINED, release HOLD.
- 동일 read-only ROS watcher에서 ExternalShutdownException/KeyboardInterrupt를 안전하게 처리하고 무조건 rclpy.shutdown 대신 멱등성 rclpy.try_shutdown 호출. 기존 알려진 rclpy 문제 참고: https://github.com/ros2/rclpy/issues/1287 와 https://github.com/ros2/rclpy/issues/1081
- d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh에서 기존 녹화된 native /clock JSONL을 같은 세션 분석기로 전달. 외부 원샷 d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh의 immutable Owner SHA/blob 갱신. 기존 D08 native receiver, 공식 Nav2/CM/Guard 및 Student SHA 변경 없음.
- 종료에서 CM -11을 근거 없이 고쳤다고 주장하지 않음. 이미 Student에는 Goal 없이도 official Nav2 lifecycle ordered shutdown을 실행할 수 있는 tools/p2_g07_ordered_shutdown.py가 존재하지만, 현장 현재 기본 NO_GOAL cleanup은 바로 SIGINT이므로 별도 실 Gazebo L2 검증 없이 기존 Owner 종료 스크립트 수정 금지.

### RED→GREEN
- RED GitHub Actions #44440071321 (commit a37b83a1aa9e63758b93f53331a2638d6652df0d): 신규 예상 ERROR 4개 (native_clock keyword 미지원 세 건, rclpy external shutdown 예외 한 건).
- GREEN GitHub Actions #44440542736 (commit 3bcf0c8402cba8be7917d62682aa8aaef41c5a89): L0 38/38 PASS (9+7+5+3+8+5+1), ROS 실제 실행 없음.
- CM-only -11과 기존 Safety+Raw TTL을 독립 HOLD로 유지하는 신규 단일 회귀 추가. 이 보고서의 HEAD 공개 CI 결과도 별도 확인 필요.
- WSL2 현장 신규 ROS/Gazebo 결과 NOT_RUN. NO_GOAL 유지, Moving L3 미검증, SW STOP은 인증 E-Stop이 아님, D06_GAZEBO_LIVE_RELEASE=HOLD / AXIA_MVP_DEMO_ACCEPTED=HOLD / MAIN_MERGED=false.

