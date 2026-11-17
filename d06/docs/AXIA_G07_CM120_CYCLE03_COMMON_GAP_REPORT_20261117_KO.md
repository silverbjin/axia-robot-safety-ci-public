# AXIA G07 Cycle03 교육용 경과보고서 — 공통 시간 공백을 실측으로 검증

## 학습 목표: 상관과 인과를 분리하라
Cycle02 실제 Gazebo NO_GOAL #43991016109는 /clock333.464ms, /odom339.852ms, /tf339.766ms **개별 max**를 얻었지만 같은 시간인지 알 수 없었다. 이번 Cycle03은 최대 gap별 정확한 host monotonic [start,end] 시간 구간을 공통 교집합으로 연결했다. 단순히 3개 숫자가 비슷하다는 이유로 공통 stall이라고 결론 내리지 않는 것이 목적이다.

## 상황·원본 기준
- 기존 **실제 Moving Goal 실패**는 #43898345608 CM RMW source128.644ms/Observer128.319ms, #43981875149 CM source133.659ms/Observer131.488ms, 릴리스 120ms 미달. Owner 실제 최초 Guard CM age 158.008ms>150ms 별개 하드 실패.
- 이번 수정은 **NO_GOAL** 검증으로 제한. ROS Jazzy, Harmonic, Nav2 공식 CM, 임시 Waffle lidar10Hz/odom100Hz, 기존 14-topic/종료 ACK 재사용. 제어 명령·공식 Nav2·Safety Supervisor·Guard·CM·120/150/300ms 변경 없음.

