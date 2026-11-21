# AXIA D06/G07 Cycle 10 — 실제 RMW 비교 후보와 공개 L2 검증 중간 보고

작성 2026-11-20 KST. 공개 Draft PR #177. 학생/강사 main 및 WSL2 Owner 불변. Release HOLD.

## 1. 원본 경계: C09 원인 후보로만 CycloneDDS를 선택한 근거

기준 실제 Jazzy/Harmonic/TurtleBot3 Waffle/Nav2/Xvfb NO_GOAL L2 [#44566309993](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44566309993), code SHA 84af2ea35ac439b6cf665b323c8d8d19f77a9067, artifact #14552316501.

- Student first Safety TTL pair 52.302→52.401초: Student365.478ms, Gazebo native100.544ms, 독립 ROS Safety102.191ms. Student 콜백이 동일 두 번째 메시지에서 peer보다 263.015ms 늦음.
- Navigation SHUTDOWN ACK1.856059초, Localization manage_nodes 단일 요청 이후30.000354초 ACK 없음. 동일 management callback group is_active27.966ms, get_parameters24.207ms 응답. 송신 client의 실제 RMW는 **rmw_fastrtps_cpp**.
- 센서 10Hz, Scan TTL300ms, CM120/Guard150ms, 공식 Nav2, Goal 정책은 그대로. 전체 public L2 FAIL. 물리적 센서 주기나 QoS 문제라고 단정할 근거 없음.
- 공식 ROS 2에서 지원되는 Jazzy 대체 RMW인 rmw_cyclonedds_cpp를 **공개 Linux CI 단일 실증**으로 비교. FastDDS 서비스 응답 경합 관련 참고: https://github.com/ros2/rmw_fastrtps/issues/842 . 이는 사건 root 원인 **증명이 아니라 조사 후보**. 이 시연의 rmw_fastrtps 버전/실제 rmw_publish 전달과 이슈의 정확한 일치 여부는 확인되지 않음.

## 2. 이미 실패한 유사 CPU 격리 브랜치 조사

- fix/g07-cycle22-cm-exclusive-sixplus-cpu-20261116: 공개 L0 GREEN인데 실제 CM142.776ms >120ms, HOLD.
- fix/g07-cycle23-full-role-cpu-partition-20261116: 11/11 L0 GREEN인데 실제 CM142.906ms >120ms, HOLD.
- fix/g07-cycle37-display-observer-noncm-cpu-20261116: 별도 CPU 분리; 현재 D06 동일 Waffle/native Scan300/Manager ack에 대한 입증된 해결 없음.
- fix/d08-executor-spin-timing-20261119: 실제 Gazebo 8 cycles RTF/Scan 수신 계층 원인 분리 계측 성공(L2 scope only), spin_once wall/thread CPU 보존. 보고서 d08/docs/reports/D08_SPIN_ONCE_FIRST_GAP_L2_RED_GREEN_20261119_KO.md; 실제 Path L2 #44437921180. D06 안전 TTL/Manager ACK 해결이나 WSLg L3 인수 증거는 아님. 계측 재사용 후보로 보존.

## 3. RED → GREEN → REFACTOR → REVIEW → COMMIT

- 신규 공개 test d06/tests/test_d06_c10_ci_rmw_comparison.py: 공개 Linux Xvfb L2에서만 RMW vendor를 교체해야 하고, 실제 lifecycle evidence nav.rmw_implementation_identifier로 설정 확인, TTL/Goal/전체 native exit 엄격 검사 유지, 강사 WSLg Owner 스크립트의 vendor override 금지.
- RED Run #44568537504: 이전 L2 workflow에 RMW_IMPLEMENTATION: rmw_cyclonedds_cpp 및 actual RMW proof 부재를 직접 재현.
- 최소 GREEN 수정은 **공개 워크플로 하나** .github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml: env RMW_IMPLEMENTATION=rmw_cyclonedds_cpp, Jazzy 공식 ros-jazzy-rmw-cyclonedds-cpp 미설치 시 signed HTTPS APT로 설치, 실제 Nav2 shutdown JSON에 RMW ID가 일치해야 전체 PASS. Goal=0, safety TTL 원본 그대로. Ubuntu disposable container 한정, WSL2 Owner 기본환경에 vendor 변경 적용하지 않음.
- GREEN 공개 L0 Run #44568745536 **137/137 PASS**, source SHA 26a3a1b299e404d6e0fe9e69312578db356081ab.
- 같은 코드의 실제 Gazebo + Nav2 L2 [#44568745545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44568745545): 결과 완료 후 원본 first-breach 증거를 별도 추가. L0를 실제 L2 PASS로 대체 금지.

## 4. 검사 기준 / 판정

공개 동일 세션 native Gazebo /clock·/scan, 독립 ROS raw/safety, Student 20초 Raw/Safety, Nav2 Navigation/Localization SHUTDOWN ACK, Guard/Supervisor/CM/Gazebo 실제 process exit0, witness unsubscribe, no Goal/Fault. 300ms 단 한 번 초과해도 전체 FAIL.

설령 Cyclone vendor에서 모두 통과해도 인과성은 여러 변수의 시간적 차이 때문에 자동 확정하지 않으며, **강사 WSL2는 FastDDS 기존 기본설정을 유지**. WSLg NVIDIA Gazebo -11 core backtrace 미확보, GPU 종료 원인 미확정, CM120/Guard150 Moving Goal E2E 및 L3 모두 미검증.

D06_GAZEBO_LIVE_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false

## 5. C10 실제 공개 Gazebo L2 완료 — 단일 세션 정밀 인수 PASS

- 실제 Linux Xvfb + ROS 2 Jazzy + Gazebo Harmonic + TurtleBot3 Waffle + 공식 Nav2, 동일 public code SHA **26a3a1b299e404d6e0fe9e69312578db356081ab**, [Run #44568745545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44568745545) **SUCCESS**.
- artifact #14552428293 압축 ZIP, SHA256 **3846bd9fe8a0c86750b80ae1c1b183e948c197cede48e94badbad25643a66f44**. native/stdout/launch/JSONL 원본 포함.
- 실제 관리 프로세스가 기록한 RMW: **rmw_cyclonedds_cpp**. 설정 문자열과 실제 식별값 일치.
- Nav2 READY host monotonic 278.494s에서 시작하는 엄격 20초 독립 관측: native/raw/safety 각 **199개**. 해당 구간 최대 gap **114.808/114.294/114.993ms**, 모두 300ms 미만. 전체 세션 native456 raw456 safety456, max gap **122.501/123.621/125.325ms**, 전부 300ms 미만.
- Student qualified **20.108초**, Raw202 max **114.426ms**, Safety202 max **114.035ms**, Safety202/202 CLEAR, front median1.414385m, side2.518874m. 모든 first_receipt_ttl_breach_at_index=null.
- Student /clock global RTF **0.999034** (sim_elapsed19.965s / host_elapsed19.984312s). CLOCK 진행 정상, 별개 safety TTL도 실제 수신 간격으로 검증.
- Navigation Lifecycle SHUTDOWN ACK **2.423671s**, Localization ACK **0.593787s**, 두 관리 요청 모두 전송·ACK. 충돌감시 CM 실제 child exit0, Base Guard/Supervisor/Gazebo server도 실제 clean exit. native witness는 subscribe 종료 및 SIGINT handoff ACK, world pause와 /server_control stop:true ACK, teardown P2_L2_GRACEFUL_TEARDOWN. Xvfb Gazebo/RViz 창 확인.
- Goal/velocity/fault/fixture 이동 없음, certified E-Stop 아님. 본 L2 종료 성공은 **NO_GOAL + Linux Xvfb + CycloneDDS** 범위로만 유효.
- artifact d06_g07_scan_delivery_layer.json의 release=HOLD/goal_allowed=false는 의도된 **L3/motion 권한 미부여 플래그**이며 첫 안전 위반 관측은 NO_ROS_TTL_VIOLATION_WITNESSED. 독립 시연 L2 verdict 성공과 모순 아님.

## 6. 원인 확정과 출고 구분

- 기존 C09 동일 개발선 Fast DDS 실측에서는 Student Safety365.478ms, Localization Manage no-ACK. C10 CycloneDDS에서 두 증상이 **같은 단일 실행에 재발하지 않았음**. 하지만 실행 회차/시스템 스케줄링 차이가 있으므로 RMW vendor가 단일 근본 원인이라고 단정 금지.
- 최소 권장 기준선 후보는 **현재 코드 SHA 26a3a1b2…의 CI-only RMW 교체**. 강사 WSL2 실행기에 무검증 전역 RMW override 이식 금지.
- 독립 owner WSL2 NVIDIA WSLg GPU Gazebo 종료 SIGSEGV exit-11 원본 core stack 미확보. Collision Monitor120ms/Guard150ms Moving Goal 실제 E2E 미검증, owner L3 실행 안 함.
- 따라서 **C10_PUBLIC_REAL_GAZEBO_NO_GOAL_L2=PASS**, 그러나 **D06_GAZEBO_LIVE_RELEASE=HOLD**, **AXIA_MVP_DEMO_ACCEPTED=HOLD**, **CERTIFIED_ESTOP=false**. User 승인 전 main 병합 금지.

