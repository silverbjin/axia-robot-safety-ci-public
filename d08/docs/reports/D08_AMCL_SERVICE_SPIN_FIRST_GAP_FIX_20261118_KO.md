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

## 2026-11-18 실행 완료 결과 — 정확한 RED / GREEN / REFACTOR / REVIEW / COMMIT

- **RED 소스 SHA** `32ffd740f3d26c8f85f616b24c99002bf3615a10`, [Public CI #44305843798](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44305843798): `ImportError: cannot import name 'spin_until_initial_pose_service_ready' from d08_amcl_initial_pose`; 새 테스트 수집 실패, 나머지 실제 Gazebo job SKIPPED. 원본 Owner Scan 2.065084s/Odom 1.952984s gap 진단은 보존.
- **GREEN 코드 SHA** `62d7e94abe2828792be32231e5ab79cdc6620f5f`, [Public CI #44306208316](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44306208316): 전체 워크플로 **SUCCESS**, L0 `123 passed in 0.53s`, Gazebo 센서/Waffle L2 PASS, **실제 Gazebo+공식 AMCL/TF/Path+8-cycle NO_GOAL L2 PASS**, 같은 World 원본 C++ YOLO/실제 Depth 2 VALID+UNKNOWN 통합 job SUCCESS. 4개 jobs 모두 success.
- 실제 ROS service readiness 판정만 CI에서 **2.0초 holdoff**(native server가 2초 unavailable이었다는 주장이 아님). 같은 관측 노드에서 `rclpy.spin_once` 반복 처리:
```text
D08_AMCL_SERVICE_DISCOVERY_RX_SPIN {
  "ready": true,
  "service_wait_wall_sec": 2.003438,
  "ci_holdoff_sec": 2.0,
  "spin_calls": 1433,
  "callback_samples_during_wait": {"scan": 19, "odom": 55, "clock": 91},
  "max_host_callback_gap_during_service_wait_sec": {
    "scan": 0.139834, "odom": 0.044505, "clock": 0.027300
  },
  "first_receive_gaps_during_wait": {"scan": null, "odom": null},
  "publisher_rmw_gap_measured": false
}
D08_REAL_AMCL_SERVICE_DISCOVERY_SPIN_SCAN_ODOM_CLOCK_L2_PASS
D08_REAL_SCAN_ODOM_CLOCK_HOST_VS_SIM_STAMP_TIMING_L2_PASS
D08_CI_REAL_GUI_EIGHT_REPEAT_PATHS_L2_PASS
D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL
```
- 실제 Localization/TF `D08_AMCL_REAL_FIRST_POSE_PLUS_LIVE_TF_READY`: AMCL source stamp **11.202s**, map→base_link TF source stamp **12.888s**, Scan 최신 host receive age **0.000078s**, Odom **0.019720s**. 기존 ROS header stamp delta 최대값은 `amcl_receive_timing.json`의 `scan/odom/clock.max_source_stamp_delta_sec`로 실제 원본 보존되며, 진단값을 Gazebo publisher나 CM RMW 내부 간격이라고 오인하지 않음.
- 같은 L2 공식 Path의 before/intrusion/restored 변화 확인, 그 중 최초 주기 Costmap lethal **0→66→0** 및 실제 Scan 최소거리 **1.8810→0.5672→1.8878m**. 이 Path는 주행 명령 아님.
- **실제 공개 아티팩트**: `d08-official-nav2-oneworld-l2-evidence` #14429360127, `d08-main-real-no-goal-evidence` #14427693244, `d08-same-world-live-person-range-cm-nav2-evidence` #14427584985, `d08-ui9-public-yolo-ros-replay-l1` #14428542454 (GitHub Actions 보관 7일).
- **검증 범위 REVIEW**: `d08_amcl_initial_pose.py` 1개 실제 실행 파일만 수정. 서비스 준비 `client.service_is_ready()`와 `rclpy.spin_once(node,timeout_sec<=.05)` 사용, `SetInitialPose` 1회·기존 첫 gap 및 500ms Scan/Odom age 기준 유지. L2의 테스트용 0.65s 일시적 subscriber pause와 NO_GOAL 실측 회복 로직은 기존대로 유지하며 새로운 fake 안전 성공을 표시하지 않음. 새 `max_source_stamp_delta_sec`는 계측용; `publisher_rmw_cadence_measured=false` 유지.
- 실제 Owner WSL2/WSLg Intel D3D12에서 원래 2.065초 공백이 재현되지 않는다는 증거는 **없음**. CPU/GPU/WSLg에서 생기는 독립적인 publisher/TF/DDS 지연 원인은 미검증. 기존 G07 CM 내부 주기·Guard TTL·주행 감속·정지 역시 별도 HOLD. **전체 L3 안정성 PASS 아님**.
- **COMMIT**: `32ffd740f3d26c8f85f616b24c99002bf3615a10`(RED), `62d7e94abe2828792be32231e5ab79cdc6620f5f`(GREEN), 본 보고서 후속 커밋은 문서 전용이며 실증 소스 SHA는 `62d7e94abe2828792be32231e5ab79cdc6620f5f`.
- CI 실행 명령: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q d08/tests/test_d08_amcl_service_discovery_starvation.py d08/tests/test_d08_owner_first_scan_odom_gap_regression.py d08/tests/test_d08_static_amcl_witness.py`. 실제 Gazebo L2는 `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`의 고정 official Nav2 job 사용.
- **RELEASE 판정**: `D08_AMCL_SERVICE_DISCOVERY_CALLBACK_L2=PASS`, `D08_OWNER_WSLG_FIRST_GAP_RETEST=NOT_RUN`, `D08_LIVE_NO_GOAL_ACCEPTED=HOLD_OWNER_L3`, `D08_MOVING_E2E_ACCEPTED=HOLD`, 모든 main 병합 NO. 사용자 요청 범위 외 기존 성공 시험·모델/World/Renderer 재설계 없음.
