# AXIA D08 — 최초 Scan 518.394ms 진단·공개 CI RED→GREEN 교육용 보고서 (2026-11-19 KST)

## 0. 대상과 증거 보존

- 공개 저장소: `silverbjin/axia-robot-safety-ci-public`; 개발 Draft PR [#179](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/179); 개발 브랜치 `fix/d08-first-scan-gap-boundary-20261119`.
- 원본 Owner 진단 `run_20261118T143911Z_VG0B5q.diagnostics.zip`: ZIP SHA256 `d5eafa80295d89d4713da7532b651e9b8ff5f64c49285025586891bc49cdb2eb`; CRC PASS; 내부 SHA256 26/26 PASS. ZIP 자체와 사용자 전용 파일 경로는 공개 커밋하지 않음.
- Owner 소스 SHA `342c6355b27af5b8b11a79b7e345820be18a581f`; 최초 `cycle_0000` **HOLD**: Scan Observer host receive 0.518394s (index 2), host monotonic 1550.021209→1550.539602, ROS header stamp 48.501→48.600s (sim delta 0.099s). RMW/native Gazebo publisher와 같은 monotonic 기준의 송신 수신 타임라인은 **없음**.
- 독립 실제 공개 CI RED: [#44312306299](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44312306299), SHA `58c085cc7766d6bbc82b28a3f60ce50f70245c46`, 공식 Nav2/Gazebo 반복 cycle_0000 Scan **0.505365s** (index 8), header stamp 0.102s 진행. 위반 직후 수신 간격 2.326/1.672/1.515ms의 몰림을 검출. 원본 증거 아티팩트 #14430518299. 해당 실행에서 정리된 Gazebo/ROS process exit=0; 최초 500ms 위반 때문에 전체 verdict BLOCKED임.
- 기존 AMCL 서비스 발견 callback 정체 수정 SHA `62d7e94abe2828792be32231e5ab79cdc6620f5f`, Git blob `f44ffe3aa67bbbde03a28319d0db3587742b6f52` 불변; 기존 GREEN [#44306208316](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44306208316) 보존.

## 1. 최초 실패 경계와 원인 가설

첫 실패는 실제 Scan 콜백의 host 수신 간격 500ms 초과다. 첫 3상 Path/YOLO/AMCL 성공 또는 뒤늦은 메시지 몰림으로 **소급 PASS할 수 없다**. 기존 `d08_same_world_replan.py`의 `evaluate_three_phases`가 최초 위반을 예외로 중단한 동작은 정확한 FAIL-CLOSED였다.

하나의 가설: 원래 Scan 콜백의 host 수신 공백은 Observer callback 실행/락, ros_gz_bridge/DDS 전달 또는 Gazebo 센서 발행·호스트 스케줄링 중 적어도 한 경계에서 발생했을 수 있다. `LaserScan.header.stamp`의 0.099~0.102s 진전만으로 source/RMW/Observer 중 하나를 확정하면 안 된다.

공식 참조: [ROS 2 Jazzy Executors](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Executors.html), [Nav2 Gazebo 센서 브리지](https://docs.nav2.org/jazzy/configuration_and_development/first_time_robot_setup_guide/sensors/setup_sensors_gz/), [Gazebo Harmonic sensors](https://gazebosim.org/docs/harmonic/sensors/).

## 2. RED → GREEN → REFACTOR → REVIEW → COMMIT

1. 원본 518.394ms fixture와 정상 비교 438.203ms를 `d08/tests/test_d08_field_first_518ms_receive_boundary.py`에 최소 정착. 이미 올바른 500ms FAIL-CLOSED 로직을 변경하지 않음. TDD RED commit `daece3ae8ac91e02bdccafe187308844dba96e7e` (원인 classifier 부재), 대상 속성 추가 `05240684689ff3531702ed1a64b3d5a1e712522c`.
2. `d08/harness/d08_scan_gap_trace.py`에 첫 위반을 유지하면서 독립 ROS receiver와 original Observer의 같은 host monotonic 수신 구간을 보수적으로 비교하는 `diagnose_first_receive_boundary` 추가. 근본 원인은 **항상 UNDETERMINED**로 보존하고 `OBSERVER_DISPATCH_OR_QOS`, `OBSERVER_PROCESSING_OR_LOCK`, `SHARED_ROS_RECEIVE_DELAY`는 candidate로만 표시. Gazebo native/Bridge send/DDS 내부 타이밍은 측정했다고 주장하지 않음.
3. `d08/harness/d08_same_world_replan.py`에 독립 O(1) read-only Scan/Odom/Clock/TF callback + 별도 Executor thread 추가. 원래 Observer `at` 시각은 유지하고 `entry_at`과 callback 처리 지속시간을 별도 계측. 추가 기능은 원래 ROS 토픽 데이터 관찰자뿐이며 publish/Goal/Velocity 없음. 최초 코드 커밋 `ac249efeb85de2c4f4b1404c5e3f4fd9b41ff8cd`.
4. L0 134 PASS + 실제 CI [#44339328168](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44339328168): 첫 L2 attempt은 **Planner unavailable**로 Path 이전 BLOCKED, 동일 공식 L2 실패 Job 1회 재검으로 실제 Gazebo 8-cycle PASS (아티팩트 #14443053396). 그러나 원래 `/clock` maxlen=512로 250Hz 약 9초 첫 구간이 삭제될 수 있음을 아티팩트 분석으로 발견.
5. **독립 계측 데이터 custody RED**: `d08/tests/test_d08_independent_clock_evidence_history.py` 2개 테스트. 실제 공개 CI [#44341827259](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44341827259) `ImportError: cannot import name 'new_independent_rx_buffers'`, exit code 2, L2 SKIPPED.
6. **GREEN**: `new_independent_rx_buffers`를 통해 최대 4096개 시각 샘플 보존 (bounded). `history_complete`가 거짓이면 8-cycle Clock/Odom/Scan gate가 PASS하지 못하도록 기존 L2 테스트에 추가. 커밋 `eb6b178724f7b082cd33dbd3815213771da151f5` → 검증 SHA `82bef69aa6c6fa7e7b73ec9708d3ab507309ec3d`.
7. 공개 CI [#44342077721](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44342077721) 실제 checkout `82bef69aa6c6fa7e7b73ec9708d3ab507309ec3d`: L0 **136 passed in 0.55s**, official Gazebo+Nav2 **L2 SUCCESS**, 8/8 real same-world NO_GOAL cycles PASS. 이 진단 브랜치에서는 무관한 Contact/YOLO 두 Job은 의도적으로 SKIPPED였고, 이 결과를 전체 통합 Job 4/4 PASS로 보고하지 않음.

실제 실행한 CI L0 명령은 `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`의 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q ...` (새 field/Clock retention 테스트 포함)이며, L2 실행은 공식 `gazebo-official-nav2-oneworld` Job의 원래 `--official-nav2 --official-path-phases --ci-owner-repro`이다. 변경 파일은 `d08/harness/d08_scan_gap_trace.py`, `d08/harness/d08_same_world_replan.py`, 위 두 테스트, L0·L2 공개 workflow로 제한.

## 3. 실제 GREEN L2 증거, 단 안전 인증은 아님

- 필수 실제 출력:

```text
136 passed in 0.55s
D08_PUBLIC_MAIN_NO_GOAL_L0_PASS
D08_CI_REAL_GUI_EIGHT_REPEAT_PATHS_L2_PASS
D08_REAL_SAME_RUN_EIGHT_CYCLES_SCAN_ODOM_CLOCK_CADENCE_L2_PASS_NOT_CM
D08_REAL_AMCL_SERVICE_DISCOVERY_SPIN_SCAN_ODOM_CLOCK_L2_PASS
D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL
```

- 아티팩트 #14444841669, ZIP SHA256 `dbc9c149f5b5021eecb7986afc0904d92150d45889225eb7de5126c4b6c45f91`, source provenance `82bef69aa6c6fa7e7b73ec9708d3ab507309ec3d`.
- 실제 8개 `ci_owner_replan_cycles/cycle_0000~cycle_0007/verdict.json` 모두 3상 공식 경로 및 fail-closed Scan gap 체크 PASS. 독립 receive Scan 최대 gap **0.239692s**, Odom **0.140963s**, Clock **0.107197s**; 500ms 초과 0건. Clock 각 cycle **1772~2475**개 callback 보존, 모든 cycle `history_complete=true`; 기존 512개에서 삭제되던 초기 구간 유지.
- 실제 별도 `/tf` topic max host receive gap **0.692512s** (cycle_0001) 관측. 이는 TF 안전 freshness TTL 위반이라고 독자적으로 단정할 수 없으나, TF와 다른 안전 계층까지 모두 안정적으로 검증됐다는 주장은 불가. Map→base_link 실제 TF lookup과 Topic 수신 주기는 별도 증거.
- 정상적인 이번 L2에 한해 Observer Scan sector 콜백의 entry→record 최대 지속시간은 **0.002027s**. 과거 FAIL 시점의 CPU 처리 시간과 Gazebo native publisher 주기까지 증명하지는 못했다.
- CM native `active`/Scan source 설정은 검증됐으나 **CM 내부 데이터 수신 간격, Guard TTL, 실제 정지/감속, 인증된 E-Stop은 전혀 이 테스트 결과로 증명되지 않는다**.

## 4. 최종 검증·미검증·브랜치/릴리스 판정

```text
D08_FIRST_SCAN_GAP_REGRESSION_L0=PASS
D08_FIRST_SCAN_GAP_CAUSE=UNDETERMINED
D08_FIRST_SCAN_GAP_PUBLIC_REAL_L2=PASS
D08_SAME_RUN_CLOCK_SCAN_ODOM_TF_TIMING=NOT_VERIFIED
D08_OFFICIAL_CM_INTERNAL_RX=NOT_VERIFIED
D08_G07_MOVING_E2E=HOLD
D08_OWNER_WSL2_L3=NOT_RUN
D08_LIVE_NO_GOAL_ACCEPTED=HOLD_OWNER_L3
D08_MAIN_MERGED=NO
```

CI L2 PASS는 `82bef69...`의 **NO_GOAL 실제 Gazebo 8-cycle 기능·Scan/Odom/Clock 수신 간격**에 관한 것이며, 현장의 간헐적 518.394ms 원인 해결을 증명하지 않는다. WSL2 Owner 재실행, 새로운 Goal/Twist, 센서/CM/Guard TTL 조정, 공식 Nav2 포크, main 병합은 진행하지 않았다.

추가 Owner 원샷을 출고 승인하기 전에 원본 실패와 동시의 native Gazebo LiDAR 발행 또는 ros_gz_bridge/DDS send gap을 실제로 분리하여 cause를 확정해야 한다. 첫 안전 전이·타이밍 위반만 기록하는 bounded trace를 사용하고 같은 현장 테스트 반복 대신 공개 CI의 해당 경계 회귀에 재편입한다.

**Git 보고서는 별도 문서 브랜치에서 커밋하여 위 L2로 이미 검증된 코드 SHA를 오염시키지 않는다. 교육용 학생 TODO·강사 정답 분리 정책 유지.**
