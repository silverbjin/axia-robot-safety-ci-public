# AXIA D08 — Exact Scan Take→Callback L2·WSL2 단일 인계 기록 (2026-11-20)

## 고정 근거 및 범위
- 기준 PR #188 SHA 28c554b1a112499af9f8e1159a77e1f70185ab8b: 공개 CI #44465533031 L0 221 PASS / 실제 Gazebo/Nav2 8-cycle L2 PASS 보존.
- 최초 현장 GUI SIGSEGV: WSLg Qt/GLX → Mesa D3D12 → NVIDIA libnvwgf2umx. PR #200에서는 Gazebo GUI에만 software GL 적용; 서버/Nav2/센서/Safety TTL 미변경.
- 이전 신규 실패: PR #200 SHA 5cf51a329f2a90baca33586c01ccf607a162cd73, 공개 #44665818906 최초 활성 Scan 534.476ms (500ms 초과). 정확히 같은 source stamp: Native Gazebo 223.306ms, 독립 ROS 223.221ms, 원본 Observer 534.476ms, 같은 Python 다른 executor 534.648ms. Python 전체 정체, 긴 callback, spin_once 534ms 한 번의 블로킹은 원본 근거로 지지되지 않음.
- 신규 작업 PR #201, branch diag/d08-exact-rcl-take-dispatch-20261120, 실제 통합 시험 코드 SHA 0998978174f9b40ad83bc2fe7907d5dab62115bc.

## RED → GREEN → REFACTOR → REVIEW → COMMIT
1. RED 공개 CI #44667906835: 첫 534ms Scan source stamp의 take completion vs callback dispatch 관측 요구 테스트 4개 중 3 ERROR, 1 FAIL. 신규 계측 파일 없음/원본 Observer 연결 없음이 기대 실패.
2. GREEN: d08/harness/d08_rcl_take_dispatch_probe.py를 추가. Jazzy 원본 rclpy Executor._take_subscription 경로를 참고해 오직 원본 /scan 구독 1개에만 기록하고 나머지 구독/Action은 원본 구현 그대로 사용함. d08/harness/d08_same_world_replan.py에서 AXIA_D08_TAKE_DISPATCH_PROBE=1일 때 선택적으로 적용. 같은 LaserScan header.stamp으로 take_message 완료 시간과 callback dispatch를 결합. 누락/중복이면 HOLD.
3. GREEN L0 공개 CI #44668285006: 4/4 PASS. 같은 SHA의 실제 ROS 2 Jazzy / Gazebo Harmonic / TurtleBot3 Waffle / 공식 Nav2 Xvfb L2 공개 CI #44668285062: L0 221 PASS, Gazebo+Nav2 8-cycle job SUCCESS, before→intrusion→restored 반복 PASS, GUI 및 Nav2/Gazebo 서버 exit0, RMW offline classifier 계약 PASS. Contact/YOLO 별도 작업은 해당 CI에서 SKIPPED. 500ms 초과 활성 Scan 위반은 해당 실행에 없음.
4. L2 구간 cycle_0005에서 실제 Native Scan 133.389ms, 독립 ROS 131.025ms, 원본 Observer 383.318ms, 원본 take completion 간격 383.352ms, take→callback dispatch 0.011ms. 해당 구간 동기 set_pose 중첩은 없음. 이는 원본 같은 프로세스에서 take 단계 이전의 지연 후보를 강화하지만, 특정 waitset/DDS/스케줄러 결함을 확정하는 증거는 아님.
5. CLI 래퍼 WSL2 스크립트 d08/scripts/d08_owner_take_dispatch_wsl2_one_shot.sh는 성공한 런타임 SHA 0998978174f9b40ad83bc2fe7907d5dab62115bc를 고정, 기존 Owner bootstrap Git blob 1a17ddaab0eac123188e29cf031c819187c4f82d 확인, 최신 경량 extractor SHA 2b3080510dfee6c9da80cf515da29663f19d27a3/blob 142c4dcc820a04accdf869b4cc903f62c7977b2c 고정. ROS/Gazebo/WSLg 실제 실행을 주장하지 않음.
6. 래퍼 RED 공개 CI #44669467418 (미존재 파일) → GREEN #44669588564: L0 5/5 PASS + bash -n/--self-check PASS. 최대 8MiB 진단 ZIP과 원본 보존, 단일 NO_GOAL 실행 모드.

## 추적 결과의 의미
take_complete는 rclpy Subscription.handle.take_message 반환 직후 Python monotonic 시점이며, 네이티브 rcl_take tracepoint 그 자체는 아님. RMW DDS source timestamp와 ROS header.stamp의 직접 등가성을 가정하지 않음. 후보는 TAKE_LATE_BEFORE_CALLBACK과 POST_TAKE_DISPATCH_DELAY로 구분하되 root_cause는 UNDETERMINED.
- 505.365/518.394ms 과거 수신 위반의 근본 원인은 아직 UNDETERMINED.
- L0 및 해당 공개 L2 PASS는 WSL2 NVIDIA WSLg mixed GPU/software GUI의 인수를 의미하지 않음. 강사 WSL2 L3 NOT_RUN.
- CM internal 120ms, Guard 150ms, Moving E2E NOT_VERIFIED; 인증된 E-Stop 아님. 500ms/TTL/Planner/CM/Guard/원본 Owner bootstrap/RMW classifier/compact source 변경 없음.
- PR #189 Moving GUI는 별도 HOLD. main 병합하지 않음.
- 강사 WSL2 최초 현장 실패 시 원본을 보존하고 최신 단일 ZIP에서 첫 타이밍/안전 전이를 분석, 공개 CI 회귀 RED→GREEN 후 다시 인수.
