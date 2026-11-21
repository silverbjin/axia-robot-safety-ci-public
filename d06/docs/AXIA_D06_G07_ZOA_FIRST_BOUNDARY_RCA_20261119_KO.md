# AXIA D06/G07 — ZOAgryLW 첫 실패 경계 재분석 및 공개 CI 회귀 보고서

- 기준: Owner WSL2 Ubuntu24.04 + ROS2 Jazzy + Gazebo Harmonic + NVIDIA D3D12, NO_GOAL.
- 원본: `d06-forensic-ab-no-goal-ZOAgryLW.tar.gz`, SHA256 `5fe3f39b02cda4a7255a0e733a425efb0a9880fddb89285c8c85fcef72618a03` (제출 sidecar와 직접 일치).
- 공개 PR: [#177](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/177); Gazebo -11 추적 [Issue #186](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/186). 강사 WSL2 원본·기존 승인 증거 보존.
- 기준 보존: 공식 TB3 Waffle/Nav2 코드, ScanTTL300ms, CM120ms, Guard150ms, NO_GOAL 유지. SW stop != certified E-Stop.

## 1. 확인된 사실과 미확정 원인

- 원본 `summary.json`: `sensor_status=NO_GOAL_SENSOR_UNSAFE_HOLD`, Safety CLEAR157/157, 전방 median 1.414382m / 측면 median2.520205m. Raw 최대 wall receipt gap0.452540s, Safety 최대0.458803s **300ms 위반**, Raw158·Safety157, ROS Clock RTF 전체0.782939. Sim source rate 10.0Hz, Safety wall rate7.849970Hz.
- `native_startup_verdict.json`: official Nav2 `NAV2_ACTION_READY` host monotonic **5131.995s**; 동일 시스템 clock evidence.
- D08 재사용 `d06_gz_scan_receipts.jsonl` 753개, 독립 ROS `d06_ros_scan_receipts.jsonl` Raw753개·Safety753개, native Clock `d06_gz_clock_receipts.jsonl` 2041개. 단순 summary가 아니라 원본 짝지은 source stamp와 host monotonic을 검산함.

### 최초 전체 세션 위반: ROS Safety observer 수신 지연

- Sim stamp16.701→16.800s, native host5096.465309→5096.561699 = **96.390ms**. ROS raw5096.465282→5096.562073 = **96.791ms**. ROS safety5096.466308→5096.845806 = **379.498ms**.
- native Clock 같은 국소 구간 RTF≈1.0. Safety observer의 두 번째 메시지 수신은 native보다 **284.107ms 늦음**. 뒤이은 sim stamp16.902,17.001이 5096.846초 부근에서 연속 처리됨.
- **5096.845806s < Nav2 READY5131.995s**: 본 계측은 프로세스 생성 시점부터 시작하므로 전체 세션 최초 위반은 본래 **학생용 NO_GOAL 20초 안전 검증 창보다 전**의 이벤트. 기존 `candidate=AFTER_NATIVE_TRANSPORT_RX`만으로 실제 Student 센서 안전 위반의 첫 원인을 설명하면 **범위 오진**.
- 콜백 수신 지연/큐 누적 관측이지 Gazebo 내부 publish 지연은 아님. ROS DDS vs rclpy executor vs OS scheduling의 정밀한 점유 시간은 미측정.

### Nav2 준비 뒤 20초 대리 창(PROXY) 최초 Scan 위반: Gazebo native 지연

- `NAV2_ACTION_READY` host5131.995s를 기준으로 +20초 **대리 관측 창** 설정(학생 probe 정확한 첫 receipt timestamp는 원본에 없음).
- Sim stamp47.901→48.000s, native host5132.355288→5132.729528 = **374.240ms**. ROS raw5132.372511→5132.729658 = **357.147ms**. ROS safety5132.372821→5132.737526 = **364.705ms**.
- Native Clock 인접 표본: sim47.919s / host5132.338515s → sim48.048s / host5132.727740s, 즉 0.129s sim /0.389225s wall = **RTF≈0.3314**. 온전히 정지한 것이 아니라 순간적인 시뮬레이션 진행률 감소.
- 이 *별도의* 구간은 **Gazebo Transport native 수신 단계에서 이미 Scan300ms FAIL**. ROS QoS/forwarder만 수정하거나 TTL을 늘리는 조치는 원인을 해결하지 못함.
- 단, 이 20초는 실제 Student probe의 timestamp pair와 직접 정합된 창이 아니므로 `POST_NAV2_READY_PROXY`, `student_probe_same_pair_proven=false`, `cause=UNDETERMINED`으로 표시. 학생 probe의 max0.45s와 witness proxy max0.37s를 직접 동일 메시지 문제로 혼동 금지.

### 종료는 세 번째 독립 실패: Gazebo SERVER SIGSEGV

- Original `native_nav2_ordered_shutdown.json`: Navigation shutdown ACK=true, Localization ACK=true, CM is Nav2 managed. Original `native_cm_shutdown_audit.json`: **Collision Monitor exit0**, clean candidate.
- Original `shutdown_context.txt` line472 **collision_monitor process finished cleanly**; line480 **`gz sim -r -s /tmp/nav2_5wtxcwad.sdf` exit code -11**. `P2_L2_GRACEFUL_TEARDOWN` marker does NOT prove Gazebo server cleanly terminated. 이번 회차에는 CM segfault가 재현된 것이 아니다.
- Original `first_stop_and_timing.txt` line324 `HEALTH_BAD_DIAGNOSTIC`은 **Nav2 manager가 이미 deactivating 중인 상태**의 `cm_active=false`/ `scan_age_sec=0.0023`/ `scan_ok=true`. 이를 센서 첫 timeout 또는 예상치 못한 첫 안전 STOP으로 해석 금지.
- Gazebo server stack/backtrace가 없으므로 shutdown SIGSEGV의 정확한 원인(서버 렌더러 정리, Sensor system teardown, WSLg, 라이브러리 등) **미확정**. Client Ogre2 GL_RENDERER NVIDIA D3D12는 실제 기록되지만 GPU causality 증거는 아님.

## 2. 개발·회귀 범위 (RED→GREEN→REFACTOR→REVIEW→COMMIT)

- 재현 fixture: `d06/fixtures/g07_zoa_first_boundary_20261119.json` (해당 원본의 exact source stamp, native/ROS callback host timestamp, native Clock, READY 5131.995, CM0/Gazebo-11을 최소화하여 등록).
- 테스트: `d06/tests/test_d06_g07_zoa_scope_regression.py`에서 전 세션 첫 ROS callback gap vs 준비 뒤 native slowdown, Clock 국소 진전, Gazebo 서버 -11 fail-closed, 원샷 CLI 두 scope를 분리해 검증.
- 공개 CI RED [#44450692005](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44450692005): 이전 코드 `classify(after_host_sec=)` 미구현, `--startup-verdict` CLI 누락 등 신규 2건 예상 실패.
- 첫 GREEN 후보에서 fixture 개행이 실제 JSONL LF가 아닌 리터럴이었던 오류 [#44451067446](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44451067446)를 발견해 수정.
- 다음 후보에서 fixture의 `NAV2_ACTION_READY` stage PASS 누락으로 proxy가 NOT_VERIFIED 됨 [#44451196245](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44451196245); 실제 startup JSON과 같은 PASS 단계로 정정.
- GREEN [#44451307908](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44451307908) 및 [canary](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44451307968) SUCCESS. 실제 ROS/Gazebo를 다시 시작하지 않고 오프라인 fixture로 검증한 L0.
- `d06/tools/d06_g07_scan_rx_witness.py`는 안전 검증을 수행하지 않는 **read-only 계측기**: `WHOLE_SESSION_FIRST_BREACH` 및 `POST_NAV2_READY_PROXY`를 각각 표시하고, Student message pair 직접 대응이 없음을 명시.
- `d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh`는 기존 startup_verdict를 **같은 실행의 기존 분석**에 전달. `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`의 경량 TAR는 두 scope를 독립 요약. 이 수정은 새 현장 재시도를 요구하지 않음.

## 3. 다음 해결 경계 및 인수

- ROS 수신 콜백만 늦는 구간: 첫 host callback 수신 경계, DDS queue vs rclpy spin/executor 및 WSL2 scheduler 각각을 계측. 전 세션 최초만 실제 학생의 첫 위반 원인으로 사용 금지.
- Gazebo native 자체가 늦는 구간: native Clock local RTF, Ogre2 GPU LiDAR / Sim server CPU/GPU load, physics/sensor update rate의 같은 시각 간격 검사. 현재 RTF0.331의 기여는 검증되나 최초 자원 원인은 미검증.
- Gazebo 서버 SIGSEGV: 동일 공식 월드/WSLg NVIDIA 세션의 **core 또는 최초 예외 백트레이스**가 필요. 실제 CM exit0 성공 증거 보존. WSLg 현장 동일 시도만 반복하지 말고 공개 CI에서 재현 가능한 구성부터 분리한다.
- 상태: **Scan300ms FAIL, Gazebo server native exit-11 FAIL, CM Nav2 shutdown/child exit0 PASS**. CM120ms·Guard150ms와 Moving Goal L3 **미검증**. `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `D06_GAZEBO_LIVE_RELEASE=HOLD`, `CERTIFIED_ESTOP=false`, main 미병합.

공식 참고: [ROS2 Executors](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Executors.html), [Gazebo Harmonic Troubleshooting](https://gazebosim.org/docs/harmonic/troubleshooting/), [Gazebo Harmonic Sensors](https://gazebosim.org/docs/harmonic/sensors/).
