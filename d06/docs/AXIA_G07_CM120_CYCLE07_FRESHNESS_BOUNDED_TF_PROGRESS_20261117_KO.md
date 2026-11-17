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

## Cycle07 실제 second L2 종료 — FIRST CLOCK_READY failure
- 다음 candidate private SHA 3cdbb65ec6130ed74b28b1368246bb70f99ed423, public release SHA ba31400e01ab98d893b5fc9e221b4cc5743ffcbb, 실제 [Run #43999412342](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43999412342) completed FAILURE, NO GOAL.
- 공개 sealed prior exact Jazzy original YAML 1.0s RED1, original C06 RED3, candidate GREEN6/6 [#43999271004](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43999271004) SUCCESS. 실제 C37 official runtime image+S02 preflight PASS, 이후 actual Gazebo/Nav2 startup stage failed at CLOCK_READY.
- 최초 실제 필수 실패 메시지: P2_STAGED_NO_GOAL_BLOCKED: CLOCK_READY: CLOCK_MISSING. 같은 창의 read-only: AXIA_G07_CI_LAUNCH_PID_ALIVE=true, AXIA_G07_CI_CLOCK_TOPIC_PRESENT=true, actual /clock callback count0, timeout90s. 이전 C06 & C07 #439986에는 source_timeout validation exception이 먼저 나왔으나 이번 #439994에는 그 문구가 보고되지 않음.
- 이번 실행의 공개 로그는 launch.log tail만 출력하므로 첫 시작 단계의 Gazebo/ROS exception/bridge log는 직접 연결되지 않았다. 따라서 Clock producer stopped, bridge no messages, DDS subscriber backlog, sim paused 등의 **원인 분류는 UNPROVEN**; source_timeout fix가 실제 런타임 두 파라미터를 반영했는지도 missing Goal preflight 때문에 **UNVERIFIED**.
- 후속 G07_C06_NO_ACTUAL_ONE_GOAL_ODOM_RISK_EVIDENCE, FIELD_NO_REAL_GOAL_CANNOT_RELEASE 및 S02/MsgInfo/CM120 audit MISS는 CLOCK_READY 실패에 따른 cascade, 주행 실패를 입증한 원본이 아님.
- 이 실행에서 실제 ROS Moving Goal 없음. CM source/Observer120ms 릴리스 수치는 새로 측정되지 않았고 이전 실제 실패 128.644ms/133.659ms와 진단 120.173ms만 보존.

## 교육적 후속: Cycle08 최소 실패 경계
- 현재 C07 SIM coupled profile을 안전 출고로 배포하지 않는다. release one-off full moving workflow를 삭제하고 immutable failed Run을 보존.
- 동일 값을 재시도하지 않고 **NO_GOAL에서 clock producer(Gazebo)→bridge (/clock)→ROS subscriber** 최초 타이밍을 독립 관찰하며, launch.log 첫 error와 clock topic 노출 여부·message count를 함께 확보. 실시간 Deadline 90초를 무턱대고 늘리지 않는다.
- Clock gate가 다시 성공하고 root cause를 좁힌 뒤에만 C07 Moving sim 후보를 다시 검토. 안전 속도·LaserScan header age/zone 정확도·120ms margin까지 검증하지 않은 상태라 OWNER WSL2 L3=BLOCKED.

AXIA_G07_C07_PUBLIC_L0=RED3_PLUS_ORIGINAL_1S_RED1_GREEN6_PASS
AXIA_G07_C07_REAL_L2=FAIL_CLOCK_READY_NO_GOAL
AXIA_G07_C07_CLOCK_FIRST_BOUNDARY=TOPIC_PRESENT_ZERO_MESSAGES
AXIA_G07_C07_RUNTIME_PARAM_READBACK=NOT_RUN
CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false

## 교차 검증: 기존 NO_GOAL 실제 CM source_timeout은 1.0초
- 별도 public [Run #43999183495](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43999183495)에서는 원본 G07 NO_GOAL profile의 실제 /collision_monitor readback을 수행하여 source_timeout_sec=1.0, base_shift_correction=true, transform_tolerance_sec=0.02 를 확인. official installed Nav2 YAML SHA256 299f9002d6dcfbf661e532c99f32dda1766eab3afa3ab71a52378d80e7ef956f. 이 값은 소스 fallback2.0이 아니라 실제 런타임 값이라는 점을 분리한다.
- 하지만 해당 별도 NO_GOAL run의 전체 lifecycle shutdown은 BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT(rc3) FAIL이므로 원래 G07 안정성의 전체 PASS가 아님. 다른 safety layer boundary가 확인되지 않음.
- 이번 C07 moving candidate #43999412342가 clock topic existed but ROS callback0에서 중단된 원인에 대한 증거를 제공하지는 못한다. 서로 다른 CI Run의 max/stage를 한 run의 인과로 합성하지 않는다.

## Cycle07 최종 교육용 판정
- C07 official config 1.0 출처 및 strict source_timeout .3 + base_shift false 코드 L0 GREEN6 verified, actual moving Goal prestartup CLOCK_READY_FAIL, root cause of startup inconclusive.
- C07 paired profile can only be evaluated after no-Goal Clock publisher/bridge/Observer and navigation shutdown boundary separately verified; no unpinned SHA/false CI pass.
- NEXT Cycle08 scoped: **read-only CI failure-window clock transport and first launch ERROR capture**, no new Goal, no new safety/source modifications. CI original Clock TTL 300ms and 120ms release must not be relaxed.
