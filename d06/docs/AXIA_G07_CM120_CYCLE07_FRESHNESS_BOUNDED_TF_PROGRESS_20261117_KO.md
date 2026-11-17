# AXIA G07 Cycle07 교육용 경과보고서 — CM sensor freshness 보호가 동반된 공식 TF 후보

## 왜 이번 Cycle을 수행했는가?
- Cycle05 #43995793080 진단: 실제 CM cmd_vel C++ callback81.972669ms와 first CM source120.172578ms, TF causality UNPROVEN.
- Cycle06 #43997318717 실제 NO_GOAL first G07_C06_SOURCE_TIMEOUT_UNVERIFIED; 공식 Jazzy default source_timeout2.0s, base_shift_correction default true. Source timeout YAML 누락 여부와 실제 runtime 파라미터를 혼동하지 않는다.
- 이동 보정을 끄는 경우 오래된 sensor data로 위치를 잘못 판단할 수 있다. 따라서 Cycle07은 공식 CM source_timeout <=0.300s 라는 **더 엄격한** 센서 freshness 조건을 같이 설정하는 실험. 원본 Guard CM TTL 0.150s, original release margin0.120s, Scan/Odom/Clock TTL0.300s, Stop0.40m/Slow0.75m, native Contact0, Nav2 공식 소스 및 Goal 권한 변경 없음.
- 단, source_timeout=0.3s는 센서 timestamp의 안전 인증이 아니다. Scan header age 실제 기록/주행 속도와 각속도에 따라 남는 위치오차 위험은 별도로 평가한다. Owner WSL2로 출고 금지.