## RED→GREEN→REFACTOR→REVIEW→COMMIT의 실제 기록
1. 계획 커밋 `f5fb8db2d45e5dbc4a75038711ea2f29cc7f43b0`: H1 공통 wall 공백 vs H0 시간대 불일치, 원인 판단의 한계와 정지 규칙 고정.
2. private RED 테스트 `tests/unit/test_g07_cm120_cycle03_common_gap.py`, 커밋 `4f130af259d6ded1f6ef9152efb3f89137303af9`. 기준 이전 private `0682caeb413c9830107b1a0d297d36597896bed7`에서 새 필드 missing expected error 2건, corrupt clock case는 이미 fail-closed PASS.
3. GREEN private `tools/p4_g07_cm120_tf_clock_readonly.py` 커밋 `2df98da9cb9507ce905acbe82da46e93a79f0398`: 기존 NO_GOAL 프로브의 순수 evaluate 함수만 +25줄 수정. ROS subscriptions/control/clock-domain safety 변경 0.
4. 공개 CI workflow 변경 `7b67561f0454f763f137ca5cd408cdf353e7b5a9` → temporary release SHA `2a5e2d09a0edca7267c2bd25a649d30167427bdc`. 실제 [Run #43992804389](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43992804389) completed SUCCESS. Baseline `Ran 3 tests ... FAILED(errors=2)` (예상 RED), 후보 `Ran 3 ... OK` 신규 + `Ran 4 ... OK` 기존, public `AXIA_G07_C03_NO_GOAL_L0_GREEN_3_PLUS_PREV4_NO_CMDVEL`. 실제 Gazebo/Nav2 NO_GOAL, ordered shutdown ACK PASS.
5. 차이 리뷰: 기존 safety-related files changed0, 신규 raw ROS/Gazebo trace 유출0, Goal sent false, RMW/source CM callback measured false. ~~ROS 실제 CM120 GREEN~~ 아님.

## 실제 NO_GOAL 공통 wall 간격 원본 — Run 43992804389
```text
AXIA_G07_CM120_BASE_SHIFT_CORRECTION_TRUE_READBACK_NO_GOAL
clock_count=1331
odom_count=346
tf_odom_count=343
scan_count=73
clock_max_wall_interarrival_s=0.333601
odom_max_wall_interarrival_s=0.338193
tf_max_wall_interarrival_s=0.338594
clock_odom_tf_max_gap_overlap_s=0.333601
clock_odom_tf_max_gap_coincident=true
scan_max_wall_interarrival_s=1.02678
sim_to_wall_factor=1.211201
clock_max_gap_sim_step_s=0.093
odom_max_gap_sim_step_s=0.060
tf_max_gap_sim_step_s=0.300
clock_tf_max_sim_age_s=0.288
goal_sent=false
cm_tf_callback_causality_proven=false
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```
- **H1 관측 확인**: 세 가지 최대 wall callback 간격의 교집합 333.601ms; H0 '서로 독립 시점'은 이 관측에 부합하지 않음.
- 세 sim-time 증가량 93ms/60ms/300ms는 wall 기간 333.6ms와 1:1로 맞지 않는다. 이 값은 수신 구간에 들어온 각 메시지의 header 시각이며 서로 다른 토픽/발행 계층에 속함. 이를 공통 clock step 원인으로 단정하면 안 됨.
- Scan 최대 callback gap 1.02678s는 NO_GOAL 이 시도에서 관측됨. 단일 Observer spin scheduling/Gazebo+DDS delivery/source stamp 차이를 분리하지 못하므로 Moving Guard hard TTL 위반의 실측 근거는 **아니다**.
- 정지 NO_GOAL의 공통 stall은 Moving CM source 133ms 간격과 동일 구간이 아니다. TF blockage와 CM callback backlog는 여전히 **UNPROVEN**.
- 정확한 화면·종료 및 원본 커밋 검증 범위: CI Ubuntu24 native Xvfb/headless, Owner WSLg 실제 GUI/Moving L3는 NOT_RUN.

## 강의 토론 주제
- 세 토픽의 max가 비슷해도 왜 동일 stall이라고 할 수 없는가? **최대 [start,end] 교집합**이 필요하다.
- 공통 stall이 관찰돼도 왜 TF 내부 원인이라고 단정하면 안 되는가? 동일 Executor 또는 DDS·Gazebo source가 공유 병목일 수 있다.
- NO_GOAL Scan 1초 공백인데 왜 Guard150/300ms 실패를 곧바로 판정하지 않는가? 주행·안전 소비자·source timestamp·Guard first latch가 연결되지 않았다.
- 평균 RTF>1이면 왜 지연이 없다는 뜻이 아닌가? 전체 평균은 330ms 단일 정체를 숨길 수 있다.

## 다음 Cycle04 최단 경계
기존 Cycle31 `d06/live/g07_cycle31_cm_topic_callback_identity.py`의 `rcl_subscription_init→rclcpp_subscription_init→rclcpp_subscription_callback_added` 핸들 맵과 Cycle30 bounded CM PID trace를 재사용. 실제 공식 CM에 명확한 토픽→콜백 handle이 매핑되지 않으면 **기존 추적의 한계**를 보고하고 Moving Goal 무작정 실행 금지. 확인되면 해당 CM callback start/end vs first RMW source interval의 직접 증거를 위한 목표 1개에 한정된 진단을 별도로 설계.

## 파일/명령/검증/미검증
- Unit:
```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/unit -p 'test_g07_cm120_cycle03_common_gap.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/unit -p 'test_g07_cm120_tf_clock_no_goal_audit.py' -v
```
- 실제 public Run: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43992804389
- 검증: 실제 Jazzy+Gazebo+Nav2 NO_GOAL L2 + L0 7/7, 원본 민감데이터 회수. 미검증: Moving CM first-gap/Guard150ms/120ms release, Owner L3. PR 공개 #142 / Instructor private #196 Draft, main 병합 없음.
- `AXIA_G07_CYCLE03_NO_GOAL_L2=PASS`; `CM_FIRST_CALLBACK_CAUSE=UNPROVEN`; `CM_120MS_RELEASE=HOLD`; `AXIA_MVP_DEMO_ACCEPTED=HOLD`; `CERTIFIED_ESTOP=false`.

## 종료 후 release 정리
- 단발성 C03 실행 워크플로 release 브랜치에서만 삭제, cleanup commit `f22014064c670fe14827f540e4ae4f2b40ee2305`. 공개 Draft PR #142/비공개 #196의 원본과 실제 Run #43992804389를 보존. Moving Goal release HOLD 워크플로는 수정하지 않음. 
