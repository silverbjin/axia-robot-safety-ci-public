# AXIA G07 Cycle02 — 실제 NO_GOAL TF/clock 원인 분리 검증 보고 (2026-11-17)

## 작업 범위
- PLAN: d06/docs/AXIA_G07_CM120_CYCLE02_TF_CLOCK_NO_GOAL_PLAN_20261117_KO.md, public plan commit 12fecf337390beff12d3ebdffbc41551bb9ff999.
- Public CI branch fix/g07-cm120-tf-clock-no-goal-audit-20261117; private Instructor branch same suffix, pinned actual private GREEN SHA 0682caeb413c9830107b1a0d297d36597896bed7.
- 공식 Jazzy/Nav2 + TurtleBot3 Waffle + Gazebo Harmonic 기존 NO_GOAL shared startup, exact G07 temporary lidar10Hz/odom100Hz model, same 14-topic recorder and ordered shutdown. NO Goal, NO /cmd_vel publisher, no safety TTL/CM/Guard/Supervisor/Nav2 source changes.
- 원본 기준: public C37 real Moving Goal Run #43898345608 CM RMW source 128.644215ms, Observer128.318661ms; public Cycle01 #43981875149 CM RMW source133.658796ms, Observer131.488230ms; 120ms margin FAIL. Owner Guard internal 158.007666ms >150ms separate hard failure.

