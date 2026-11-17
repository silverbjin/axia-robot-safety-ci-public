# AXIA G07 CM120 Cycle06 교육용 경과보고서 — 공식 Nav2 sensor motion compensation 단일 후보

## 문제 경계와 후보 선정
- C05 Run #43995793080 실제 첫 CM source120.172578ms gap에서 정확한 공식 /cmd_vel_supervised callback 81.972669ms 실행을 관측했음. TF 내부 지연 원인 직접 입증은 하지 못함. 이전 true 기본 설정의 non-tracing CI source128.644ms/133.659ms release FAIL.
- 공식 Nav2 Jazzy code collision_monitor_node.cpp 에서 base_shift_correction (default true) 글로벌 파라미터를 Source별로 전달하며, source.cpp의 advanced vs simple TF lookup 선택. 공식 Issue #3402 / 병합 PR #3412가 선례.
- 하나의 sim-only 후보만 검토: 정확한 G07 공개 CI 내에서 공식 param base_shift_correction=true(원본)→false. Safety Supervisor/Guard/CM 공식 소스/STOP0.40/SLOW0.75 polygon/source_timeout/TF bound0.02/120ms release/150ms hard/300ms Scan·Odom·Clock 전부 그대로.

## RED→GREEN→REFACTOR→REVIEW→COMMIT
- PLAN: d06/docs/AXIA_G07_CM120_CYCLE06_OFFICIAL_TF_OPTION_PLAN_20261117_KO.md commit 7642d168c03a3b896461f1c2e39f08a28182e5d9.
- private original 966886c4627deb2bb3b37111fe336eeee6b9ebb4, candidate private commit 67664552d9283d24db25fadb329733f83dc27878.
- Test RED commit f93687d936e5da8e2b5343042b6c0227694136b3. GREEN-only module tools/p4_g07_cm_sim_simple_tf.py commit 2a355df98717285290497f07b8664928a39e1559, original Nav2 config writer guarded insertion commit db12d85a33f70184821cbb1ecff1541835b9bc34, original Goal runner pre-goal readback insertion commit 67664552d9283d24db25fadb329733f83dc27878.
- Actual public sealed Run #43997055220 SUCCESS; old source missing module expected RED, private candidate 4/4 GREEN, source diff scope check, bash syntax, py_compile. Actual log:
    AXIA_G07_C06_ORIGINAL_OFFICIAL_SIMPLE_TF_CONTRACT_MISSING_RED
    Ran 4 tests in 0.003s
    OK
    AXIA_G07_C06_SCOPE_ONLY_OFFICIAL_CM_PARAMETER_UNCHANGED_GUARD_STATIC_PASS
    AXIA_G07_C06_RED_GREEN_4_PUBLIC_SEALED_L0_PASS_NO_GOAL
- Public Draft PR #146, private Draft PR #198. Source acceptance scope: public scripts d06/docs and .github/workflows only, private only test+option module+launch params+pre-goal actual readback. main unmerged.

