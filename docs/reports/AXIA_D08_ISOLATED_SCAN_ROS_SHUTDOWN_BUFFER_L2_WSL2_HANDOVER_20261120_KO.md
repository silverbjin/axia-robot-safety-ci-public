# AXIA D08 — 독립 ROS witness 종료 증거 유실 RED→GREEN 및 WSL2 인계 (2026-11-20)

## 결론
- 한정 범위의 공개 CI 인수 후보: **공개 실제 Jazzy/Gazebo Harmonic/TB3 Waffle/공식 Nav2 NO_GOAL 8-cycle L2 SUCCESS** (CI #44671619213, 런타임 SHA d6a9c490ffb1430cd49443a2648577459fa667bf).
- WSL2/WSLg NVIDIA 현장 GUI 실기: **NOT_RUN**, 인수 판정 HOLD. 505.365/518.394/534.476ms 최초 Observer 수신 지연 **근본 원인 UNDETERMINED**. 진단 수집 안정화만 검증; 반복 안정성·CM 내부 120ms/Guard 150ms/Moving E2E 미검증.
- 기존 PR #188 SHA 28c554b1a112499af9f8e1159a77e1f70185ab8b의 L0 221 및 실제 Nav2 L2 8-cycle PASS 보존. PR #189 Moving GUI 별도 HOLD, main 병합 없음.

## 최초 현장·CI 실패 경계
1. PR #201 CI #44669849419: 원본 Gazebo/Nav2 before→intrusion→restored 8-cycle 및 clean shutdown은 성공. 독립 ROS 별도 witness에서만 521.381ms 수신 공백 (동일 source stamp Native Gazebo 201.066ms, 원본 Observer 198.790ms). strict witness gate FAIL. 독립 프로세스가 LaserScan 수신 콜백마다 즉시 JSON 파일에 기록하는 구조 발견. 디스크 I/O의 실제 근본 원인 여부는 미확정.
2. PR #202 최초 수정 SHA 60cc10313cae67423d75ff8027df2771de71cf09: 첫 Scan만 동기 저장하여 기동 준비 ACK 보존, 이후 bounded 메모리 큐에 기록하고 정상 종료에서만 flush. 공개 L0 #44670938985 3/3 PASS. 그러나 실제 Gazebo/Nav2 #44670938997 FAIL: 8개 cycle의 isolated_ros_scan_rx.log 모두 rclpy.spin_once에서 ExternalShutdownException. ROS Context SIGTERM 종료 때문에 정상 루프 뒤 파일 flush 코드를 실행하지 못해 각 cycle 데이터가 첫 1건만 남았음. 원본 메시지·Nav2 장애로 혼동 금지.
3. 추가 회귀 RED #44671521164: SIGTERM ExternalShutdownException에서 flush가 보호되지 않는 구조를 정확히 검출 (4 tests 중 1 FAIL).
4. 최소 GREEN SHA **d6a9c490ffb1430cd49443a2648577459fa667bf**: d08/harness/d08_ros_isolated_scan_probe.py의 종료 경로에 ShutdownException/ExternalShutdownException을 제한적으로 처리하고, 파일이 열린 try/finally에서 bounded 원본 source stamp를 저장. 관련 공개 L0 #44671619104 SUCCESS (4/4). 새 planner, Goal, /cmd_vel, ROS safety TTL, Gazebo LiDAR publisher, Nav2/CM/Guard 코드 변경 **없음**.
5. 실제 Gazebo/Nav2 Xvfb 공개 CI #44671619213 **전체 SUCCESS**: l0-human-proxy-red-green 221 PASS, gazebo-official-nav2-oneworld SUCCESS, 실제 8-cycle before/intrusion/restored 및 clean teardown. 출력 D08_CI_REAL_GUI_EIGHT_REPEAT_PATHS_L2_PASS, D08_REAL_SAME_RUN_EIGHT_CYCLES_SCAN_ODOM_CLOCK_CADENCE_L2_PASS_NOT_CM, D08_OWNER_RMW_PUBLIC_L2_OFFLINE_CONTRACT_PASS_NOT_WSL2. 원본 Observer 459.509ms near-boundary 1회가 있었으나 500ms FAIL 없음. 독립 ROS 원본 수신 기록 complete; 최대 별도 일부 cycle 353.466ms로 500ms 아래. 근본 원인 확정이나 장기적인 500ms 이내 보장 **아님**.
6. WSL2 Owner one-shot 고정 SHA 변경 시험 RED #44672303607: 래퍼가 이전 CI 성공 구버전 099897...을 참조함을 재현. 이후 d08/scripts/d08_owner_take_dispatch_wsl2_one_shot.sh 런타임 SHA를 위 d6a9c...로 변경. 래퍼 L0 GREEN은 후속 공개 CI 확인 후 기록.
7. 기존 학생/강사 교육 구현 답안, Supervisor/CM/Guard, 명시된 safety 120/150ms, 500ms Scan 한계, 원본 d08/scripts/d08_owner_no_goal_bootstrap.sh, d08/scripts/d08_owner_rmw_first_gap.py, d08/scripts/d08_compact_evidence.py는 모두 변경하지 않음.

## 코드·증거 경로
- 독립 진단 원본 경로: d08/harness/d08_ros_isolated_scan_probe.py
- 본문 ROS 원본 Observer 선택적 take→callback 추적: d08/harness/d08_same_world_replan.py, d08/harness/d08_rcl_take_dispatch_probe.py
- 테스트: d08/tests/test_d08_isolated_scan_buffered_io.py, d08/tests/test_d08_rcl_take_dispatch_probe.py
- 원샷: d08/scripts/d08_owner_take_dispatch_wsl2_one_shot.sh
- 경량 ZIP 추출기 immutable SHA 2b3080510dfee6c9da80cf515da29663f19d27a3 / Git blob 142c4dcc820a04accdf869b4cc903f62c7977b2c
- Owner 원본 Git blob 1a17ddaab0eac123188e29cf031c819187c4f82d
- WSL2 최신 실행 root: ~/axia_d08_owner_runs/once_*/run_*/
- 제출 파일: 해당 once_*/D08_LATEST_FIRST_BOUNDARY.zip (<=8MiB, 원본 ROS/CTF 및 모델은 현장에 보존)
- 사용자 현장 NO_GOAL 단일 시연 원샷은 GitHub HEAD 고정 URL과 Git blob sha256이 확인된 후에만 출고.

## 검증 수준과 수락 조건
공개 CI L0는 ROS-free 계약 검증, L2는 실제 Linux Xvfb Gazebo/Nav2/Scan/RMW 8-cycle (GPU WSLg 아님). 현장 WSL2 NVIDIA D3D12+Gazebo GUI software+GPU 센서 혼합 조건, 영상 내용 및 새로운 500ms 현장 경계는 1회 L3에서 검증해야 함. L3 신뢰성 또는 Safety TTL 전체 인수로 승격 금지. 최초 새로운 오류는 최초 RMW/native/독립 ROS/원본 Observer Scan gap과 최초 안전 상태 전이를 증거로 분리, 재현 가능한 부분을 CI RED→GREEN. 반복 현장 시험만으로 성공 처리 금지.
