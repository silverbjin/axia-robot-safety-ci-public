# AXIA G07 CM120 — 4-Gate 원인 우선 개발·디버깅 교육용 경과보고서

## Gate A — 최초 실패 증거 재판정 [완료: 부분 증명]
- Baseline original private Instructor SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public original C05 tool `202b66eb49001e59a06adecb70dde67a457f0780`, same actual Gazebo Harmonic/Jazzy Nav2 one-Goal [Run #43995793080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995793080).
- Live first CM `/cmd_vel_pre_guard` RMW publisher source gap **120.172578ms**, external Observer gap **120.523837ms**, exact real official `/cmd_vel_supervised` C++ callback handle wall elapsed / overlap **81.972669ms**. Two more upstream Supervisor source messages in that gap, CM output seq delta=1. This is *not* a direct per-message input→callback→output pairing.
- The original private `tools/p2_l3_live_session.py` records the observer's `supervised`, `pre_guard` RMW MessageInfo `rmw_source_ns`/`rmw_received_ns`/`rmw_publication_seq`, and the original `tools/p2_g07_ci_moving_goal_oracle.py` compares within-domain gaps. Live actual logger `actual_ros_events.jsonl` existed in the runtime but is absent from Actions artifacts (**0 artifacts** on Run #43995793080); original cleanup deletes local trace. GitHub job log retains only aggregate first boundary, not raw per-message records. Cannot reconstruct exact 1:1 pairing offline. **Gate A=FIRST_CM_GAP_CONFIRMED_ROOT_CAUSE_UNPROVEN.**
- Original official Jazzy `nav2_collision_monitor/src/collision_monitor_node.cpp` invokes `cmdVelInCallbackStamped → process → source->getData → publishVelocity`. `src/scan.cpp` invokes `Source::getTransform`; `nav2_util::getTransform` advanced overload uses source and target times. CM zero publication may be suppressed after `stop_pub_timeout` when already stopped. C05 first 120ms occurred during actual moving window; no independent evidence ZERO suppression caused that first gap. Do not attribute to it.
- First **actual** Gate A verdict: source RMW publish gap proven, exact CM callback duration is a large possible contributor, TF call wall/CPU/scheduling/other processing time unmeasured. No parameter tuning authorized, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

## Gate B — bounded diagnostic, no official production source changes
- User authorized **one** exact pinned public diagnostic moving simulation Goal only **after** a NO_GOAL L0 ABI preflight proves installed official advanced `nav2_util::getTransform` symbol can be transparently delegated by a CI-only userspace wrapper. Avoid custom Nav2 fork, kernel privilege/uprobes, new general profiler.
- Files: `d06/diagnostic/cm_tf_gettransform_preload.cpp`, `d06/diagnostic/CMakeLists.txt`, `d06/diagnostic/analyze_first_cm_tf.py`, tests `d06/tests/test_g07_cm120_tf_first_gap_join.py`, preflight workflow `.github/workflows/axia-g07-cm120-tf-shim-build-l0.yml`. Exact pins and runtime remain previous.
- Intended TF wrapper: intercept only official advanced overload, forward unmodified to `RTLD_NEXT`, record bounded per process/thread CLOCK_MONOTONIC, CLOCK_THREAD_CPUTIME_ID and return status; no ROS publisher, no sensor data or private position. On actual CM process only, public simulation only. Diagnostic execution instrumentation can bias timing; not a release benchmark.
- Gate B tests must prove same CM pid/tid and callback-to-TF event alignment with C05 LTTng and RMW source pair. TF wall cost alone **is not** proof of TF waiting vs OS preemption; script never grants `gate_c_authorized` from unmeasured scheduler data.
- First preflight [Run #44006345463](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44006345463) `completed/failure`, **before ROS/Goal**: CMake RED: `ament_target_dependencies` used plain signature but new CMake `target_link_libraries(... PRIVATE dl)` used keyword signature. First failure is `CMake Error at CMakeLists.txt:13`, not CM logic. Minimal one-line fix to plain `target_link_libraries(... dl)` commit `1cc5a8463d06508ed9656a2a3a6ad06f7cfb4957`. Revalidated ABI pending. Fail-fast prevents any moving Goal on unverified instrumentation.
- If direct TF shared-object linkage cannot be proven in L0, do not send Goal. If TF diagnostic itself fails, mark `CAUSE_UNPROVEN` and stop. Never repeatedly retry the same moving Goal.

## Gate C — one proven cause only [NOT STARTED]
No extra CM/Nav2/Guard/Supervisor source, CPU affinity, QoS, TF motion-correction, source_timeout=1.0, CM120/Guard150/ScanOdomClock300 or Stop zone parameter changes. At Gate B with confirmed actionable root do RED→GREEN→REFACTOR→REVIEW→COMMIT; otherwise STOP.

## Gate D — original tracer-OFF all-layer CI [NOT STARTED]
Only with Gate C proven Green. Same official C37 original Waffle/Harmonic/Nav2 one Goal; real first CM source+Observer <=120ms, Guard actual <=150ms, Scan/Odom/Clock <=300ms, S02 native Contact0, CLEAR/SLOWDOWN/STOP, odom zero dwell>=1s, original Goal Cancel and Navigation+Localization lifecycle ACK, CM exit0. Only **then** one Owner WSL2 final and separate user approval before main merge.

## 교육용 학습 요소
1. 소스 publication 간격과 Observer callback 간격을 각각 재고 RMW SYSTEM timestamps와 host-monotonic values를 직접 빼지 않기.
2. 81.973ms 콜백 elapsed가 TF `lookupTransform` 81.973ms 또는 스케줄러 runqueue 지연임을 증명하지 않는 이유.
3. CMake 링크 오류/원본 CI preflight와 실제 moving Safety TTL 오류의 최초 실패 분류.
4. TF 함수의 wall time 중 CPU vs non-CPU는 TF wait과 preempt를 구분하지 못하므로 fail-closed 인과 판정을 유지하는 방법.

```text
AXIA_G07_CM120_GATE_A=FIRST_GAP_CONFIRMED_ROOT_CAUSE_UNPROVEN
AXIA_G07_CM120_GATE_B=ABI_L0_PENDING_NO_GOAL
AXIA_G07_CM120_GATE_C=NOT_STARTED
AXIA_G07_CM120_GATE_D=NOT_STARTED
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

## Gate B 사전검증 실제 결과 — L0 GREEN, 실제 Goal은 별도

- 최초 CI [#44006345463](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44006345463) RED: `ament_target_dependencies` plain과 `target_link_libraries PRIVATE` 혼용. 최초 오류 `CMake Error at CMakeLists.txt:13`; ROS·Goal 시작 전 실패. 한 줄 변경 commit `1cc5a8463d06508ed9656a2a3a6ad06f7cfb4957`.
- 수정 뒤 실제 pinned Jazzy toolchain CI [#44006597068](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44006597068) **completed SUCCESS**:
```text
[100%] Linking CXX shared library libaxia_g07_cm120_tf_diag.so
AXIA_G07_CM120_OFFICIAL_ADVANCED_TF_ABI_INTERPOSITION_L0_PASS_NO_ROS_NO_GOAL
AXIA_G07_CM120_DIAGNOSTIC_ONLY_L0_PASS_NOT_RELEASE
```
- 시간창·Clock negative cases 추가 CI [#44006795555](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44006795555) **completed SUCCESS**, same source SHA `35abdbef803e08de14d0ffc955bf06ef478a56f0`:
```text
Ran 3 tests in 0.001s
OK
Ran 3 tests in 0.001s
OK
AXIA_G07_CM120_FIRST_GAP_TF_INTERVAL_JOIN_GREEN3_AND_C05_REGRESSION_NO_ROS_NO_GOAL
AXIA_G07_CM120_OFFICIAL_ADVANCED_TF_ABI_INTERPOSITION_L0_PASS_NO_ROS_NO_GOAL
```
- 신규 분석기는 실제 `cm` PID + vtid + C05 callback handle + same host-monotonic TF interval만 인정하고, 잘못된 프로세스·누락된 함수 호출·시계 offset drift를 fail-closed. **TF elapsed가 콜백을 대부분 차지해도 TF function wall 자체가 OS preemption을 포함할 수 있으므로 `tf_wait_proven=false`, `root_cause_proven=false`, `gate_c_authorized=false`로 고정**. 단일 진단만으로 확인 가능한 단계와 실제 원인 분리를 혼동하지 않는다.
- 사전검증이 통과한 뒤 Original C05 exact private `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public diagnostic `35abdbef803e08de14d0ffc955bf06ef478a56f0` 소스가 고정된 one-off 공개 진단 workflow `.github/workflows/axia-g07-cm120-four-gate-one-diagnostic-l2.yml`, trigger release commit `3332d7704bc6057f06ddcc15dd188d1188eabb2d`, actual [Run #44007105539](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44007105539) 시작.
- 이 **한 번의 실제 Goal 진단**은 원래 C05 LTTng, official Waffle/Nav2/Harmonic, original Stop·Contact0·CancelGoal·ordered shutdown·7-channel 120/150/300ms oracle을 그대로 재사용하되, original advanced TF 호출의 entry/end/CPU만 bounded LD_PRELOAD로 관측. 해석 결과나 CI status는 Run 완료 후 아래에 추가. Tracer-ON Goal은 릴리스 PASS 근거가 아니다.

## Gate B 실제 1회 진단 L2 종료 — 재실행 금지, 원인 미확정

**정확한 실제 Run:** [#44007105539](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44007105539); one-shot release SHA `3332d7704bc6057f06ddcc15dd188d1188eabb2d`, source-pinned private `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public diagnostic `35abdbef803e08de14d0ffc955bf06ef478a56f0`, pinned official Jazzy runtime container (계획 참조). **completed FAILURE**, exact original Moving Goal 1개 실제 실행. 더 이상의 동일 Goal 반복 금지.

### 최초 안전/타이밍 위반과 시연 성공 범위
실제 같은 Goal source/Observer:
```text
AXIA_G07_FIRST_CM_SOURCE_GAP_SCHEDULER_WINDOW
  first_cm_source_gap_ms=138.610710
  first_cm_observer_callback_gap_ms=138.523011
  cm_publication_seq_delta=1
  upstream_publications_inside_source_gap=2
  scheduler_samples_in_first_gap=3
  scheduler_sample_coverage_ms=102.800975
  scheduler_run_delta_ms=1.738167
  scheduler_wait_delta_ms=3.457718
  status=FIRST_CM_120MS_GAP_SCHEDULER_VS_EXECUTION_UNDETERMINED
AXIA_G07_CI_FIRST_120MS_CM_SUPERVISOR_RMW_WINDOW
  cm_source_gap_sec=0.138610710
  upstream_max_coverage_gap_sec=0.049967709
  upstream_publications_inside_gap=2
  status=CM_SOURCE_GAP_EXCEEDS_120MS
AXIA_G07_PUBLIC_CI_MOVING_GOAL_CLEAR_SLOW_STOP_ODOM_PASS
  displacement_m=0.1995
  stopped_dwell_s=1.01
AXIA_G07_FIELD_REAL_L2_SEVEN_CHANNELS
  clock=0.130568344,cm=0.138523011,guard=0.138406240
  odom=0.114534569,scan=0.213887068
  source=0.138056054,supervisor=0.138084846
AssertionError: FIELD_CI_L2_PASS_LOW_MARGIN_OWNER_NOT_READY
```
- 최초 CM **120ms release headroom** 실패는 실제 RMW source 간격138.611ms로 입증. Guard host interval max138.406ms는150ms, Scan interval213.887ms/Odom114.535ms/Clock130.568ms는300ms 이내였음. **Guard의 내부 receive age TTL 안전 인증과 동일하지 않다**. 독립 guard first-latch extractor는 `NO_FIRST_GUARD_LATCH_TRACE`를 보고, 최초 Guard stale latch를 이 실행에서 입증하지 않음. 이전 Owner >150ms 실제 실패와 이 Run의 수치를 합쳐 같은 실행으로 주장하지 않는다.
- 공식 Gazebo Waffle/Harmonic/Nav2 Moving Goal 실제 CLEAR→SLOWDOWN→STOP, native real STOP RPC duration0.118428초, front scan≈0.399m, CM/final vx=0, odom dwell1.01초 출력. 하지만 **완전한 인수는 FAIL**. post-goal S02 contact0/전체 shutdown proof는 함께 통과하지 못했고, 14-topic/CANCEL/CM exit0 전체 동시 인수도 주장할 수 없음.
- Step after Goal: Navigation lifecycle ACK=true elapsed1.809s. **최초 실제 shutdown 오류**는 `LOCALIZATION_SHUTDOWN_REQUEST_SENT_ACK_TIMEOUT` after25.000396s, AMCL/map_server both 'active', localization manage service advertised, localization ACK=false. Final `BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT`, not CLOCK_MISSING; 후속 RCL publisher-context invalid errors are teardown consequences. 이 종료 문제는 CM120 원인으로 확인되지 않았고 별도 수명주기 계층 문제로 유지.

### 진단기의 첫 오류와 계측 한계
- 실제 shell startup에서 한 번 `ERROR: ld.so: object '/tmp/axia_g07_cm120_abi/libaxia_g07_cm120_tf_diag.so' from LD_PRELOAD cannot be preloaded (cannot open shared object file): ignored.` 경고가 발생함. 직전 L0 preflight에서는 빌드 및 `RTLD_NEXT` 본래 함수 링크 PASS, actual step에서도 해당 파일 존재 검사 통과. **이 경고만으로 공식 CM 프로세스에 diagnostic hook가 로드됐는지 확증 또는 배제할 수 없다**. 동일 CM pid/tid의 함수 호출 원본을 확보하지 못함.
- Gate B 분석기는 **`AXIA_G07_C05_FILTERED_CM_TRACE_UNBOUNDED_HOLD`**로 종료. 원본 C05 LTTng 전체 이벤트 수가 100,000 limit을 초과했으며, 분석 전에 탈락. 이것은 **TF 함수가 오래 걸렸다는 결과가 아니라 계측 데이터 상한 초과**다. 당초 계획의 "bounded traces"와 실제 CM proc filtering/count 증명에 부족함이 있었음. Raw trace/TF event file은 비공개 CI cleanup으로 회수됐고 공개 artifact는 배포하지 않았음. TF duration, per-thread CPU, exact callback pairing **측정 실패**.
- 본 실행은 사용자 승인한 **단일 진단 Goal 1회**를 소비했으므로 동일 목표 재실행은 하지 않는다. 진단기 버그와 첫 localization timeout을 보고서·실제 GitHub CI Fail로 회귀 증거에 편입했고, 새 기능 또는 즉시 반복 주행 작업으로 확대하지 않는다.
- CI 검사 자체는 실패를 `PASS`로 승격하지 않음. Total job failures: (1) real Moving Goal step (localization ACK timeout), (2) C05 callback trace analysis (>100k), (3) CM120 release headroom 138.611ms, (4) post-Goal native 14-topic/Shutdown proof combined failure. 성격을 분리해 최초 증거부터 검토한다.

### 승인된 게이트 중단/후속 범위
- `Gate B=DIAGNOSTIC_EVIDENCE_UNVERIFIED`: original TF function 내부 wall vs CPU time 결과 없고, 선행 초과 CM output gap 138.611ms의 실제 root cause 역시 unproven. **Gate C는 시작하지 않는다**. `base_shift_correction=false`, `source_timeout` 변경, CPU affinity, CM output rate, TTL120/150/300 완화 모두 금지.
- `Gate D=NOT_STARTED`: tracer OFF 동일 원본 공개 CI 완전 통합 L2는 root cause/one-fix GREEN이 없어서 실행하지 않는다. Owner WSL2 L3 NOT_RUN; main not merged. Stop은 software STOP이며 인증 E-Stop이 아님.
- 앞서 성공한 original C05/C37 evidence를 보존하고 이번 CI의 실패를 별도 증거로 보존. 단발 public release trigger workflow는 **안전 폐기 cleanup commit `d0898e05bd1e951526962bf6ae4cbc13dfd0835f`**, 소스·계획·보고서·검증 workflow는 공개 Draft PR #152에서 추적.
- 과도한 확장 방지: 동일 Goal 재주행은 사용자 별도 결정이 있을 때만. 별도의 미리 검증된 NO_GOAL/L0 trace volume filter 및 localization service first-error contract까지 성공했다고 주장하지 않는다.

```text
AXIA_G07_CM120_GATE_A=FIRST_GAP_CONFIRMED_ROOT_CAUSE_UNPROVEN
AXIA_G07_CM120_GATE_B=FAIL_TRACE_UNBOUNDED_AND_HOOK_UNVERIFIED
AXIA_G07_CM120_GATE_C=NOT_STARTED_CAUSE_UNPROVEN
AXIA_G07_CM120_GATE_D=NOT_STARTED_NO_ONE_FIX_GREEN
CM120_FIRST_RMW_SOURCE_GAP_MS=138.610710
AXIA_G07_REAL_ONE_DIAGNOSTIC_GOAL=EXECUTED_ONCE
AXIA_G07_L2_LOCALIZATION_SHUTDOWN=FAIL_ACK_TIMEOUT_25S
CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_MOVING_L3=NOT_RUN
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