## RED→GREEN→REFACTOR→REVIEW→COMMIT 이력
- Plan: d06/docs/AXIA_G07_CM120_CYCLE07_FRESHNESS_BOUNDED_SIMPLE_TF_PLAN_20261117_KO.md, commit b1352b5e272eaf8280a55b834ab66b1e84502c1b.
- Private RED test 기존 tests/unit/test_g07_cycle06_sim_simple_tf_option.py를 5개 테스트로 강화 commit 0d5446ca8264d9685f1d65b5acc6d5485a0db719. 기존 C06 private 67664552d9283d24db25fadb329733f83dc27878에서 source_timeout 없는 프로파일 및 2s 원본 입력에 대해 예상 RED 2건.
- Private GREEN code: tools/p4_g07_cm_sim_simple_tf.py 실험 승인 범위와 unknown original 보존, official source_timeout default 2.0/explicit2.0→0.300s, already stricter 0.15~0.3 unchanged, other original values fail-closed. Commit 91e09a43a5827e1ae8bb52087cff5bb6975bba45; source pair assign after all validation only commit 3bde220039415d28d12928427dd507dd28346461. Runtime warning about coupled profile commit 60245b7b04f7ef9e0d917f91dcbdbe4e76144046.
- Actual pre-Goal official ROS param readback for base_shift false and source_timeout <=0.300s: scripts/p2_no_goal_smoke_ci.sh commits 84501ab8a6b31db308db1bf38004a29433b4e9ae and regex fix 682849f5dd85cba14fe091fd3317cb0be8a1619b. Source is PRIVATE Instructor; students only public contracts.
- Actual public sealed CI L0 [Run #43998427122](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43998427122) completed SUCCESS, original C06 RED2, candidate GREEN5/5; Python compile, bash -n and readback/launch file static review PASS. Logs:
  AXIA_G07_C07_OLD_C06_UNBOUNDED_SOURCE_TIMEOUT_RED2
  Ran 5 tests in 0.002s
  OK
  AXIA_G07_C07_COUPLED_OFFICIAL_CM_SENSOR_FRESHNESS_STATIC_PASS
  AXIA_G07_C07_RED2_GREEN5_PUBLIC_SEALED_L0_PASS_NO_GOAL
- Public Draft PR #148 / Private Draft PR #200, main NOT_MERGED.

## 실제 공개 sim-only one Goal 진단 (결과 갱신 전)
- Public workflow .github/workflows/axia-g07-cycle07-freshness-simple-tf-moving-l2.yml, exact Instructor private source SHA 682849f5dd85cba14fe091fd3317cb0be8a1619b, original public release C37 official Waffle/Nav2/Xvfb/S02 native 14 topics + seven safety periods unchanged.
- temporary release trigger SHA c952f6ec4083890f12aab684b5e0260f36399130. Actual [Run #43998639510](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43998639510) started; no success claim until result.
- Before Goal, script must print AXIA_G07_C06_OFFICIAL_CM_BASE_SHIFT_FALSE_RUNTIME_READBACK_PASS_SIM_ONLY and AXIA_G07_C07_OFFICIAL_CM_SOURCE_TIMEOUT_LTE_300MS_RUNTIME_READBACK_PASS_SIM_ONLY. If either missing, Goal must be blocked.
- After Goal, check actual ROS event odom max |v|/|w| with conservative 0.300s sensor source-age assumption, bound=0.3*(|v|max +0.75*|w|max); reject if >= Slow-Stop zone x gap0.35m. This is an educational risk screen, NOT observed LaserScan header age or certified safe stopping distance.
- Original Nav2 one-Goal CLEAR→SLOWDOWN→STOP, Contact0, >=1s odom dwell, GoalCancel ACK, ordered Shutdown, Guard CM<=150ms, Scan/Odom/Clock<=300ms, CM native source+Observer<=120ms must all pass in same observed Goal. Failure first boundary determines HOLD.

## 강의용 토론
- 설정 출처 YAML과 코드의 기본값이 다를 때 어떤 자료를 신뢰해야 하는가?
- source_timeout를 2.0에서 0.3으로 줄이는 것은 안전 임계값 완화인가 강화인가? 단, 왜 새로운 STOP 동작 회귀가 필요할까?
- 후속 CLOCK_MISSING을 원인으로 고치기 전에 Nav2 params first exception을 찾는 이유는?
- RMW source 간격과 /scan header age를 같은 수치로 취급하면 어떤 허위 인수 판단이 생기는가?

CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_MOVING_L3=NOT_RUN
CERTIFIED_ESTOP=false

## C07 첫 실제 L2 실패와 정확한 공식 입력 YAML 재검증
- 첫 sim-only public [Run #43998639510](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43998639510) FAILED PRE-GOAL. 최초 launch error: G07_C07_SOURCE_TIMEOUT_NOT_APPROVED_FOR_SIMPLE_TF, 이후 CLOCK_MISSING, FIELD_NO_REAL_GOAL_CANNOT_RELEASE는 cascade. Goal/Stop/CM period는 이 실행에서 수집되지 않았다.
- Jazzy official nav2_bringup/params/nav2_params.yaml (ros-navigation/navigation2@jazzy, exact file blob ac52c787f587288c448079fdcaa2f4c686f25fbd) 에 source_timeout: 1.0 명시. C++ undeclared parameter fallback은 2.0, 둘은 다르다. 시스템 기본값2.0이라는 이유로 원본 YAML의 실제1.0을 무시한 것이 첫 pregoal failure의 원인. 해당 1.0 source 값을 대조하고 다른 정체불명 값은 거부.
- 신규 unit test exact official 1.0→0.300s tightening, unknown1.5 거부를 RED로 편입; private test commit 997e794b82322590d0ddf7f78290cc307b9a1991. 기존 private source commit 682849f5dd85cba14fe091fd3317cb0be8a1619b에서 해당 테스트 FAILED(errors=1) 재현. GREEN code commit 3cdbb65ec6130ed74b28b1368246bb70f99ed423: 공식 YAML1.0 또는 C++ fallback2.0만 .3으로 조정, original already <=0.3은 유지.
- 공개 sealed [Run #43999271004](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43999271004) completed SUCCESS, original C06 RED3 + previously rejected C07 real1.0 RED1 + current GREEN6. 실제 로그: AXIA_G07_C07_PREVIOUS_ACTUAL_JAZZY_ONE_SECOND_SOURCE_TIMEOUT_RED, Ran 6 tests, OK, AXIA_G07_C07_RED3_PLUS_REAL_1S_SOURCE_RED1_GREEN6_PUBLIC_SEALED_L0_PASS_NO_GOAL.
- 새 sim-only 1개 real one-Goal release trigger commit ba31400e01ab98d893b5fc9e221b4cc5743ffcbb, [Run #43999412342](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43999412342) actual outcome pending. 이전 failed Run과 다른 SHA이며, 같은 오류 현장 재시도가 아니라 원본 official config에 대한 새로운 CI RED→GREEN 증거를 갖춘 실행이다.
- 수업 핵심: '기본값(Default)'과 '실제 설정값(Effective configuration)'이 다를 수 있다. 정확한 source provenance를 확인하지 않고 CI 코드를 반복 조정하면 pregoal false negatives에 시간 소모가 크다. 따라서 G07 실제 source_timeout=1.0와 official fallback2.0을 별도로 기록한다.
