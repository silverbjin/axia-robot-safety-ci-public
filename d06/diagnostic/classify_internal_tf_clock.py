"""Only numeric/time-domain public data from exact original CM TF clock.

Calls and clock rows are PRIVATE in-memory PID/TID tuples read on the sealed
runner. No PID, thread, ROS frame/pose, pointer, source stamp, absolute ROS
epoch, or private code is ever returned. All verdicts remain diagnostic HOLD.
"""
from __future__ import annotations

MAX_CLOCK_RAW=100
MAX_PUBLIC_SAMPLES=64


def _hold(status):
    return dict(
        status=status,
        tf_buffer_availability_wait_proven=False,
        same_rmw_source_clock_alignment_proven=False,
        scheduler_runqueue_wait_proven=False,
        clock_causality_proven=False,
        cm120_release_pass=False,
        gate_c_authorized=False,
        root_cause_proven=False,
        sample_count=0)


def summarize_tf_clock(calls,clock_rows,first_mono_ns,last_mono_ns):
    """call=(pid,tid,start_ns,end_ns,declared_sleeps,thread_cpu_ns)
    clock=(pid,tid,mono_ns,ros_ns,type,override_active).
    """
    if not clock_rows:
        return None
    if len(clock_rows)>MAX_CLOCK_RAW or not calls or last_mono_ns<=first_mono_ns:
        return _hold("TF_INTERNAL_CLOCK_BOUNDED_OR_OWNER_HOLD")
    # The exact first observer gap and official same-thread function must
    # both overlap. No same-run first gap => the exporter never calls here.
    eligible=[(i,c) for i,c in enumerate(calls) if
              min(c[3],last_mono_ns)>max(c[2],first_mono_ns)]
    if not eligible:
        return _hold("TF_INTERNAL_CLOCK_FIRST_PAIR_MISMATCH_HOLD")
    # Pick the single longest official Advanced TF call. Never sum
    # independent TF clock domains / unrelated callback invocations.
    selected=max(eligible,key=lambda item:item[1][3]-item[1][2])[1]
    pid,tid,start,end,declared,cpu=selected
    private=[]
    for row in clock_rows:
        if (not isinstance(row,tuple) or len(row)!=6
            or not all(type(x) is int for x in row)):
            return _hold("TF_INTERNAL_CLOCK_ROW_INVALID_HOLD")
        p,t,m,r,typ,active=row
        if p!=pid or t!=tid:
            continue
        if start<=m<=end:
            private.append((m,r,typ,active))
        elif first_mono_ns-200_000_000<=m<=last_mono_ns+200_000_000:
            # Rows on this same original thread but outside selected TF
            # call may belong to another invocation; exclude, never join.
            continue
    if len(private)>MAX_PUBLIC_SAMPLES:
        return _hold("TF_INTERNAL_CLOCK_BOUNDED_OR_OWNER_HOLD")
    if len(private)<2:
        return _hold("TF_INTERNAL_CLOCK_INSUFFICIENT_SAMPLES_HOLD")
    private.sort(key=lambda x:x[0])
    if any(a[0]>=b[0] for a,b in zip(private,private[1:])):
        return _hold("TF_INTERNAL_CLOCK_INVALID_MONOTONIC_HOLD")
    if any(a[1]>b[1] for a,b in zip(private,private[1:])):
        return _hold("TF_INTERNAL_CLOCK_REWIND_HOLD")
    types={r[2] for r in private}
    actives={r[3] for r in private}
    if len(types)!=1 or len(actives)!=1:
        return _hold("TF_INTERNAL_CLOCK_INCONSISTENT_TYPE_HOLD")
    typ=private[0][2]
    active=private[0][3]
    if typ!=1 or active!=1:
        return _hold("TF_CLOCK_OVERRIDE_NOT_ACTIVE_HOLD")
    # Only clock PROGRESS inside one actual official TF function is known;
    # neither failed canTransform results nor RMW source publication
    # (CLOCK_REALTIME from another process) is proved here.
    first,last=private[0],private[-1]
    return dict(_hold("TF_INTERNAL_RCL_CLOCK_SAMPLES_OBSERVED_CAUSALITY_HOLD"),
        clock_type=typ,
        override_active=True,
        sample_count=len(private),
        mono_advance_ns=last[0]-first[0],
        sim_advance_ns=last[1]-first[1],
        sim_to_mono_progress_ratio=round(
            (last[1]-first[1])/(last[0]-first[0]),7),
        samples=[dict(
            mono_rel_first_observer_ns=m-first_mono_ns,
            ros_rel_first_internal_sample_ns=r-first[1])
            for m,r,typ,active in private])
