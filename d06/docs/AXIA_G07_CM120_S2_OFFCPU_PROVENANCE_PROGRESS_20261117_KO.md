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
- Because S2-2 real CM NO_GOAL loader/actual TF sleep hook was verified and S2 L0 unit+ABI passed, one source-pinned original diagnostic Moving Goal was registered [public Run #44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942), release trigger SHA `fe57ee49edcde2b7a03080177b8148f917486cf2`. **PENDING at this note**; do not infer actual Goal or result before immutable logs.
- Future output requires `AXIA_G07_S2_FIRST_CM_TF_OFFCPU_PROVENANCE`: SAME first failed CM RMW source gap→topic-specific official CM callback PID/TID→Advanced TF function→libc sleep intervals, plus Guard/Scan/Odom/Clock, Collision0, Stop/CANCEL/Shutdown, original14 topic. Even if TF sleeps dominate, `root_cause_proven=false`, `gate_c_authorized=false` until standalone causal attribution/safety fix.
