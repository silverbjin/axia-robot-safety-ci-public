# AXIA D08 — CM Lifecycle 서비스 조회 A/B 실측 L2 및 WSL2 최초 500.535ms 보고서

작성 2026-11-21 KST. Draft PR #206. 브랜치 feat/d08-cm-service-ab-isolation-20261121. main 병합 없음. 범위: NO_GOAL 교육용 원인 분리.

## 1. 보존할 근거

기준 PR #188, SHA 28c554b1a112499af9f8e1159a77e1f70185ab8b: L0 221 PASS 및 실제 Gazebo/Nav2 8-cycle PASS 보존.
PR #204, SHA 31e2d0662c39e4e35781d9d62f0d98699d383845: 실제 YOLO/RGB-D/D05 동일 월드 공개 CI #44736215113 PASS 보존.
PR #205, SHA e00d851e4dc20f10bcae65b1ddfa6c42962cca16: 강사 WSL2 원본 ZIP run_20261120T143716Z_Fj7oCf.diagnostics.zip SHA256 검증, 개인정보 및 원본 공개 업로드 없음.

최초 현장 FAIL: 원본 Observer Scan 간격 500.535ms > 500ms. LaserScan 헤더 소스 39.102→39.201s, monotonic 272.757400→273.257935s.
동일 소스쌍 Native Gazebo 165.625ms, 별도 OS ROS 164.282ms, 동일 Python 다른 Executor 496.165ms, 원본 take 간격 500.334ms, take→callback 진입 0.048ms.
CM 서비스 조회 272.342032→273.620514와 최초 실패 구간 전체가 중첩됨. 중첩이 원인이라는 증거는 없음.
CM Active / Scan 토픽 확인은 CM 내부 수신 TTL 120ms나 Guard TTL 150ms 검증이 아님.

## 2. A/B 원리와 구현

가설: 같은 Python 프로세스의 CM Lifecycle 서비스 조회 중 rclpy Executor의 Scan 수신이 지연될 수 있다.

A: 원래 Observation Python 프로세스에서 실제 CM GetState/GetParameters 읽기.
B: 별도 OS ROS 2 프로세스에서 동일 서비스 조회, 원래 Observer의 Scan 콜백과 QoS는 그대로 유지.
같은 실제 Gazebo/Waffle/Nav2 월드에서 A/B를 교대 4회씩 8-cycle.
CM 실제 Active, observation_sources=scan, scan.topic=scan 또는 /scan 확인은 두 모드 모두 필수. 예외나 잘못된 서비스 응답은 Fail-Closed.
500ms Scan 경계, 공식 Planner, Collision Monitor, Supervisor, Guard 및 안전 TTL 변경 없음.

변경 파일:
- d08/harness/d08_cm_native_probe_isolated.py : 별도 ROS 프로세스 CM 읽기, 결과 검증, 모드별 8-cycle 통계, Nav2 최초 CM 설정 handoff 진단.
- d08/harness/d08_same_world_replan.py : 지정된 모드만 실제 CM 조회에 적용. 원본 콜백 그대로.
- d08/scripts/d08_public_gazebo_l2.py : A/B 교대, 원본 결과 JSON, 500ms 위반 시 최종 HOLD 유지, 최초 Nav2 CM 설정 장애 기록.
- d08/tests/test_d08_cm_service_process_ab.py : ROS-free 회귀.
- .github/workflows/d08-cm-service-ab-l0.yml 및 .github/workflows/d08-main-no-goal-real-gazebo-l2.yml : L0/실제 Gazebo L2.

## 3. RED→GREEN→REFACTOR→REVIEW→COMMIT

