# AXIA G07 Cycle02 — CM120 최초 구간 TF/Executor 원인 분리 NO_GOAL 계획

## 성격 및 결정
- 기존 공식 Nav2 Jazzy Collision Monitor(입력 Twist 콜백 → source.getData → TF → velocity publish)에서 발생하는 120ms release margin 초과의 **원인 분리**. 신규 safety 제어·주행 기능 개발 아님.
- 기존 정상/실패 실제 실행: public #43898345608 CM RMW source 128.644215ms, observer 128.318661ms; public #43981875149 source133.658796ms, observer131.488230ms. Supervisor는 첫 gap 동안 추가 발행 2건. 이전 Owner Guard first CM age158.007666ms>150ms 별도 하드 위반. `CM_RELEASE=HOLD`.
- 외부 참조: 공식 Nav2 Issue #3402, merged PR #3412. `base_shift_correction=true` advanced TF lookup(odom 포함)이 기다릴 수 있으나 현재 AXIA가 이미 Gazebo odom 임시 30→100Hz, CM transform_tolerance 0.2→0.02s 설정을 적용했으므로 원인 확정 불가.
- 이전 Cycle30 trace 2611716 callback events 중 CM 849/registrations 817, 실제 cmd_vel callback identity 0. Cycle31 public L0 후 실제 Goal callback identity 인과 입증 없음. 기존 모든 raw trace를 공개하지 않으며, 무제한 tracing 재실행 금지.
- **단일 목표:** 이미 존재하는 G07 Nav2 실제 NO_GOAL 스타트업에서 `/clock`, `/odom`, `/tf`, `/scan`의 벽시계/시뮬레이션 timestamp와 CM 실제 `base_shift_correction`·`transform_tolerance`을 **읽기 전용** 수집. 그 결과로 TF·RTF 가설의 반증 가능성을 높이고, 이후 한 단계만 선택.

## 개발·검증 순서 (RED→GREEN→REFACTOR→REVIEW→COMMIT)
1. **RED**: 기존 소스 불변 `966886c4627deb2bb3b37111fe336eeee6b9ebb4`에는 신규 G07 NO_GOAL TF/clock 관찰값 계약이 없음을 단일 unittest로 검증한다. 기존 실제 120ms 수치는 RED fixture로만 사용, fake ROS 성공 금지.
2. **GREEN L0**: 비공개 `tools/p4_g07_cm120_tf_clock_readonly.py` 하나, 기존 `scripts/p2_no_goal_smoke_ci.sh`에 `AXIA_G07_CM120_TF_AUDIT_NO_GOAL=1` 조건부 호출 1개를 추가한다. 다른 컴포넌트 수정 없음. 관찰기 자체는 구독만 하고 제어 publisher/Goal 0. 시계 영역이 다르거나 TF/odom 프레임 누락이면 `UNVERIFIED`/HOLD. 시계 sim-age와 관찰 wall-gap을 혼동 금지.
3. **공개 L0**: exact private RED baseline vs GREEN 4개 순수 진단 계약 + static no-control/no-goal 체크. 물리 안전 TTL·CM `base_shift_correction` 상태는 절대 바꾸지 않는다.
4. **공개 실제 NO_GOAL Gazebo/Nav2 L2 1회**: 이미 성공한 `.github/workflows/axia-p4-g07-owner-shared-pregoal-l2.yml` / private `scripts/p2_no_goal_smoke_ci.sh`/immutable Jazzy runtime digest만 사용. 필수: actual `/tf`, `/odom`, `/clock`, `/scan` 및 CM `base_shift_correction` readback. NO_GOAL, NO_FAULT, NO_CM_STOP_INJECTION. 관측된 RTF는 **NO_GOAL 관측값**이지 움직이는 CM callback 원인 확정이 아님.
5. **REVIEW+COMMIT**: 정확한 Run ID, first boundary, 실제 속도 값, 검증 범위, 미검증 사항을 docs 커밋. 증거 없으면 `ROOT_CAUSE=UNPROVEN`; 지표가 CM TF 가설을 지지하면 다음 사이클에서 공식 CM callback identity + 단일 계측 또는 안전한 `base_shift_correction` sim-only A/B 계획. 근거 없으면 추가 Gazebo Goal 금지.
6. **출고 중단 규칙**: Owner WSL2/Moving Goal은 L2 120ms GREEN 및 별도 150/300ms hard TTL 원본 동시 인수 전까지 금지. main 병합은 사용자 승인 대기.

## 기술 제약
- G07 작업은 비공개 instructor 브랜치와 public CI 브랜치에만. 학생 저장소/강사 정답 공개/정식 인증 E-Stop 주장 금지.
- 진단 절대 `/cmd_vel`/Nav2 Goal publisher 생성 금지; 실패 보정용 dummy input도 금지.
- no-goal 관찰자에서 `/clock` sim clock 간격과 host monotonic 수신 간격, `odom->base_footprint` TF 시각 및 `/odom` stamp를 같은 관찰 노드에서 수집. 각 clock domain이 정합하지 않으면 비교하지 않는다.
- 실측 전까지 모든 상태: `CM_120MS_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `OWNER_WSL2_GOAL=BLOCKED`.