## TDD 실행 기록
- Private RED test commit 5aa4f46d6309ac4a59d5a50b0bfba94e7f9044d8; candidate bounded probe commit b2e53944654c8b1b386b201fb8f862461519477c, shared no-Goal opt-in commit 85ba498c3f33948c96658c5613a1ee9881b0e8dd, ROS param regex correction f6faa72295a4b6b28577af3a44e693c057f254ec.
- Public first [Run #43990745709](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43990745709) **FAIL at L0**: immutable old private source RED4 expected errors (probe absent), candidate GREEN3/4 with one test expectation mismatch; real Gazebo job step NOT RUN. Actual mismatch: UNVERIFIED_TF_ODOM_FRAME_MISMATCH vs generic expected UNVERIFIED_TF_ODOM_OR_CLOCK_MISSING. No safety or ROS bug. Corrected only test expectation in private commit 0682caeb413c9830107b1a0d297d36597896bed7.
- Public second [Run #43991016109](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43991016109), release CI SHA 0a41aa274a2089a103d7517803911ee4995c42d2, **completed SUCCESS**. Baseline RED4 FileNotFoundErrors reproducible, candidate GREEN4/4 unit tests, static compile and bash syntax PASS, followed by official real no-Goal Gazebo/Nav2 L2 and NAV2_LIFECYCLE_SHUTDOWN_ACK verified.
- Real L0 log: Ran 4 tests in 0.002s, FAILED(errors=4) expected on baseline; Ran 4 tests in 0.007s, OK on candidate; AXIA_G07_C02_NO_GOAL_L0_GREEN_4_NO_ROS_NO_CMDVEL.
- Real L2 log: AXIA_G07_CM120_BASE_SHIFT_CORRECTION_TRUE_READBACK_NO_GOAL; AXIA_G07_C02_REAL_GAZEBO_NAV2_TF_CLOCK_OBSERVED_NO_GOAL_CM120_ROOT_CAUSE_UNPROVEN; AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false.

## 실제 ROS 2/Gazebo 관측값 — 단일 읽기 전용 rclpy Observer, 8초 구간
| 지표 | 원본 출력 | 판정 범위 |
|---|---:|---|
| base_shift_correction | true (실제 ros2 param readback) | 공식 advanced TF 경로 유지 확인 |
| /clock 메시지 | 2,222건 | 8초 관찰자 실제 수신 |
| /odom 메시지 | 565건 | 8초 관찰자 실제 수신 |
| odom→base_footprint /tf | 562건 | 8초 관찰자 실제 수신 |
| /safety/scan | 63건 | 8초 관찰자 실제 수신 |
| clock sim/wall 평균 증가율 | 0.999124 | 이 실행의 평균, 구간별 RTF 보증 아님 |
| /clock 최대 wall callback 간격 | 333.464ms | 관찰자 시각, 안전 TTL 판정 아님 |
| /odom 최대 wall callback 간격 | 339.852ms | 관찰자 시각, 안전 TTL 판정 아님 |
| /tf 최대 wall callback 간격 | 339.766ms | 관찰자 시각, TF lookup blocking 증거 아님 |
| /safety/scan 최대 wall callback 간격 | 102.943ms | 관찰자 시각, source publish period 증거 아님 |
| /clock- /tf 양의 sim stamp 차이 최대 | 33ms | 부분적 epoch 정합 표본, ROS2 transform wait 아님 |
- 세 채널 /clock,/odom,/tf 각각 최대 ~333~340ms인 이유가 동일 시각 또는 동일 source 원인인지는 **UNVERIFIED**. 여기서는 각 토픽 최대 수치만 저장했고 같은 gap onset timestamp·CM input callback은 없으므로 인과관계 주장 금지.
- 평균 RTF가 0.999124라는 점에서 시뮬레이터의 지속적인 저속 진행만으로 설명할 근거는 약함. 단발성 지연, Gazebo publication, DDS, 단일 Observer callback queue 모두 가설로 유지.
- NO_GOAL 정지 상태에서 300ms를 넘는 관찰 간격은 품질 경고지만 움직이는 Guard/CM의 hard 150/300ms TTL 위반 증거가 아님. 각 채널의 source_publish→receive 및 Guard first transition을 반드시 구분.

## 아키텍처 의사결정
- G0 환경·런타임 계약: 확인 완료. G07 100Hz odom SDF 임시 복사, transform_tolerance=0.02 readback (기존 동일 실행), base_shift_correction=true 이번 실제 readback. TF/odom/scan 데이터 존재 확인.
- G1 root cause: 미확정. 움직이는 첫 CM RMW source 133.659ms interval에 해당하는 official cmd_vel callback entry/exit timestamp 및 TF wait span이 없음. 기존 Cycle31 source has subscription-topic→callback-handle resolver but real exact first gap handle proof not 확보. 이전 Cycle30 LTTng 대량 추적 반복 금지.
- **결론:** 단순 `base_shift_correction=false` 튜닝은 보류. max no-goal TF/odom observer gap만으로 TF 처리 병목 또는 safety sensor stop distance를 판단할 수 없음.
- 다음 단 한 단계: 기존 Cycle31 콜백 핸들 매핑과 CM vpid bounded trace extractor의 **이미 생성된 원본/이전 CI 데이터 접근 가능성**을 먼저 확인. 접근 불가면 단일 CM PID + 실제 first RMW gap 하나만 계측하는 공개 CI 진단 설계를 별도 검토. 증거 없이 실제 Moving Goal 반복 금지.
- TF 지연이 실제 원인으로 확인되면 공식 Nav2 base_shift_correction 옵션의 G07 sim-only A/B에 한정하고, scan stamp age, v*age 위험, STOP/SLOWDOWN zone 거리와 Contact0/Stop dwell 모두 필요.
- Owner WSL2 Goal=BLOCKED; Moving CI 120ms=FAIL historical unchanged; main merge none. SW Stop != certified E-Stop.

## 파일·실행·검증 수준
- Private: tools/p4_g07_cm120_tf_clock_readonly.py, scripts/p2_no_goal_smoke_ci.sh (opt-in only), tests/unit/test_g07_cm120_tf_clock_no_goal_audit.py.
- Public: .github/workflows/axia-g07-cm120-nogoal-tf-clock-l2.yml, Cycle02 plan and this report. Protected Instructor raw ROS logs/UUID/source not uploaded publicly; Actions cleanup confirmed.
- Unit CLI: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/unit -p 'test_g07_cm120_tf_clock_no_goal_audit.py' -v
- Runtime CLI (public workflow only): AXIA_G07_CM120_TF_AUDIT_NO_GOAL=1 AXIA_G07_CI_SIM_GOAL_ALLOWED=0 AXIA_P4_G07_SHARED_PREFLIGHT_ONLY=1 AXIA_G07_SHUTDOWN_L2_ONLY=1 bash scripts/p2_no_goal_smoke_ci.sh
- Verified: PUBLIC_RED4→GREEN4, ROS/Gazebo actual NO_GOAL source TF and clock timestamps, ordered shutdown. UNVERIFIED: real moving CM first callback timing, C37 same-window first-TF delay, stop safety TTL, Owner WSLg parity. Exact public CI/Instructor SHAs above.

AXIA_G07_C02_PUBLIC_L0=RED4_GREEN4_PASS
AXIA_G07_C02_PUBLIC_NO_GOAL_L2=PASS
AXIA_G07_CM120_FIRST_CALLBACK_CAUSE=UNPROVEN
AXIA_G07_CM120_RELEASE=HOLD
OWNER_WSL2_GOAL=BLOCKED_NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
