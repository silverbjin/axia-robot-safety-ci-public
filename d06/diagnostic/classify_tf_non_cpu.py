"""Conservative Linux scheduling provenance for one matched CM TF call.

No ROS, no goal, no official Nav2 patch. Runqueue wait is measured by
per-thread schedstat only if the kernel reports schedstats enabled. Voluntary
switches indicate an actor yielded but cannot uniquely name tf2's poll.
"""
from __future__ import annotations

def _hold(status, **extra):
    return dict(schema="axia.g07.s2.tf_offcpu_v1",status=status,
                root_cause_proven=False,tf_buffer_wait_proven=False,
                gate_c_authorized=False,release_pass=False,
                certified_estop=False,**extra)

def classify_tf_offcpu(*,wall_ns,cpu_ns,schedstat_available,runqueue_ns,
                       sched_cpu_ns,voluntary_cs,involuntary_cs):
    values=(wall_ns,cpu_ns,runqueue_ns,sched_cpu_ns,
            voluntary_cs,involuntary_cs)
    if (any(type(v) is not int or v<0 for v in values)
        or type(schedstat_available) is not bool or
        wall_ns<=0 or cpu_ns>wall_ns or
        runqueue_ns>wall_ns-cpu_ns+2_000_000 or
        (schedstat_available and sched_cpu_ns+2_000_000<cpu_ns)):
        return _hold("INVALID_SCHEDULER_METRICS_HOLD")
    off=wall_ns-cpu_ns
    base=dict(tf_wall_ms=round(wall_ns/1e6,6),
              thread_cpu_ms=round(cpu_ns/1e6,6),
              offcpu_ms=round(off/1e6,6),
              schedstat_available=schedstat_available,
              voluntary_context_switches=voluntary_cs,
              involuntary_context_switches=involuntary_cs)
    if not schedstat_available:
        return _hold("SCHEDSTAT_UNAVAILABLE_HOLD",**base)
    runq=min(off,runqueue_ns)
    # schedstat values are bracketing *upper bounds*; proc reads themselves
    # may contribute a small additional delay outside the TF call.
    base.update(runqueue_wait_ms=round(runq/1e6,6),
                blocking_or_sleep_upper_ms=round(max(0,off-runq)/1e6,6),
                sched_thread_runtime_ms=round(sched_cpu_ns/1e6,6))
    if off<2_000_000:
        status="TF_NONCPU_NOT_DOMINANT"
    elif runq>=off*.7:
        status="RUNQUEUE_WAIT_DOMINANT"
    elif (runq<=off*.2 and off-runq>=off*.5
          and voluntary_cs>=2):
        status="VOLUNTARY_BLOCKING_DOMINANT"
    else:
        status="OFFCPU_MIXED_UNPROVEN"
    # Neither runqueue dominance nor voluntary blocking alone proves what
    # happened inside tf2 Buffer::canTransform. Never authorize Gate C.
    return _hold(status,**base)
