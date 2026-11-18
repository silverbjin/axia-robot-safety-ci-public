# AXIA D08 — 최초 Scan 518.394ms 원인 계층 분리: Gazebo 원천 Transport 수신 계측 RED→GREEN 보고서

> 2026-11-19 KST · 교육/인수 증거 문서 · **결론은 근본 원인 UNDETERMINED, Owner L3 HOLD**

## 1. 목적과 기존 성공 증거

- 개발 기준: 공개 `silverbjin/axia-robot-safety-ci-public` [PR #180](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/180) (Draft), 브랜치 `fix/d08-native-scan-first-gap-20261119`.
- 기준 NO_GOAL Scan 원인계측 GREEN SHA `82bef69aa6c6fa7e7b73ec9708d3ab507309ec3d`, 공개 [Run #44342077721](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44342077721): L0 136 PASS + 공식 Gazebo 8-cycle L2 PASS. **본 작업에서 수정하지 않음**.
- 이전 AMCL 서비스 탐색 정체 수정 SHA `62d7e94abe2828792be32231e5ab79cdc6620f5f`, 실제 L2 [Run #44306208316](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44306208316). 변경 후에도 `d08/harness/d08_amcl_initial_pose.py` Git blob `f44ffe3aa67bbbde03a28319d0db3587742b6f52` 동일.
- 현장 ZIP `run_20261118T143911Z_VG0B5q.diagnostics.zip`: SHA256 `d5eafa80295d89d4713da7532b651e9b8ff5f64c49285025586891bc49cdb2eb`, 내부 26/26 SHA256 일치. 원본 ZIP은 Git에 게시하지 않음.
- Owner 첫 안전 타이밍 위반: `D08_FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS` **0.518394s** (index 2), Scan 원본 ROS stamp 48.501s→48.600s(0.099s), 호스트 수신 1550.021209→1550.539602초.
- 독립 공개 CI 실제 재현: [Run #44312306299](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44312306299), 공식 Gazebo 반복 경로 `0.505365s` first Scan Rx gap; 원인계층 미계측. WSL2 고유 원인으로 단정 불가.

기존 `evaluate_three_phases`의 500ms FAIL-CLOSED는 정상 동작. 뒤늦은 메시지 회복, 공식 Path 생성 또는 새 테스트 PASS로 과거 첫 위반 이력을 지우지 않음. 이 보고서는 **새 주행/센서/안전 알고리즘 구현이 아닌 원인 계층 최소 계측**만 기록한다.

## 2. 공식 근거 및 단일 원인 분리 가설

Gazebo Harmonic 문서에 따르면 LiDAR `<update_rate>`는 **시뮬레이션 시간 기준**이며, ROS 2 Jazzy는 `ros_gz_bridge`를 통해 Gazebo native LaserScan을 ROS `/scan`으로 연결한다.

- [Gazebo Harmonic sensors](https://gazebosim.org/docs/harmonic/sensors/)
- [Gazebo Transport 13 Python subscriber](https://gazebosim.org/api/transport/13/python.html)
- [Gazebo Harmonic OSRF Noble signed Apt repository](https://gazebosim.org/docs/harmonic/install_ubuntu/)
- [ROS Jazzy/Nav2 Gazebo sensor bridge](https://docs.nav2.org/jazzy/configuration_and_development/first_time_robot_setup_guide/sensors/setup_sensors_gz/)

기존 D08 생성 SDF의 GPU LiDAR는 10Hz **SIM**이다. 예전 실패의 0.099s sim stamp 진행과 0.518394s ROS Observer host receive 간격만으로 원천 발행 느림, 브리지/RMW 지연, Observer callback 정체 중 하나를 원인으로 지정할 수 없다. `0.099/0.518394≈0.191`은 *두 Scan sample의 stamp 진행 대비 ROS callback host 구간의 비율*일 뿐, 동시간 Gazebo `/clock`/native publisher 측정으로 검증된 RTF는 아니다.

단일 계측 가설: 원래 ROS Scan 수신 경계가 >0.5s일 때, 동일 원본 timestamp 쌍에 대해 **별도 프로세스의 Gazebo Transport read-only /scan 구독 시각**을 함께 수집하면 at/before native transport와 after native transport 간 지연 후보를 좁힐 수 있다. Gazebo Transport 구독 수신 시각은 실제 Gazebo sensor 내부 publish 시각이나 Bridge/DDS 송신 시각과 **다르다**. 그러므로 원인 `cause=UNDETERMINED` 유지, candidate만 표시한다.

## 3. RED→GREEN→REFACTOR→REVIEW→COMMIT

### Cycle A — 원천-ROS first-gap timestamp 대조

- **RED** `d08/tests/test_d08_native_gazebo_scan_causal_trace.py` 추가 및 원천 probe 부재/함수 부재 계약. [Public Run #44349218405](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44349218405), 최초 L0 수집 오류:

```text
ImportError: cannot import name 'compare_native_scan_first_gap'
from 'd08_scan_gap_trace'
ERROR d08/tests/test_d08_native_gazebo_scan_causal_trace.py
```

- **GREEN** `d08/harness/d08_gz_native_scan_probe.py` (신규): 공식 `gz.transport13.Node.subscribe(gz.msgs10.LaserScan, '/scan', ...)`; 분리된 Python 프로세스에서 `time.monotonic()`·native `header.stamp`만 JSONL에 제한(1 cycle 최대 1,024개), CLI 및 Publish 없음.
- `d08/harness/d08_scan_gap_trace.py`: `compare_native_scan_first_gap()`를 추가하여 이전/현재 ROS LaserScan stamp 두 개와 native subscriber stamp를 정확히 매칭. first-gap 없으면 NO_ROS_FIRST_GAP, native pair 없으면 NATIVE_SOURCE_STAMP_PAIR_UNAVAILABLE, 일치하면 `AT_OR_BEFORE_NATIVE_TRANSPORT_RX` 또는 `AFTER_NATIVE_TRANSPORT_RX` **candidate**. 모든 경우 `cause=UNDETERMINED`, `publisher_send_timing_proven=false`, `bridge_dds_send_measured=false`.
- `d08/harness/d08_same_world_replan.py`: 환경 플래그 `AXIA_D08_NATIVE_RX_PROBE=1`인 **공개 CI**에서만 원천 독립 프로브 프로세스를 실행하고 첫 Scan 공백 및 모든 native sample 통계 보존. 임의 publish, Goal, cmd_vel 추가 없음. 미수집/버퍼 포화는 HOLD.
- 최초 GREEN CI [#44349748962](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44349748962): `141 passed in 0.73s`. 실제 L2는 Python gz transport apt 패키지 미발견으로 **Gazebo 실행 전 BLOCKED**: `Unable to locate package python3-gz-transport13`, `python3-gz-msgs10`, rc 100. 이 오류를 Scan 원인/ROS L2 FAIL로 승격하지 않음.

### Cycle B — 공식 Gazebo Python 패키지 소스 누락

- **RED** `d08/tests/test_d08_native_probe_apt_contract.py`: signed OSRF Apt 출처 및 ROS/Gazebo 라이브러리 no-upgrade 계약. [Public Run #44350696018](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44350696018) 실제 출력 `2 failed, 141 passed in 0.88s`. 누락 `packages.osrfoundation.org/gazebo.gpg`, `--no-upgrade`.
- **GREEN** 변경은 CI 전용 `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml` 한 곳: 공식 Gazebo Harmonic signed Noble repository에서 **두 Python binding 패키지만** `apt-get install -y -qq --no-install-recommends --no-upgrade`로 설치. `gz-harmonic` 메타패키지 설치/Owner PC 시스템 변경 없음.
- **GREEN SHA** `fc81b1890e6e680431376b06e9dc32b7bba06f0e`, [Public Run #44350898702](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44350898702): **L0 `143 passed in 0.94s`, official Gazebo+Nav2 L2 SUCCESS**. 다른 Contact/YOLO Job들은 의도적으로 `SKIPPED`; 전체 통합 4/4 PASS 아님.

### 실제 검증 명령

L0의 정확한 실행은 workflow 내 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q` (기존 테스트 목록 + `test_d08_native_gazebo_scan_causal_trace.py` + `test_d08_native_probe_apt_contract.py`). 네이티브 사전검사 `/usr/bin/python3 -c 'from gz.transport13 import Node; from gz.msgs10.laserscan_pb2 import LaserScan; ...'`. 실제 L2는 ROS Jazzy/Gazebo Harmonic Docker Job에서

```bash
xvfb-run -a -s '-screen 0 1280x720x24' \
  python3 -u d08/scripts/d08_public_gazebo_l2.py \
  --actor /tmp/axia-d08-nav2-assets/walk.dae \
  --out results/d08-official-nav2-sameworld \
  --official-nav2 --official-path-phases --ci-owner-repro
```

with `AXIA_D08_NATIVE_RX_PROBE=1`, `AXIA_D08_EXACT_SOURCE_SHA=fc81b1890e6e680431376b06e9dc32b7bba06f0e` and ROS env from workflow.

## 4. 증거 아티팩트 및 실제 8-cycle 통계

- [Actual L2 Evidence artifact #14447029830](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44350898702/artifacts/14447029830), ZIP SHA256 `b386f8a398a13cf541b2139a79f9dac468cda2231ece1a57e575dc02d51fb4c3`, ZIP CRC PASS, 86개 항목.
- `official_path_phases` 1회 + `ci_owner_replan_cycles/cycle_0000~cycle_0007` 8회 모두 `D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL` 및 `first_scan_timing_boundary=null`.
- 8회 원천 Gazebo Transport Scan 구독 sample_count: `65,58,51,66,58,67,52,48`; 모두 최소 8개 통과, 1,024개 상한 미도달. 원천 Scan **최대 host receive gap = 0.241989s**.
- 같은 8회 독립 ROS 수신 최대 gap: `/scan=0.429612s`, `/odom=0.357614s`, `/clock=0.337267s`, `/tf=0.409458s`. 모든 독립 Scan/Odom/Clock 관측 interval은 500ms 이하. `/tf` gap 자체를 별도 TF freshness/안전 TTL PASS로 오인하지 않음.
- 공식 실행 Job 로그:

```text
D08_NATIVE_PYTHON_APT_IMPORT_L2_PASS
D08_NATIVE_GZ_SCAN_RX_WITNESS {"sample_count": 57, "max_host_receive_gap_sec": 0.229633, "history_complete": true, "first_violation_cause": "UNDETERMINED"}
D08_NATIVE_GZ_SCAN_RX_WITNESS {"sample_count": 65, "max_host_receive_gap_sec": 0.236332, "history_complete": true, "first_violation_cause": "UNDETERMINED"}
D08_CI_REAL_GUI_EIGHT_REPEAT_PATHS_L2_PASS
D08_REAL_SAME_RUN_EIGHT_CYCLES_SCAN_ODOM_CLOCK_CADENCE_L2_PASS_NOT_CM
D08_REAL_AMCL_SERVICE_DISCOVERY_SPIN_SCAN_ODOM_CLOCK_L2_PASS
D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL
```

- 이번 성공 실행에는 최초 ROS >500ms gap이 **없었으므로**, native/ROS 첫 위반 source-stamp pair crosscheck는 `candidate=NO_ROS_FIRST_GAP`, `native_pair_matched=false`, `cause=UNDETERMINED`가 **정확한 기대값**. 새로운 native receiver가 실제 독립 메시지 수신에 성공했다는 사실이 과거 Owner/CI 첫 위반의 native timestamp 증거로 소급되지는 않는다.

## 5. 리뷰 / 미검증 / 릴리스 기준

본 변경의 파일 범위는 아래 **6개**뿐임:
1. `d08/harness/d08_gz_native_scan_probe.py` (신규, read-only)
2. `d08/harness/d08_scan_gap_trace.py` (pure 비교, 이전 첫 위반 보존)
3. `d08/harness/d08_same_world_replan.py` (CI-only 원천 계측 프로세스)
4. `d08/tests/test_d08_native_gazebo_scan_causal_trace.py` (RED→GREEN)
5. `d08/tests/test_d08_native_probe_apt_contract.py` (Apt RED→GREEN)
6. `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml` (L0 + 좁힌 L2 진단)

이 검증에서 확인한 것은 **원천 수신 계측기와 기존 NO_GOAL 8사이클이 동일 CI에서 실제로 실행됨**이다. 과거 518.394ms 실패 시 원천 Gazebo 구독자가 없었으므로 최초 실패의 실제 경계가 Gazebo native인지 Bridge/Executor인지 **여전히 미확정**. 최초 505.365ms CI 실패도 동일. 새로운 시험에서 간헐적 실패를 재현하지 못했다고 '해결' 선언 금지. WSLg 실제 pixel/Owner L3 미실행; 로봇 주행 Goal/Velocity 없음; CM native lifecycle active 및 configured Scan은 기존 범위일 뿐 CM 내부 RX, Guard 120/150ms, 실제 STOP/SLOW, 인증된 E-Stop은 미검증. 위원회/사용자 승인 없는 main 병합 없음.

```text
D08_FIRST_SCAN_GAP_REGRESSION_L0=PASS
D08_NATIVE_GZ_SCAN_RX_PROBE_L2=PASS
D08_OFFICIAL_NO_GOAL_EIGHT_CYCLE_L2=PASS
D08_FIRST_SCAN_GAP_CAUSE=UNDETERMINED
D08_FIRST_SCAN_GAP_FIELD_FIXED=NOT_VERIFIED
D08_G07_MOVING_E2E=HOLD
D08_CM_INTERNAL_RX=NOT_VERIFIED
D08_GUARD_TTL=NOT_VERIFIED
D08_OWNER_WSL2_L3=NOT_RUN
D08_MAIN_MERGED=NO
D08_LIVE_NO_GOAL_ACCEPTED=HOLD_OWNER_L3
```

**학습 포인트:** 테스트 실패를 ① 최초 실제 Scan 500ms 위반, ② 계측 코드 부재, ③ OSRF Apt 소스 부재, ④ 실제 Gazebo/ROS 통합 성공으로 나눠야 하며, 이 네 가지를 하나의 '성공/실패'로 합산하면 원인 분석과 출고 판정이 훼손된다.

**브랜치/커밋:** 원인계측 개발 `fix/d08-native-scan-first-gap-20261119` SHA `fc81b1890e6e680431376b06e9dc32b7bba06f0e`; 교육용 문서 분리 `docs/d08-native-scan-first-gap-20261119` (본 보고서 커밋); main NO MERGE.