## 실제 G07 sim-only Moving Goal 통합 CI 후보
- Public source workflow .github/workflows/axia-g07-cycle06-official-simple-tf-moving-l2.yml from unchanged C37 Waffle/Nav2 one Goal baseline. Exact candidate pin 67664552d9283d24db25fadb329733f83dc27878, original 14-topic/ S02 Contact0/CLEAR-SLOW-STOP/Nav2 ordered shutdown original requirements. Test must first prove live /collision_monitor base_shift_correction=false, then inspect motion error upper candidate vs slow-stop zone gap0.35m, then original CM source/Observer<=120ms and Guard<=150ms, Scan/Odom/Clock<=300ms.
- Conservative motion error screen assumes 0.5s scan age maximum for educational bounding but **does not measure actual scan header age**, so its PASS cannot certify safe sensor compensation; fail is a hold. Stop zone geometry untouched and sim-only.
- Public release one-shot trigger commit 1490f564ac4f06317392291e3f22247aff156b12; [Run #43997318717](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43997318717) started; actual result to append after final verification.

## 교육용 해설 질문
- ROS2 param YAML의 정적 diff가 실제 /collision_monitor readback을 대체할 수 없는 이유는?
- 동일 소스 이외 안전 코드 0건 변경에서도 sensor points time correction을 끄면 어떤 안전 정확도 위험이 생기는가?
- 왜 scan callback 간격을 sensor header timestamp age로 간주하면 안 되는가?
- tracing on callback81.973ms와 이번 tracer-off real L2 결과를 직접 인과로 단정할 수 있는가?
- CM 120ms 성공만으로 왜 Guard150ms, contact0, stop dwell, CancelGoal, ordered shutdown까지 검증해야 하는가?

## 현재 미검증/중단 규칙
- 실제 candidate run 결과 / WSLg Owner L3 / stop displacement physical hazard proof / TF call internal duration / no-scan-age actual certification은 아직 미검증.
- Owner/Hardware 적용 금지. 검증 없이 main merge 금지. G07 시연의 software STOP은 certified E-Stop이 아님.

AXIA_G07_C06_PUBLIC_L0=RED_GREEN4_PASS
AXIA_G07_C06_REAL_MOVING_L2=PENDING
CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false

## Cycle06 실제 공개 G07 sim-only L2 결과 및 첫 실패 포렌식
- 실제 [Run #43997318717](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43997318717), release SHA 1490f564ac4f06317392291e3f22247aff156b12, completed FAILURE. Sealed RED/GREEN4, immutable runtime, GUI/CPU, S02 native build까지 PASS. 실제 official Waffle/Nav2 one-Goal step에 진입했으나 **Goal이 보내지기 전에** Nav2 파라미터 writer의 fail-closed 조건에서 launch exception 발생.
- 첫 실제 오류: G07_C06_SOURCE_TIMEOUT_UNVERIFIED. 정확히 private tools/p4_g07_cm_sim_simple_tf.py의 cm.get('source_timeout')이 유효한 수치/범위인지 검사 중 실패. 원래 파라미터 YAML에서 해당 값을 검증하지 못한 것을 실패로 정직하게 처리한 것이다.
- 공식 Jazzy collision_monitor_node.cpp 선언에는 'source_timeout' undeclared default 2.0초, 'base_shift_correction' undeclared default true. **이번 후보는 CM 노드 생성에 실패했으므로 실제 source_timeout runtime readback=2.0을 확보하지 못했다**; 원래 YAML에서 값이 부재/비범위인 사실과 공식 fallback2.0이라는 소스 근거를 구분한다.
- 후속 'P2_STAGED_NO_GOAL_BLOCKED: CLOCK_READY: CLOCK_MISSING'와 필수 후처리 단계 FIELD_NO_REAL_GOAL_CANNOT_RELEASE는 **최초 launch failure의 연쇄 결과**, 스캔/시계/CM 내부 오류의 독립 원인 아님. 실제 moving Goal/CM120 샘플/Stop/Collision 새로운 관측 없음.
- 안전 의미: source_timeout가 실제 2초 수준이면 'base_shift_correction=false' 선택 시 시뮬레이션의 움직이는 센서 point 위치 보정 오차를 무시하는 위험이 커질 수 있다. 기존 Guard Scan TTL300ms는 별개의 downstream safety layer이므로 자동으로 CM source freshness2초를 허용할 수 있다는 의미가 아님.
- 원래 Stop 0.40m/Slow 0.75m 정책, Guard150ms, release120ms, Scan/Odom/Clock300ms을 **조정하지 않았다**. 억지로 검사 범위를 늘리거나 값을 임의로0.3으로 바꿔 Goal을 통과시키지 않는다.

## 이번 Cycle의 RED→GREEN 및 회귀 성과
- Original baseline code missing gated single parameter module expected RED. Candidate private GREEN4/4 public sealed [Run #43997055220](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43997055220) PASS. 임의 Owner/NO_GOAL/other ROS/safety-zone changed mode는 코드에서 ValueError로 차단. 대조: 실제 source_timeout 미확인 경우에는 sim 후보를 fail-closed로 중단.
- 실제 L2는 Goal 이전 오류. 이전 Cycle05 Source gap120.173ms+cmdVel callback81.973ms와 새 CM 설정 후보의 성능 비교는 **미실행**. 이 상태에서 CM120 해결/최종 안정화 PASS 보고 금지.
- 이 사이클은 '개별 함수의 GREEN과 실운영 파라미터 계약 일치'가 다르다는 TDD 교육 사례. 학생은 original source/default/time contract에서 최초 fail을 찾고 CLOCK_MISSING 연쇄에 집중하지 않는 훈련을 한다.

## 결정 및 최소 다음 Cycle
- C06 official simple TF sim-only 후보는 즉시 출고 불가. **다음 단계는 safety policy 수정이 아니라 원래 CM 파라미터의 실제 NO_GOAL readback**을 확보해 source_timeout 설정 출처와 시간축을 먼저 확인하는 것이다. 필요 시 관련 기준 문서 원문을 대조한다.
- 실제 런타임 source_timeout가 안전 경계로 입증되고 STOP geometry/scan.header.stamp/v 및 ω 범위가 확인된 경우에만, 원래 runtime 코드의 공식 옵션 하나를 바꾸는 CI-only 실험을 승인할 수 있다. 기존 hard TTL과 original release gate를 우회하면 안 된다.
- 동일 잘못된 candidate/run SHA로 현장 또는 공개 Moving Goal을 반복하지 않는다. Owner WSL2 NOT_RUN, main 미병합, SW Stop != certified E-Stop.

AXIA_G07_C06_PUBLIC_L0=RED4_GREEN4_PASS
AXIA_G07_C06_REAL_L2=PREGOAL_PARAMS_FAIL_CLOSED_NO_GOAL
AXIA_G07_C06_FIRST_FAILURE=SOURCE_TIMEOUT_UNVERIFIED
CM120_ROOT_CAUSE=PARTIAL_CALLBACK_LONG_TF_UNPROVEN
CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false

## Cycle06 사후 정정 — source_timeout 기본값과 실제 공식 YAML 값의 구분
- 중요 정정: 앞서 '원래 YAML source_timeout가 부재할 수 있다'고 기술한 문장은 원본 확인 전 가설이었다. 소스 수준에서 원래 `tools/p2_zone_overlay.py::patch_p2_zone_parameters`는 source_timeout 미존재/비양수일 때 ValueError를 내므로, **해당 파라미터가 없다면 최초 Nav2 파라미터 overlay도 통과할 수 없다**. Cycle06 실제 첫 오류는 값의 부재만을 증명하지 않는다.
- 외부 공식 Jazzy [`nav2_bringup/params/nav2_params.yaml`](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_bringup/params/nav2_params.yaml)에는 collision_monitor.source_timeout=**1.0초**, transform_tolerance=0.2초, base_shift_correction=True가 명시되어 있다. 반면 [`collision_monitor_node.cpp`](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/collision_monitor_node.cpp)의 *파라미터 미선언 시* 코드 기본값은 2.0초다. 이 둘은 다른 계약이다. 실제 해당 컨테이너 설치 파일 SHA/파라미터 readback은 아직 직접 확인 전이다.
- Cycle06 초과로 구동 중단된 직접 원인은 private `p4_g07_cm_sim_simple_tf.py`의 **임의 0.15~0.50초** 범위 제한이며, 공식 YAML의 1.0초를 허용하지 않는 테스트 설계 오류일 가능성이 높다. 안전을 이유로 더 짧은 값을 강요하는 것이 본 실험의 원래 '공식 1개 파라미터만 변경' 계약에 부합하지 않는다.
- 수정 정책: source_timeout를 인위적으로 0.5초 이하로 변경하지 않고, 기존 공식 YAML의 값과 실제 NO_GOAL 런타임 값을 공개 CI에서 대조한다. 그 결과 없이 `source_timeout=1.0`을 실제 시행값으로 확정하지 않는다. 현재 `base_shift_correction=false`는 Goal 이전 차단 상태 유지.
- 일회성 공개 release C06 workflow는 이미 cleanup `7b859836724ded52f8fd3f0d436bbcdb627fc3e9`(Moving L2), `59788bf73bef6e8734ed47689b867e6d0b57808e`(L0)로 회수. 원래 자동 GOAL HOLD 유지.

### 교육 포인트
- **라이브러리 선언 시 기본값**, **공식 패키지 기본 YAML**, **실제 설치된 파일**, **노드 실행 중 readback**의 네 층위는 다르며, 1.0과 2.0을 임의로 혼용해서는 안 된다.
- 파라미터 검사 코드 자체가 실제 baseline보다 더 제한적인 가설이었는지 의심한다. GREEN4는 존재하지 않는 범위를 단위 테스트로 강제한 자체 검증에 불과할 수 있다. 반드시 실제 런타임을 계약의 기준으로 삼는다.