RED 공개 #44764122661: 신규 6회귀 중 2 FAIL, 4 ERROR. 별도 OS query 미구현, 실행기 A/B 누락.
실제 WSL2 CM 토픽 scan을 /scan만 허용하는 신규 검증기 오류 RED #44765970837 (6 중 2 ERROR). 공식 Nav2 CM 설정 규칙과 같게 둘 다 허용, 다른 토픽 거부. GREEN #44766088721 (6/6 PASS).
선행 CI #44766088696 실패: Planner inactive는 후속 상태. 공식 Lifecycle Manager가 Configuring collision_monitor 요청 후 CM Configure 콜백 진입 및 응답 로그 없음. 실제 Nav2 로그를 분석한 후 earliest CM handoff를 nav2_cm_startup_boundary.json에 기록하는 회귀 추가. 원인은 UNDETERMINED, 노드 비활성화나 기동 제한 완화 금지.
A 첫 실제 >500ms Scan failure가 발생하면 한정된 진단을 위해 B 결과를 추가 수집하되 최종 전체 HOLD, CM/TF/Planner 다른 첫 오류는 즉시 중단. RED 후 제한적 GREEN.
최종 L0 #44768099832: 10/10 PASS, 출력 D08_CM_PROCESS_AB_L0_PASS_NOT_GAZEBO_NOT_WSL2. 기존 공개 D08 L0/GUI 렌더러/Take-Dispatch도 GREEN.
실제 공개 Linux Xvfb ROS 2 Jazzy + Gazebo Harmonic + 공식 Nav2 L2 #44768100012 전체 SUCCESS. 실증 코드 SHA 682ee4a1670789a288b12af60d307f49f7e53202. 아티팩트 d08-official-nav2-oneworld-l2-evidence, artifact ID 14644859188, ZIP 114개 파일 CRC 정상. 실제 8-cycle 전부 CM Active + 실제 source 확인, Native/독립 ROS/Observer 동일 헤더 쌍 확인, 최초 500ms 위반 없음, 정상 종료.

## 4. 실제 8-cycle 관측 수치

A(in_process) cycle 0/2/4/6: 원본 Observer 동일 소스 최대 간격 239.539 / 238.400 / 241.466 / 423.447ms. 전체 최대 423.447ms, 중앙값 240.503ms. 실제 CM 상태 조회 시간 0.265177 / 0.264389 / 0.256409 / 0.472367초.
B(isolated_process) cycle 1/3/5/7: 최대 간격 244.923 / 233.311 / 242.831 / 230.845ms. 전체 최대 244.923ms, 중앙값 238.071ms. 별도 프로세스 생성 포함 조회 시간 3.325211 / 6.085413 / 3.356495 / 2.834715초.

A cycle_0006 같은 Scan 소스 쌍: Native Gazebo 132.402ms, 별도 ROS 347.038ms, 동일 Python 독립 Executor 422.562ms, 원본 Observer 423.447ms. RMW 분류 ROS_BRIDGE_DDS_OR_SHARED_HOST_DELAY_CANDIDATE. CM 조회와 해당 간격이 355.265ms 중첩. Observer spin_once 최대 332.518ms, 같은 Python 다른 Executor 최대 231.371ms. cause=UNDETERMINED.
독립 ROS까지 지연된 점에서 같은 Python의 CM 서비스 호출만을 원인으로 지목할 수 없음. B의 작은 표본 최대값이 낮다는 점은 후보 증거이나 실제 WSL2 개선 증거가 아님. B는 시작 비용으로 조회가 2.8~6.1초 걸렸으므로 Owner의 기본 동작으로 승격하지 않음.

## 5. 정확한 실행 명령 및 검증 수준

L0: python3 -m unittest discover -s d08/tests -p test_d08_cm_service_process_ab.py -v
실제 CI: xvfb-run -a -s '-screen 0 1280x720x24' python3 -u d08/scripts/d08_public_gazebo_l2.py --actor /tmp/axia-d08-nav2-assets/walk.dae --out results/d08-official-nav2-sameworld --official-nav2 --official-path-phases --ci-owner-repro
A/B 환경 변수 AXIA_D08_CM_AB_MODE=1, Native Gazebo/독립 ROS/RMW probe 켜짐.
실제 결과: results/d08-official-nav2-sameworld/d08-cm-service-ab-comparison.json 및 ci_owner_replan_cycles/cycle_0000~0007/verdict.json.

검증: 공개 CI L0 PASS, 실제 Gazebo/Nav2 8-cycle L2 PASS. 기존 D05+YOLO L2는 과거 증거 보존; 이 A/B SHA에서 해당 작업 SKIPPED라 전체 Owner 인수로 표시하지 않음.
미검증: WSL2 NVIDIA D3D12/WSLg L3 NOT_RUN, 기존 500.535ms 실측 지연의 최종 원인 UNDETERMINED, CM 내부 Scan120ms/Guard150ms 및 최초 안전 전이 NOT_VERIFIED, Moving E2E HOLD, 인증 E-Stop 아님.
WSL2 수정 실행기 출고 HOLD. 본 A/B 결과만으로 원인 해결 또는 장기 안정성을 주장하지 않음. main 병합 없음, 기존 PR #189 Moving GUI 별도 HOLD.
