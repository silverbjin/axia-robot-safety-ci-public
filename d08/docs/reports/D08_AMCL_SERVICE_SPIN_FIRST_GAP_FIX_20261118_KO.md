# AXIA D08 — AMCL 서비스 준비 대기 중 Scan·Odom 콜백 정체 최소 회귀·수정 보고서

## 범위·변경 금지선
- 수정 대상 **하나**: `d08/harness/d08_amcl_initial_pose.py`; 새 L0 테스트 `d08/tests/test_d08_amcl_service_discovery_starvation.py`; 기존 공개 CI 워크플로의 테스트/현장 동일 World L2 계측만 보강.
- 기존 공식 ROS 2 Jazzy/Gazebo Harmonic/Waffle/Nav2/Collision Monitor/yolo_ros, 실제 /scan·/odom 신선도 **0.5초**, G07/Guard TTL, World SDF/생성기, nav2 launch, Owner WSLg GUI/renderer, Student/Instructor 정답 **무변경**.
- 소스 대상 PR [Public #166](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/166), `feat/d08-unified-sensor-cm-path-20261118`, 처음 작업 진입 HEAD `4963f6ae306a25cf61f9f9278ce9b57c75df49b3`.
- 현재 브랜치는 이전 Owner 오류 대응으로 초기 NO_GOAL 1.0s 회복 관측 및 fake executor pause 0.65s CI L2를 이미 갖추고 있으므로 **재구현하지 않고 그대로 보존**. 여기서 수정할 최초 경계는 서비스를 기다리면서 단일 관측기 스핀 중단이 발생하는 별도의 구조적 문제.

## 실제 원본 증거와 최초 위반
- Owner 업로드 `run_20261118T115317Z_QEBQYv.tar.gz`; SHA256 `905f85c4777414ce8edd1dae21cb1114879789c64aa827b0c97ba148baa968fd`.
- 기존 실행기 `a83629edd71ce51567e184451f2a76bafcf1318b`; 실제 `/scan` 최초 host callback gap **2.065084초**, `/odom` **1.952984초** (허용 0.5s), 최초 AMCL Pose stamp 1.602s/source age .108s; 실제 TF map→base_link stamp 2.628s; 마지막 Scan/Odom 수신 age .049586/.001060s. 물리 센서 publisher gap, ROS bridge/RMW, Python executor 중 어느 것이 2s 원인인지 **아직 직접 분리하지 못함**.
- 기존 `d08_amcl_initial_pose.py`는 하나의 rclpy observer node에 Scan/Odom/Clock/TF2를 구독하고, service-discovery를 `cli.wait_for_service(timeout_sec=12)`로 수행함. 공식 `ros2/rclpy@jazzy:rclpy/rclpy/client.py`는 내부 `time.sleep(0.25)` polling을 사용. 이 구간에 별도 executor 스레드가 없으면 observer callback이 처리되지 않을 수 있음.
- 처음 실패 `D08_FIRST_LIVE_SCAN_ODOM_GAP`는 실제 안전 경계에 맞춰 HOLD 처리된 결과로, 수정 이후에도 진짜 데이터 공백이 발생한다면 보존되어야 함.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
1. **RED L0**: fake clock + fake service readiness 2.0초 + 10Hz Scan/20Hz Odom callback을 사용한 순수 Python 테스트에서 서비스가 준비될 때까지 `spin_once`가 계속 실행되어야 한다는 계약을 먼저 추가. 원본 2.065084/1.952984s 첫 gap의 fail-closed 회귀와 ROS source stamp delta vs host receive delta 구분 회귀도 추가. Fake 값은 실제 Gazebo 증거로 사용 금지.
2. **GREEN 최소 수정**: `cli.wait_for_service`를 같은 rclpy node의 `service_is_ready()`+짧은 `rclpy.spin_once` 폴링으로 치환. `/set_initial_pose` 1회 call_async/ACK, 최초 실제 AMCL Pose와 TF 검증, Scan/Odom 0.5s 신선도·첫 gap 증거 모두 유지. 서비스 준비 후 Scan/Odom fresh 재검사 추가.
3. **계측 보강**: 서비스 discovery wall wait/spin count 및 그 동안 실제 /scan·/odom·/clock callback 수, 최초 receive gap, /clock observed RTF, 실제 header.stamp max interval을 `amcl_receive_timing.json`에 보존. Reporter는 `publisher_rmw_cadence_measured=false`를 유지하며 callback gap만으로 publisher 장애/안전 PASS 주장 금지.
4. **L2 동일 실제 Gazebo**: 기존 공개 `gazebo-official-nav2-oneworld` **정확한 HEAD** run을 재사용, 별도 새 월드·새 노드 없이 CI에서 **service discovery 준비 2초 holdoff**를 시뮬레이션하되 Scan/Odom/Clock 메시지는 실제 Gazebo/ROS에서만 수신. 기존 0.65s 일시적 executor pause 회귀와 공식 AMCL/TF/3 Path 인수도 유지. native `/scan`/ `/odom` source sim stamps 및 host gap, `map→base_link` TF stamp, 서비스 응답 시각을 비교.
5. **REVIEW**: L0 fake가 L2 실제 증거가 되지 않았는지, 실제 500ms 데이터 경계가 완화되지 않았는지, 공식 Nav2/CM·ROS/World/GUI/Student/Instructor가 변경되지 않았는지 검토 후 commit.
6. **인수**: L0 + 실제 ROS2/Gazebo L2 성공이 있더라도 **Owner WSL2 D3D12 GUI L3 NOT_RUN**, MOVING G07 strict HOLD. 현재 Head에서 소스와 무관한 기존 성공 테스트 불필요 반복 금지(워크플로가 자동 실행하는 기존 필수 job은 별도).

## 실제 명령·증거 기록
- L0: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q d08/tests/test_d08_amcl_service_discovery_starvation.py d08/tests/test_d08_static_amcl_witness.py d08/tests/test_d08_owner_first_scan_odom_gap_regression.py`
- L2: 이미 존재하는 `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`의 `gazebo-official-nav2-oneworld` job, 같은 기존 `d08/scripts/d08_public_gazebo_l2.py --official-nav2 --official-path-phases --ci-owner-repro` 사용.
- 원본: `results/d08-official-nav2-sameworld/amcl_receive_timing.json`, `official_nav2_before_path.json`, `verdict.json`, native Gazebo/Nav2 logs, SHA256SUMS.
- RED 실제 CI Run/출력: **PENDING (작성 시점, 성공 주장 금지)**.
- GREEN 실제 CI Run/출력: **PENDING (작성 시점, 성공 주장 금지)**.
- 실제 검증 수준: 0→CI 실행 후 기록. 미검증 Owner WSLg/NVIDIA/OpenGL 렌더링, 공식 CM 내부 RMW-source/Guard TTL, 실제 moving Goal.
- Branch: `feat/d08-unified-sensor-cm-path-20261118`; main 병합 **NO**. 결과 SHA/Run URL은 RED/GREEN 뒤 같은 보고서에 남김.
