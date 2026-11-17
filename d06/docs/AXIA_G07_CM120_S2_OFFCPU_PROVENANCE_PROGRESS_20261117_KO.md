# AXIA G07 S2 — 공식 Advanced TF 함수 내 비CPU 101ms 분류·진단기 검증 경과

## 인수 기준과 원본 증거
**변경 대상은 진단기만**: 원본 공식 Jazzy Collision Monitor, Nav2, TurtleBot3 Waffle, Gazebo Harmonic, Instructor Safety Supervisor/Guard/Fault Injector/Verifier, stop polygon/TTL은 모두 변경하지 않는다. S1 first true Moving Goal [#44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816) exact same LTTng callback/publisher RMW: CM first source139.723543ms, Observer123.527663ms; CM callback102.456878ms, advanced TF function101.682875ms, thread CPU0.322830ms, 비CPU101.360045ms. S1 Diagnostics on, CI overall FAIL CM120, not release pass.

## 원인 후보와 공식 근거
- Linux Kernel `/proc/thread-self/schedstat` has thread CPU runtime, **runqueue ready wait**, timeslices. Kernel docs: https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html . **Only** if `/proc/sys/kernel/sched_schedstats=1` can runqueue wait be interpreted as a valid quantitative counter; 0 is UNKNOWN, not zero scheduler wait.
- Linux `getrusage(RUSAGE_THREAD)` voluntary vs involuntary context switches, count only not duration: https://man7.org/linux/man-pages/man2/getrusage.2.html .
- Official **Jazzy** `tf2_ros/src/buffer.cpp`: https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp advanced lookupTransform→canTransform poll loop calls `std::this_thread::sleep_for(std::chrono::milliseconds(10))` until transform ready or timeout, not necessarily CPU execution. Original Nav2 Jazzy helper: https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_util/src/robot_utils.cpp delegates to tf_buffer->lookupTransform with time correction and configured tolerance.
- Strong hypothesis: ~101ms nonCPU may include real TF polling `sleep_for(10ms)`; does NOT prove that every offCPU ns is TF wait, and callback/TF long elapsed can include descheduling, runqueue, locks, ROS sim clock. Official Issue #3402 and merged PR #3412 are similar upstream cases, but not AXIA proof.

## TDD cycle S2-1 — first runqueue measurement opportunity
- Baseline pre-S2 public S1 pinned `eab2527f5016ff9433f88241c9ac6806ed1f02c0`. RED: S1 TF_ADV reports wall/CPU only; source has **no schedstat fields** and no offCPU classifier.
- RED tests `d06/tests/test_g07_cm120_s2_offcpu_classification.py` 5 cases commit `46818d16e4d3deb52ccc56c7ba96bb2108cc5639`. GREEN new pure classifier `d06/diagnostic/classify_tf_non_cpu.py` commit `cc5677a99e5436df7c3c339abb045380c5fa7367`.
- Minimal extension existing real C++ diagnostic `d06/diagnostic/cm_tf_gettransform_preload.cpp` commit `3d09901bcfd7de75e899e57e716a98cdd6508c77`, report only RUSAGE_THREAD voluntary/involuntary + per-thread schedstat runqueue delta when kernel flag explicitly 1, original Advanced TF delegation unchanged. S1 first-gap analyzer accepts optional fields `d06/diagnostic/analyze_first_cm_tf.py` commit `cf57f67f31721af9f7adfefbfab6d59fb363e92d`; S1 legacy test preserved.
- Real public [L0 #44012856210](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44012856210) **completed SUCCESS**: S1 RED, 5+4+3 unit GREEN, original Jazzy ABI compile and RTLD_NEXT PASS, NO_GOAL. **Actual kernel `sched_schedstats=0`**, `/proc/thread-self/schedstat` 3 fields present but runqueue wait *NOT VERIFIED*, so pure scheduling quantitative attribution blocked, no sysctl mutation. Observed marker `AXIA_G07_S2_RUNQUEUE_NANOSECONDS_NOT_VERIFIABLE_NO_GOAL_HOLD`.

## TDD cycle S2-2 — minimal direct tf2 poll sleep observation (kernel independent)
- Official tf2 Jazzy uses `std::this_thread::sleep_for(10ms)`; rather than enabling kernel accounting/perf/BPF/ptrace or changing official CM, existing simulation-only LD_PRELOAD shim adds **thread-local** wall-time/count of libc `nanosleep` and `clock_nanosleep` only during exact official Advanced TF function invocation. Delegates original libc via `RTLD_NEXT`, preserving return, errno and clock semantics; suppresses nested double counting.
- Exact synthetic tests `d06/tests/test_g07_cm120_s2_actual_sleep_provenance.py` GREEN3 including sleep-dominant without schedstats, missing sleep HOLD and impossible sleep>offCPU HOLD, and 5+4+original3. Pure matcher cannot promote Gate C or CM120 PASS. Original C++ module also exposes **NO_GOAL `std::this_thread::sleep_for` selftest** (rather than merely checking symbol existence).
- Public L0 [#44013410740](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013410740) **completed SUCCESS**:
```text
AXIA_G07_S2_RED_ORIGINAL_S1_NONCPU_UNATTRIBUTED_CONFIRMED
Ran 5 tests ... OK
Ran 4 tests ... OK
Ran 3 tests ... OK
Ran 3 tests ... OK
AXIA_G07_S2_REAL_CXX_SLEEP_FOR_INTERPOSITION_L0_GREEN_NO_GOAL
AXIA_G07_S2_OFFICIAL_ADVANCED_TF_ORIGINAL_ABI_L0_GREEN_NO_GOAL
kernel_sched_schedstats = 0
AXIA_G07_S2_RUNQUEUE_NANOSECONDS_NOT_VERIFIABLE_NO_GOAL_HOLD
```
- One-off S2 real original Jazzy/Harmonic/Nav2 **NO_GOAL** workflow `.github/workflows/axia-g07-cm120-s2-real-nogoal-sleep-probe-l2.yml`, source pin `9bcdc5cb92ff4da61efb2eba1d2fd77c30dfff96`, private Instructor original pin `966886c4627deb2bb3b37111fe336eeee6b9ebb4`; actual [Run #44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608) **PENDING** when this draft written. Must verify actual CM `TF_ADV` extended fields, CM mapped, noGoal, Navigation/Localization ACK/rc0 before another Goal. No result fabricated.

## S2-3 — conditional single Moving Goal (DO NOT RELEASE YET)
- Dev-only future workflow `.github/workflows/axia-g07-cm120-s2-one-diagnostic-moving-l2.yml` added, original C05/C37 official one Goal, original contact0/STOP/dwell/cancel/lifecycle, existing LTTng same-PID/TID first-gap matching reused; pins source `9bcdc5cb92ff4da61efb2eba1d2fd77c30dfff96` and Instructor `966886c4627deb2bb3b37111fe336eeee6b9ebb4`.
- Send **at most one** real Goal if S2 NO_GOAL probe & exact ABI/TF tests L0 PASS, never trigger on prereq FAIL. Its diagnostics do not prove release performance because tracing changes timing; no safety parameters changed. If no >120ms initial source gap, parser/TF sleep attachment missing, kernel runqueue unavailable and libc sleep absent, verdict `CAUSE_UNPROVEN`; no accidental Gate C.
- Actual Moving Goal **NOT RUN as of this draft**. Final status must be updated from immutable Actions run, never infer success from CI YAML or pure tests. One-off release workflows removed after verdict (keep source dev workflow, don't touch other agents' work).

## Verification/branch/handoff
- Branch `fix/g07-cm120-s2-offcpu-provenance-20261117`, public Git commits above; private Instructor/student untouched; main not merged.
- This report is educational evidence, including first source timing violation, actual stdout, verification level, unverified items, SHAs, and stoppage boundaries.
- Same goal Safety: CM source+Observer <=120ms, Guard internal <=150ms, Scan/Odom/Clock <=300ms, CLEAR/SLOWDOWN/STOP, S02 contact0, odom zero dwell>=1s, CancelGoal ACK, Navigation/Localization ACK, CM exit0, original 14-topic raw evidence. Stop is software, not certified E-Stop.
```text
S2_KERNEL_SCHEDSTAT=DISABLED
S2_PURE_L0=GREEN_15
S2_FIRST_TF_OFFCPU_CAUSE=UNPROVEN
GATE_C=NOT_STARTED
GATE_D=NOT_STARTED
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```


## S2-2 실제 공식 Jazzy/Harmonic/Nav2 NO_GOAL L2 결과 — GREEN

**Public [Run #44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608), completed SUCCESS**, original private SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public S2 tested source pin `9bcdc5cb92ff4da61efb2eba1d2fd77c30dfff96`, actual one-off release trigger `65769ad477d61215e925005dc2d9fbf0ffd7d0a1`. NO_GOAL runner rc0; after completed, retired only one-off NO_GOAL workflow release commit `9947b8ab15b566ffb963029bc279e737c681da71`. No Goal or CM configuration change.
```text
AXIA_G07_S2_CM_PRELOAD_MAP_OBSERVED=1
AXIA_G07_S2_REAL_NO_GOAL_CM_TF_READINESS {
  "actual_tf_call_count":477,
  "tf_nanosleep_calls_total":427,
  "tf_actual_sleep_wall_ms_total":4399.656895,
  "process_mapping_proven":true,
  "tf_call_observed":true,
  "startup_status":"SMOKE_READY",
  "goal_sent":false,
  "localization_shutdown_status":"NAV2_LIFECYCLE_SHUTDOWN_ACK",
  "navigation_ack":true,
  "localization_ack":true,
  "runner_rc":0,
  "root_cause_proven":false,
  "release_pass":false,
  "owner_accepted":false,
  "certified_estop":false
}
AXIA_G07_S2_REAL_CM_LOADER_AND_LOCALIZATION_NO_GOAL_PASS
AXIA_G07_S2_TF_FUNCTION_CALLED_NO_GOAL_DIAGNOSTIC_NOT_RELEASE
AXIA_MVP_DEMO_ACCEPTED=HOLD
```
- **Proven**: official original CM process successfully loads diagnostic shim and intercepts actual libc sleep calls *while* Advanced TF wrapper active. 427 sleep intervals elapsed 4.399657 seconds **aggregated across 477 calls**.
- This is **NOT** same S1 first CM gap (different Run, NO_GOAL), and **NOT** proof that all the elapsed time is transform availability waiting: libc sleep wall includes potential scheduling delay after timer expiry. Do not attribute or divide 4399ms as a first-gap number.
- Existing original Navigation and Localization ACK both SUCCESS. NO_GOAL life-cycle pass does not prove post-Goal lifecycle stability.

## S2-3 single new Moving Goal status
- Because S2-2 real CM NO_GOAL loader/actual TF sleep hook was verified and S2 L0 unit+ABI passed, one source-pinned original diagnostic Moving Goal was registered [public Run #44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942), release trigger SHA `fe57ee49edcde2b7a03080177b8148f917486cf2`. **completed FAILURE**, actual one Moving Goal executed; full result below. Do not rerun. This S2 Goal differed from S1 by tested trace instrumentation and sleep-for context collection.
- Future output requires `AXIA_G07_S2_FIRST_CM_TF_OFFCPU_PROVENANCE`: SAME first failed CM RMW source gap→topic-specific official CM callback PID/TID→Advanced TF function→libc sleep intervals, plus Guard/Scan/Odom/Clock, Collision0, Stop/CANCEL/Shutdown, original14 topic. Even if TF sleeps dominate, `root_cause_proven=false`, `gate_c_authorized=false` until standalone causal attribution/safety fix.


## S2-3 실제 원본 Moving Goal 1회 — SOURCE GAP 미재현, Observer 120ms 위반, Localization 종료 실패

**Actual [public Run #44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942), job 133807789938, completed FAILURE**. One-off release commit `fe57ee49edcde2b7a03080177b8148f917486cf2`, original Instructor `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, S2 probe source `9bcdc5cb92ff4da61efb2eba1d2fd77c30dfff96`. Exactly **one** diagnostic Moving Goal; old source, CM/Guard TTL, Nav2 mode/params unchanged. Retired only this release one-off workflow after job completion in commit `b199c72ff5e4f918a35385758d5f187d90579aaa`.

### 최초 타이밍 위반 및 S2 직접 측정의 경계

```text
AXIA_G07_FIRST_CM_SOURCE_GAP_SCHEDULER_WINDOW
  status=NO_CM_SOURCE_GAP_OVER_120MS_IN_OBSERVED_WINDOW
  first_cm_source_gap_ms=null
  first_cm_observer_callback_gap_ms=null
  reason=NO_FIRST_GAP_SCHEDULER_PROOF

AXIA_G07_CI_FIRST_120MS_CM_SUPERVISOR_RMW_WINDOW
  status=NO_CM_SOURCE_GAP_OBSERVED
  cm_source_gap_sec=null
  upstream_publications_inside_gap=0

AXIA_G07_CI_MEASURED_MESSAGE_PERIODS
  clock=0.112780975
  cm=0.121776640
  guard=0.062292188
  odom=0.121693707
  scan=0.204252238
  source=0.091394802
  supervisor=0.091397720

AXIA_G07_S0_ACTUAL_CM_CALLBACK_FILTER_COUNTS
  raw_examined=125065
  accepted_cm_callback_count=2692
  cm_metadata_count=24
  status=EXACT_CM_CALLBACK_FILTER_READY

AXIA_G07_C05_FIRST_CM_CMD_CALLBACK_DIAGNOSTIC
  status=FIRST_CM_RMW_SOURCE_PAIR_UNVERIFIED_HOLD

AXIA_G07_C05_CM_CALLBACK_ROOT_CAUSE_UNPROVEN_HOLD
```

- **실제 CM Observer interval 최대 121.776640ms >120ms**. 하지만 `/cmd_vel_pre_guard` RMW source에서 >120ms first pair가 관측되지 않아 기존 S1 분석기의 단일 실패 창에 해당하는 동일 CM callback/TF/sleep pairing을 실행하지 못했다. `source gap not observed`를 `source <=120ms PASS`로 확대하지 않으며 source/Observer 두 계약 모두 통과했다고 주장 금지.
- 기존 S0 10만 이벤트 overflow는 **이 실행에서도 해결** (raw125065 이벤트→exact 콜백2692). 그러나 첫 RMW source breach가 없어 분석기가 `FIRST_CM_RMW_SOURCE_PAIR_UNVERIFIED_HOLD`로 정확히 실패했다. 따라서 `AXIA_G07_S2_FIRST_CM_TF_OFFCPU_PROVENANCE`는 **출력되지 않았고 S2 최초 초과 창 정량 분류는 실패**. Private raw TF events는 post-CI cleanup됨; public run artifacts **0건**. NO_GOAL aggregate sleep4399.657ms를 이 Goal 첫 위반에 대입 금지.
- Original official Waffle/Gazebo/Nav2 moving CLEAR→SLOWDOWN→STOP, displacement0.1921m, odom stopped dwell1.015sec, native STOP request duration0.105846sec, nav Goal CANCELED 확인. **하위 Safety TTL 전체 인수는 미충족**: Guard message interval62.292ms는 Guard internal CM age150ms 검증이 아니며, `AXIA_P4_G07_L2_FIRST_CM_GUARD_BOUNDARY` returned `NO_FIRST_GUARD_LATCH_TRACE`. Native 0 contact + 14-topic raw custody postGoal combined PASS 실패로 이 Goal의 통합 인수 근거가 아님.
- **독립 Lifecycle first failure**, Navigation ACK true elapsed2.64552sec; Localization managed service request_sent=true, after25.000516sec ACK=false; AMCL+map_server active, localization manage service advertised, `LOCALIZATION_SHUTDOWN_REQUEST_SENT_ACK_TIMEOUT` → `BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT`. Same problem as previous #44007105539 but not the cause of first CM Observer interval breach. Neither force timeout increase nor retry Goal.
- Important: `CM 120ms release FAIL` in real **Observer 121.777ms** and overall CI FAILURE; the S2 trace-on diagnostic is not a release performance measurement.
- **One Goal allowed/used; no repetition**. All code changes remain CI-only diagnostic and reports; original Nav2/Safety/Instructor/Student untouched.

### S2 도달 가능한 원인 분류 판정 (과잉 결론 금지)

**직접 입증**:
- Original S1 one actual Moving Goal [#44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816) had first CM RMW source139.723543ms and exact advanced TF wall101.682875ms of callback102.456878ms; nonCPU101.360045ms.
- Original S2 actual NO_GOAL [#44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608) same official CM sim process recorded advanced TF calls477 and **actual within-function nanosleep427 / aggregated sleep4399.656895ms** (not first source violation).
- Original Jazzy tf2_ros::Buffer::canTransform advanced polling code uses `sleep_for(10ms)`; this mechanism is indeed plausible. Kernel `sched_schedstats=0` means S2 cannot directly quantify runqueue ready-queue preemption in current CI. No sysctl modifications.

**미확정**:
- S1 first CM source gap139.724ms **안에서** tf2 sleep vs scheduler precise partition was **not captured in the same run**, because S1 lacked sleep counters and S2 did not reproduce first RMW source breach.
- Whether tf2 Buffer transform availability wait, per-thread CPU preemption, clock tick quantization or a combination is the *dominant causal reason for the 120ms release failure* remains **UNPROVEN**; NO_GOAL aggregate sleep doesn't prove same first-gap cause.
- No Gate C tuning (TF mode, transform tolerance, source timeout, CPU affinity, safety TTL) allowed from this evidence. No Gate D tracer-OFF same-run full release Green, no Owner WSL2 acceptance, no main merge.

### RED→GREEN→REFACTOR→REVIEW→COMMIT cycle summary
- RED original S1 instrument lacked scheduler/sleep context; synthetic S2 RED commit `46818d16e4d3deb52ccc56c7ba96bb2108cc5639`.
- GREEN pure 5 offCPU +4 exact first-window+3 legacy S1+3 sleep cases, true Jazzy ABI and C++ `sleep_for` interposition: [public L0 #44013410740](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013410740) completed SUCCESS. Prior pure kernel capability [#44012856210](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44012856210) completed SUCCESS but kernel schedstats0.
- Real official NO_GOAL S2 [#44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608) completed SUCCESS. Real moving single goal S2 [#44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942) completed **FAIL** first-source gap absent / Observer121.777ms and first Localization ACK timeout; trace once verified but no exact gap classification.
- REFACTOR: only CI-only `d06/diagnostic/cm_tf_gettransform_preload.cpp` same-ABI wrapper, `d06/diagnostic/classify_tf_non_cpu.py`, `d06/diagnostic/analyze_first_cm_tf.py`, exact negative unit regressions; no production CM/Nav2 changes.
- REVIEW: no sensor safety regression from tuning because no tuning; real S2 moving source first-gap classification unverified. COMMIT: public plan/this education report and Draft PR #156 preserved. No exported raw PID/poses/Instructor answer.
```text
AXIA_G07_S2_OFFCPU_HYPOTHESIS=TF_FUNCTION_REAL_SLEEP_POLL_OBSERVED_NO_GOAL
AXIA_G07_S2_KERNEL_RUNQUEUE_ACCOUNTING=DISABLED
AXIA_G07_S2_FIRST_CM_SOURCE_GAP_MATCH=NOT_REPRODUCED_IN_ONE_GOAL
AXIA_G07_S2_OBSERVER_MAX_GAP_MS=121.776640
AXIA_G07_S2_LOCALIZATION_FIRST_ERROR=LOCALIZATION_SHUTDOWN_REQUEST_SENT_ACK_TIMEOUT
AXIA_G07_S2_REAL_MOVING_GOAL=EXECUTED_ONCE_CI_FAILURE
AXIA_G07_S2_FIRST_SOURCE_GAP_SLEEP_VS_SCHEDULER=UNPROVEN
AXIA_G07_GATE_C=NOT_STARTED
AXIA_G07_GATE_D=NOT_STARTED
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```
