# AXIA G07 — S1 공식 Nav2 문서·Issue 기반 단일 Moving Goal 원인 진단

## 0. 목적과 현재 인수 판정
- 사용자가 **S1** 진행을 승인하면서 공식 Collision Monitor 설정·이슈 리서치를 **진단보다 먼저 수행**하도록 요청. 원래 C05/C37 official Nav2, Waffle, Gazebo Harmonic 재사용.
- CM120 source·Observer <=120ms, Guard hard age<=150ms, Scan/Odom/Clock<=300ms 등 본래 경계를 유지. SW STOP과 인증 E-Stop 구분. CM120 `CAUSE_UNPROVEN`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, Owner WSL2 NOT_RUN. `main` 병합 별도 승인.

## 1. 조사한 공식 문서 (Jazzy 버전 고정)
1. Nav2 Jazzy Configuration: https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/collision_monitor/configuring_collision_monitor_node/
   - `base_shift_correction` default **true**: source time과 현재 base 이동 차이를 Advanced TF transform으로 보정. 저속 로봇에도 정확도와 성능 절충; 공식 설명 평균 비용 대략 `1/(2*odom_rate)`, 빠른 로봇 비활성화 권고하지 않음.
   - `transform_tolerance` default **0.1s**: lookup/transform 허용 시각·대기와 관련; **AXIA 실제 runtime 0.02s** (Cycle07 installed source vs live CM readback #43999183495). 공식 기본값과 현장 overlay 값을 혼동하지 않음.
   - `source_timeout` default **2.0s**: 관측 센서 데이터 신선도, source별 override 가능, 0이면 검사가 비활성화되므로 사용 금지. **AXIA 실제 installed+runtime 1.0s** (same #43999183495), 임의 0.3/0.5초 변경 금지.
   - `stop_pub_timeout` default **1.0s**: 지속 ZERO 상태 후 발행을 멈출 수 있음. **AXIA runtime 값은 이번 연구에서 별도 실측하지 않음**. 최초 MOVING 구간 120~139ms 출력 공백과 장시간 STOP ZERO suppression을 동일 현상으로 오인 금지.
   - `cmd_vel_in_topic` default **cmd_vel_smoothed**; AXIA actual CM subscribed **/cmd_vel_supervised** (Cycle04 exact callback topic handle). `enable_stamped_cmd_vel` Jazzy default false; stamped vs unstamped 처리와 Header/MessageInfo로 입력·출력 메시지의 정확한 대응을 추정하지 않음.
2. Nav2 Jazzy source code:
   - https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/collision_monitor_node.cpp
   - https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp
   - https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/scan.cpp
   - `cmdVelInCallbackStamped→process→source->getData→Scan::getData→Source::getTransform→nav2_util::getTransform(Advanced)`; 별도 고정 출력 주파수 timer가 아니라 입력 callback에 의존. STOP 지속 시 `publishVelocity`가 ZERO publish를 생략할 수 있음.
   - Original source `getTransform`: `base_shift_correction_ true` → source header stamp→now advanced TF, false→simple TF. 이 옵션은 단순 속도 스위치가 아니라 센서 좌표 시각 보정 정책.
3. Official Nav2 Jazzy package README: https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/README.md
   - LaserScan360 points Stop/Slowdown/Limit benchmark 약 **4.45ms**. 원래 하드웨어·input rate·장애물 수·tf readiness·Executor 조건이 달라 AXIA C05 81.973ms 콜백 elapsed와 직접 동일 벤치마크 비교는 불가능. LTTng tracer overhead도 분리.
   - CPU level software stop은 hard real-time certified E-Stop이 아님.

## 2. 공식 Issue/PR에 따른 인과 가설
- https://github.com/ros-navigation/navigation2/issues/3402 (**Closed**): Advanced lookupTransform에서 fixed frame→base transform 대기, 한 사례의 fixed-frame TF 30Hz에서 최대 ~33ms 추가 지연 가능. **원래 사용자 보고에 한정**된 내용, AXIA의 확인된 원인으로 확장 금지.
- https://github.com/ros-navigation/navigation2/pull/3412 (**Merged**): simple vs advanced TF lookup 선택 옵션 `base_shift_correction`. 당시 TB3 Gazebo와 테스트 수행, simple 모드는 낮은 정확도/성능 절충. 이미 Jazzy 설치 코드에 존재하므로 새로운 기능 구현 불필요.
- AXIA 다른 실행에서 odom 100Hz overlay를 사용. 공식 평균 보정대기 추산 ~5ms는 worst-case가 아니며, C05 콜백 wall=81.973ms나 별도 S1 최초 CM source138.611ms의 설명 증명이 아님.
- **이번 S1의 단일 가설 시험:** TF 함수 wall clock 및 thread CPU 시간, 공식 C05 cmd_vel 콜백 포인터/동일 CM PID·TID, 최초 CM RMW publisher source gap (source SYSTEM 내 비교)과 observer host MONOTONIC을 각자 정합. TF wall이 지연 대부분이라도 TF blocking vs CPU 선점/스케줄링은 `CAUSE_UNPROVEN` 유지.

## 3. S0 완료 증거와 S1 사전 진입 게이트
- S0 public source branch `fix/g07-cm120-s0-no-goal-diagnostic-regression-20261117` HEAD `904904df2ddd12c3f6cc2149945f0178face8eb1`; report `d06/docs/AXIA_G07_CM120_S0_READINESS_AND_LOCALIZATION_REGRESSION_20261117_KO.md`.
- Public real S0 L0 [#44009950139](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44009950139): bounded exact CM filter GREEN4, C05 TF interval join3, future inline diagnostic static compile2, old source RED. No Goal.
- Public actual official S0 NO_GOAL L2 [#44009454224](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44009454224): exact original private `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, CM mapped test-only TF shim & `TF_ADV` calls **337**, Navigation+Localization shutdown both ACK, runtime rc0 and goal_sent=false. This proves actual loader/function invocation **only in NO_GOAL**, not moving temporal root.
- Last actual diagnostic Moving Goal [#44007105539](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44007105539): source first gap **138.610710ms**, TF proof failed old trace >100k, Localization shutdown 25.000396s timeout. Its result preserved as FAIL. No rerun of same source.
- S1 candidate uses S0 test-proven bounded **exact topic→callback** stream collector; child-only LD_PRELOAD already tested NO_GOAL; existing original pinned private Goal/Guard/CANCEL/S02 contact/Nav2 ordered shutdown unmodified. Diagnostic tracer-ON never release benchmark.
- **No other speculative tunings**: `base_shift_correction=true`, `source_timeout=1.0`, `transform_tolerance=0.02`, CM120/Guard150/ScanOdomClock300, STOP/SLOW polygons, CPU affinity as original unmodified.

## 4. S1 진단 단 한 번의 실제 시뮬레이션 Goal 계약
1. 먼저 공개 CI pre-Goal strict source and public test bindings, actual Jazzy TF ABI, C05/CM callback pretrace setup, simulation-only conditions fail-closed GREEN. Any preGoal failure => NO Goal.
2. 그 후에만 exact **one** bounded original Waffle/Nav2/Gazebo Moving Goal, first CM source gap & observer, safety first states, same PID·TID TF function interval. S02 contact0, STOP, odom>=1s, Goal Cancel and Navigation/Localization ACK are independent same-run gates, not override.
3. `TF_ADV` intervals missing, raw trace >bounds, mapping/clock ambiguous or RMW first gap not reproduced ⇒ `CAUSE_UNPROVEN`. TF dominant elapsed ≠ proven TF blocking. **Gate C unauthorized** without direct actionable cause proof.
4. After single actual run (PASS/FAIL), retire **only temporary S1 workflow trigger** on public release branch. Never re-trigger same diagnostic Goal automatically, never run on Owner WSL2. Preserve exact Actions URL/output, CI SHA, first failed boundary in this report and public Draft PR.

## 5. 교육용 사례 문제
- 공식 30Hz TF 사례 최대 33ms를 100Hz AXIA 실제 138ms 공백의 원인으로 곧바로 치환하면 왜 오류인가?
- `source_timeout=1.0` vs Guard TTL0.15, Scan TTL0.3과 `stop_pub_timeout`는 어떤 서로 다른 계층인가?
- TF 함수 내부 `thread_cpu < wall`이 실제 `lookupTransform` 대기인지 scheduler preemption인지 구분하려면 무엇이 더 필요한가?
- 한 진단 run에서 Localization Shutdown FAIL이면 왜 CM output latency 원인도 localization이라고 할 수 없는가?

## 6. 결과 기록 (S1 preflight/actual Goal 이후 채움)
```text
S1_OFFICIAL_RESEARCH=VERIFIED_NAV2_JAZZY_DOC_SOURCE_ISSUE3402_PR3412
S1_MOVING_GOAL=REAL_ONE_DIAGNOSTIC_EXECUTED
S1_ROOT_CAUSE=UNPROVEN
GATE_C=BLOCKED_CAUSE_UNPROVEN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
OWNER_WSL2_L3=NOT_RUN
MAIN_MERGED=false
```


## 7. S1 실제 Gazebo Harmonic/Jazzy/Nav2 Moving Goal 1회 — 원본 측정 결과

**공개 CI [Run #44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816), job 133797884405, completed FAILURE**. Release temporary workflow SHA `e684c1f6f46f0d5462dce8e93891a909af090176`, original Instructor SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public C05/S0 TF shim source `ec059007670c0a5c1c13b0fe7d06ad1107f2e1d6`, official Jazzy runtime digest `sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e`. New features/official Nav2 code/CM/Guard/TF/safety policy **변경 0**. S1 Goal **실제 단 한 번 수행**; 이 뒤 동일 조건 반복 금지.

### 첫 120ms 위반을 기준으로 한 동시 계측
원본 필터·callbacks·TF interval은 기존 S0가 수정한 동일 subprocess에서 계측됨:
```text
AXIA_G07_FIRST_CM_SOURCE_GAP_SCHEDULER_WINDOW
  first_cm_source_gap_ms=139.723543
  first_cm_observer_callback_gap_ms=123.527663
  upstream_publications_inside_source_gap=3
  scheduler_samples_in_first_gap=2
  scheduler_sample_coverage_ms=57.036824
  scheduler_run_delta_ms=1.095760
  scheduler_wait_delta_ms=4.942960
  status=FIRST_CM_120MS_GAP_SCHEDULER_VS_EXECUTION_UNDETERMINED

AXIA_G07_S0_ACTUAL_CM_CALLBACK_FILTER_COUNTS
  raw_examined=110297
  accepted_cm_callback_count=2700
  cm_metadata_count=24
  status=EXACT_CM_CALLBACK_FILTER_READY

AXIA_G07_C05_FIRST_CM_CMD_CALLBACK_DIAGNOSTIC
  first_cm_rmw_source_gap_ms=139.723543
  first_cm_observer_wall_gap_ms=123.527663
  matched_cm_cmd_callback_count=2
  max_matched_cm_cmd_callback_duration_ms=102.456878
  max_callback_overlap_first_gap_ms=102.456878
  official_cm_topic_to_callback_link_proven=true
  trace_clock_domain=LTTNG_WALL_EPOCH_MAPPED_MONOTONIC
  status=CM_INPUT_CALLBACK_INTERVAL_OBSERVED_HYPOTHESIS_ONLY

AXIA_G07_CM120_GATE_B_REAL_TF_CALLBACK_TIME
  first_cm_rmw_source_gap_ms=139.723543
  first_cm_observer_gap_ms=123.527663
  cm_callback_wall_ms=102.456878
  tf_function_wall_ms=101.682875
  tf_thread_cpu_ms=0.322830
  cpu_vs_wall_difference_ms=101.360045
  tf_wall_fraction_of_callback=0.9924
  other_elapsed_upper_ms=0.774003
  matched_tf_calls=1
  actual_tf_function_interval_recorded=true
  status=TF_FUNCTION_DOMINANT_WAIT_CAUSE_UNPROVEN
  tf_wait_proven=false
  scheduler_wait_proven=false
  root_cause_proven=false
  gate_c_authorized=false
  cm120_release_pass=false
```

**이제 확인된 사실:** 첫 위반 구간과 동일 공식 CM `/cmd_vel_supervised` 콜백의 실행시간 **102.457ms** 중 `nav2_util::getTransform` Advanced 호출의 wall time **101.683ms**, 즉 **99.24%**를 직접 측정했다. TF 함수 내부 thread CPU time은 **0.323ms**이며 wall-CPU 차이는 **101.360ms**. 앞선 S0 10만 이벤트 중단을 실제 >110k 원본 이벤트 필터링으로 회귀 해결했다. PID/TID/Callback 및 monotonic clock 일치 확인을 거쳤다. 이 실측은 Nav2 Issue #3402의 Advanced TF 경로 지연 선례와 같은 방향의 강한 단서다.

**여전히 확정되지 않은 사실:** TF 함수 **내부** 101.36ms 비CPU 시간에 대한 `tf2 Buffer::lookupTransform` 기다림 vs OS thread deschedule/preemption vs 기타 middleware 대기 분리. 기존 proc scheduler samples2/coverage57ms로 first gap139ms 전체를 설명할 수 없음. 따라서 `TF_FUNCTION_ELAPSED_DOMINANT=PROVEN`이지만 `TF_WAIT_ROOT_CAUSE=UNPROVEN`. 본 source_timeout/transform_tolerance/CPU/TF policy를 추정 변경하지 않는다. 임의 TF simple 모드 배포 금지.

### 같은 Goal의 시연/안전·후처리 확인
```text
AXIA_G07_CI_MEASURED_MESSAGE_PERIODS
  clock=0.104360598
  cm=0.123527663
  guard=0.064869509
  odom=0.112332674
  scan=0.201726819
  source=0.076274317
  supervisor=0.076299686

AXIA_G07_PUBLIC_CI_MOVING_GOAL_CLEAR_SLOW_STOP_ODOM_PASS
  displacement_m=0.1957
  stopped_dwell_s=1.001

AXIA_G07_NAV2_EXACT_GOAL_CANCEL_ACK_BEFORE_SHUTDOWN
  status=CANCELED

G07_NAV2_ORDERED_SHUTDOWN
  navigation_ack=true
  localization_ack=true
  navigation_elapsed_sec=2.896142
  localization_elapsed_sec=0.305263
  status=NAV2_LIFECYCLE_SHUTDOWN_ACK

AXIA_G07_OWNER_SHUTDOWN_AUDIT
  cm_exit_code=0
  status=SHUTDOWN_CLEAN_CANDIDATE

AXIA_S02_SAME_GOAL_NATIVE_CI_REVIEW
  native_positive_contacts=0
  native_observed_iterations=30159
  status=CI_S02_SAME_GOAL_NATIVE_CONTACT_ZERO_CANDIDATE

AXIA_G07_PUBLIC_CI_WSL2_MATCHED_14_TOPIC_REAL_BAG_L2_PASS
AXIA_G07_REAL_POST_GOAL_OWNER_IDENTICAL_NAV2_SHUTDOWN_CM_EXIT0_PASS

AssertionError: FIELD_CI_L2_PASS_LOW_MARGIN_OWNER_NOT_READY
```
- Clock/Odom/Scan 메시지 최대 *전달 간격*은 이번 Goal에서 각 300ms보다 짧다. Guard message interval 64.87ms는 Guard **내부 CM age**가 150ms 아래였다는 동등 증거가 아니다. 첫 Guard Latch 진단 `NO_FIRST_GUARD_LATCH_TRACE` (이 run에서 첫 내부 래치 존재 증명 없음), 과거 Owner 150ms 위반과 혼합 금지.
- 원래 주행 CLEAR→SLOWDOWN→STOP, CancelGoal CANCELED, STOP/odom dwell, S02 native contact0 **CI 한정 후보**, 14 topic 증거, Navigation/Localization shutdown ACK, CM exit0 확인. 전체 인수는 **CM120 source139.724ms 및 Observer123.528ms 위반으로 FAIL**. 계측된 진단용 Goal은 tracer on이므로 본래 성능 릴리스 PASS로 사용하지 않는다.

### Gate C/D 진행 판단
- Official Jazzy `nav2_util/src/robot_utils.cpp`에서 Advanced `tf_buffer->lookupTransform(target_frame_id,target_time,source_frame_id,source_time,fixed_frame_id,transform_tolerance)`를 직접 확인했다. 이 호출 경로가 장시간 wall-time 대부분을 차지하되, 내부 OS scheduling 대기인지 TF buffer blocking인지는 여전히 구분 필요.
- **진단 결과는 Gate C 설정 변경을 자동 허가하지 않는다**: `root_cause_proven=false`, `gate_c_authorized=false`. 우선 진단 source/run 타임라인을 보존하고 TF availability와 callback thread scheduler wait을 최소 범위에서 분리할 방법을 검토해야 한다. 이 때도 변경 변수 하나만, 기존 공식 Nav2 재사용/안전 공간 오차 검증, 별도 승인 및 공개 CI GREEN 전 Owner 현장 재시도 금지.
- Gate D tracer OFF 본래 Moving Goal 완전 통합 L2 및 Owner WSL2 L3 **NOT_RUN**, main 병합 **NO**.
- 단발 실행기 `.github/workflows/axia-g07-cm120-four-gate-one-diagnostic-l2.yml`는 실제 Run 확인 후 **public release에서 제거**: cleanup commit `51673ae942e18d00b6dd8bd5b9a80de308409c30`. S1 개발 branch의 원본 변경 없음. 공개 Draft PR #155는 연구/보고서만 보존.

## 8. S1 RED→GREEN→REFACTOR→REVIEW→COMMIT 기록 및 교육 활용
- S0 진단기 최초 RED [#44007105539](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44007105539) `FILTERED_CM_TRACE_UNBOUNDED_HOLD`/shim loader unverified. S0 수정 전 source baseline `00ab632b51d1cae6aec254d440253e4f6b44cbe6`, 이후 public S0 L0 [#44009950139](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44009950139) GREEN4+3+2, live NO_GOAL [#44009454224](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44009454224) 337 TF_ADV+Navigation/Localization ACK, S1 actual single Goal 앞서 official config and issues review. **S1은 새로운 product fix cycle이 아닌 보정된 진단기 실측 단계**라 제품 코드에 대한 새 RED→GREEN을 허위 기록하지 않는다.
- Paths `d06/diagnostic/{cm_tf_gettransform_preload.cpp,s0_cm_diag_readiness.py,analyze_first_cm_tf.py}`, `d06/live/g07_cycle05_cm_callback_window.py`, `d06/tests/test_g07_cm120_s0_diag_runner_contract.py`, workflow and this document. 실행 명령 전체는 실제 공개 Actions workflow source에서 유지; WSL2 재실행 명령은 **미배포**. Private Instructor SHA 및 source 변경 없음.
- 강의 질문: 콜백 102.457ms 중 TF 101.683ms를 측정했는데도 왜 TF buffer wait 인과 결론을 내릴 수 없는가? 프로세스 TF 함수 wall=101ms·CPU=.323ms로 OS scheduler 선점을 어떻게 배제할 것인가? S1 진단 모듈을 켠 120ms release FAIL을 그대로 출고 성능 평가에 사용할 수 있는가? 120ms criterion을 맞추기 위해 safety TTL·TF motion compensation을 완화하면 왜 위험한가?

```text
AXIA_G07_S1_MOVING_GOAL=REAL_ONE_DIAGNOSTIC_EXECUTED
AXIA_G07_S1_OFFICIAL_RESEARCH=JAZZY_DOCS_ISSUE3402_PR3412_CONFIRMED
AXIA_G07_S1_CM_SOURCE_FIRST_GAP_MS=139.723543
AXIA_G07_S1_CM_CALLBACK_WALL_MS=102.456878
AXIA_G07_S1_ADVANCED_TF_FUNCTION_WALL_MS=101.682875
AXIA_G07_S1_ADVANCED_TF_FUNCTION_THREAD_CPU_MS=0.322830
AXIA_G07_S1_TF_FUNCTION_ELAPSED_DOMINANT=PROVEN
AXIA_G07_S1_TF_BUFFER_WAIT_VS_OS_PREEMPTION=UNPROVEN
AXIA_G07_S1_EVENT_FILTER=PASS_110297_TO_2700
AXIA_G07_S1_GOAL_CLEAR_SLOW_STOP_ODOM=PASS_DIAGNOSTIC_ONLY
AXIA_G07_S1_NATIVE_CONTACT_ZERO=CI_CANDIDATE
AXIA_G07_S1_NAV_LOCALIZATION_SHUTDOWN=ACK_ACK
AXIA_G07_S1_PUBLIC_CI_CONCLUSION=FAIL_CM120_HEADROOM
AXIA_G07_GATE_C=NOT_STARTED_ROOT_CAUSE_UNPROVEN
AXIA_G07_GATE_D=NOT_STARTED
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```
