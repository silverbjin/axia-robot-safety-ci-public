# AXIA G07 S2 — Advanced TF 내부 비CPU 시간 최소 원인 분리 (새 기능 Cycle 아님)

## 기준·승인
사용자 지시: "S2에서는 추가적인 성능 튜닝을 시작하기 전에 TF 함수 내부의 비CPU 시간을 한 번 더 분류하라." Goal 반복 및 CM 파라미터 튜닝이 아닌, **기존 S1 진단 함수 내 스레드별 scheduler/voluntary blocking 귀속**만 허용. 공식 Jazzy Nav2/TB3 Waffle/Harmonic/Guard 원본. No E-Stop certificate.

- S1 immutable public research + actual Goal [#44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816) report `d06/docs/AXIA_G07_CM120_S1_OFFICIAL_NAV2_RESEARCH_AND_SINGLE_DIAGNOSTIC_20261117_KO.md`, HEAD `eab2527f5016ff9433f88241c9ac6806ed1f02c0`; original private Instructor `966886c4627deb2bb3b37111fe336eeee6b9ebb4`.
- S1 actual same first CM RMW publisher gap=139.723543ms (>120), Observer=123.527663ms (>120), same official input callback=102.456878ms, Advanced `nav2_util::getTransform` wall=101.682875ms, thread CPU=0.322830ms, nonCPU=101.360045ms, 1 matched call, TF elapsed fraction=0.9924. **Only TF function wall is proven dominant**, no Buffer wait / scheduler causality proven.
- Original Guard 150ms, CM120ms RMW+Observer, Scan/Odom/Clock300ms, STOP0.40/SLOW0.75, source_timeout1.0, transform_tolerance0.02, base_shift_correction=true unchanged. Never claim tracer-ON is release performance test.

## 공식 코드 근거
1. Linux kernel schedstats per-task `/proc/thread-self/schedstat`: 3 fields nanoseconds CPU runtime, **runqueue wait**, timeslices (https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html). `sched_schedstats` tunable must be 1 for run-delay inference; kernel may not support this => **UNAVAILABLE**, never infer zero wait.
2. Linux `getrusage(RUSAGE_THREAD)` `ru_nvcsw` voluntary context switches, `ru_nivcsw` involuntary (https://man7.org/linux/man-pages/man2/getrusage.2.html). Counts identify kind, **not the exact duration or reason** of sleep.
3. Official ROS2 Jazzy `tf2_ros/src/buffer.cpp` (https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp), `Buffer::lookupTransform` advanced with timeout delegates to `canTransform`; polling loop `std::this_thread::sleep_for(10ms)`. Therefore a valid TF lookup **can** sleep between TF availability polls. Exact S1 `tf_thread_cpu<<tf_wall` is consistent with sleep, but also scheduler preemption/other waits; actual TF availability is not established.
4. Official Nav2 Jazzy `nav2_util/src/robot_utils.cpp` getTransform Advanced delegates to `tf_buffer->lookupTransform(target_frame,target_time,source_frame,source_time,fixed_frame,transform_tolerance)`. Official #3402 TF fixed-frame wait issue; merged Nav2 #3412 simple-mode accuracy tradeoff. **No setting change in S2**.

## Minimal 3-step method
A. L0 RED→GREEN **synthetic boundary classification**: known runqueue-dominant case; voluntary-blocking-dominant case; metrics invalid/unavailable; no authorization of source fix. Extend exactly original S1 CI-only LD_PRELOAD `d06/diagnostic/cm_tf_gettransform_preload.cpp` to bracket the SAME actual `nav2_util::getTransform` invocation with `getrusage(RUSAGE_THREAD)`, `/proc/thread-self/schedstat` if kernel schedstats=1; use strict PID/TID/clock matching already verified by S1; never modify official Nav2.
B. S0 reuse **original NO_GOAL**: on pinned original official running CM verify procfs scheduler interface, actual `TF_ADV` record has added context switches + runqueue. These probes themselves may add latency, so do NOT count their runtime as release performance. If schedstats disabled or inconsistent, classify `SCHEDSTAT_UNAVAILABLE`, no fake zero CPU preemption.
C. Only after true B confidence may run ONE S2 trace-ON Moving Goal (no repeat of same source), and record at FIRST CM120ms breach the *same callback's* `TF_ADV` wall/CPU/runqueue/context-switch deltas; report S2 wait-vs-runnable delay classification. If no same-window failure or TF context, `CAUSE_UNPROVEN`. If schedstat unavailable, voluntary counters alone cannot definitively partition time. Further performance/policy tuning (Gate C) blocked without defensible root cause, and original tracer-OFF Gate D / Owner WSL2 not started.

## Conservative verdict contract
- RUNQUEUE_DOMINANT: schedstats on + complete same-thread counters + runqueue_delay>=70% of TF nonCPU. Marks **scheduler ready-queue interval dominant within measured TF interval**, not final CM release root or code fix authorization.
- VOLUNTARY_BLOCKING_DOMINANT: schedstats on + runqueue_delay<=20% of TF nonCPU + voluntary switches>=2 + residual>=50%. Marks **sleep/blocking outside ready queue dominant**; official tf2 poll is plausible but not definitively proven as source of all sleep. Need TF availability/time correlation before claiming `TF_BUFFER_WAIT_PROVEN`.
- Others: `OFFCPU_MIXED_UNPROVEN`, `SCHEDSTAT_UNAVAILABLE_HOLD`, or `INVALID_METRICS_HOLD`. No implicit cause proof, no Goal/Owner approval.
- Difference between `CLOCK_THREAD_CPUTIME_ID` and `/proc/thread-self/schedstat` CPU runtime is subject to probe bracketing overhead; kernel reads start-before and end-after original call produce broad conservative bounds, **not exact nanosecond decomposition**. Threshold/multiple contexts and fail closed.
- Maximum one additional diagnostic Goal only if S0 real NO_GOAL capability GREEN; refuse preGoal negative triggers.

## Deliverables/acceptance gates
Pure tests RED, GREEN, REFACTOR/REVIEW, exact SHA docs, run evidence, no raw private ROS bags. `AXIA_G07_S2_OFFCPU_PROVENANCE`, `S2_REAL_NO_GOAL`, optional `S2_ONE_MOVING_GOAL`, all with first CM violation/rmw source & observer, first lifecycle failure. Public Draft PR; main never merged without user approval. SW software stop != certified E-Stop.
```text
S2_ROOT_CAUSE=UNPROVEN
S2_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
