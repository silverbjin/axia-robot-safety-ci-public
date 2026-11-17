"""Evidence-only CM120 first-source-pair TF sleep bounds.

Accepts ONLY the immutable already-public numeric artifact from actual
one-Goal Gazebo Run 44049067368. Classifies *observer-window-relative*
libc sleep, not first publisher gap causation or Linux runqueue duration.
This function never authorizes a Goal, TF performance change or release.
"""
from __future__ import annotations

import math
import re

EXPECTED_SCHEMA="axia.g07.cm120.public_first_gap_v1"
EXPECTED_RUN="44049067368"
EXPECTED_DIAG_SHA="5e6db932728085398fd1b6d9441847286d70c2be"


def _hold(status):
    return dict(
        status=status,
        root_cause_proven=False, gate_c_authorized=False,
        cm120_release_pass=False, owner_wsl2_accepted=False,
        tf_buffer_availability_wait_proven=False,
        tf_sleep_exact_rmw_source_cause_proven=False,
        source_publication_to_monotonic_alignment_proven=False,
        sim_time_stall_proven=False,
        scheduler_wait_proven=False,
        scheduler_runqueue="UNAVAILABLE_SAME_RUN",
        first_gap_ros_clock_progress="UNAVAILABLE_SAME_RUN",
        tf_sleep_observed=False,
    )


def _int(v):
    return type(v) is int


def classify(public_artifact):
    """Compute only observable spans, with strict provenance and fail-closed."""
    p=public_artifact
    if not isinstance(p,dict) or p.get("schema")!=EXPECTED_SCHEMA or (
            p.get("run_id")!=EXPECTED_RUN or
            p.get("public_source_sha")!=EXPECTED_DIAG_SHA):
        return _hold("PUBLIC_SOURCE_PROVENANCE_INVALID_HOLD")
    if (p.get("cm120_release_pass") is not False or
            p.get("root_cause_proven") is not False or
            p.get("gate_c_authorized") is not False or
            p.get("source_publication_to_monotonic_alignment_proven") is not False or
            p.get("owner_wsl2_accepted") is not False):
        return _hold("PUBLIC_DIAGNOSTIC_RELEASE_FLAG_INVALID_HOLD")

    gap=p.get("first_gap")
    if not isinstance(gap,dict):
        return _hold("FIRST_CM_SOURCE_PAIR_ABSENT_HOLD")
    source=gap.get("rmw_source_gap_ns")
    observer=gap.get("observer_gap_ns")
    pair=gap.get("pairs")
    if (not _int(source) or not _int(observer) or
            not 120_000_000<source<1_000_000_000 or
            not 0<observer<1_000_000_000 or
            not isinstance(pair,list) or len(pair)!=2):
        return _hold("FIRST_CM_SOURCE_PAIR_INVALID_HOLD")

    sleep=p.get("tf_sleep")
    if not isinstance(sleep,dict) or sleep.get("coverage_proven") is not True:
        return _hold("SLEEP_COVERAGE_UNVERIFIED_HOLD")
    spans=sleep.get("spans")
    if (not isinstance(spans,list) or len(spans)>64 or
            sleep.get("count")!=len(spans)):
        return _hold("SLEEP_INTERVAL_INVALID_HOLD")
    validated=[]
    for sp in spans:
        if not isinstance(sp,dict):
            return _hold("SLEEP_INTERVAL_INVALID_HOLD")
        st,en,req,rc=(sp.get(k) for k in
                      ("start_rel_observer_ns","end_rel_observer_ns","request_ns","rc"))
        if (not all(_int(v) for v in (st,en,req,rc))
                or not (-1_000_000_000<st<2_000_000_000)
                or not st<en<=2_000_000_000
                or not 0<req<=100_000_000 or rc!=0):
            return _hold("SLEEP_INTERVAL_INVALID_HOLD")
        validated.append((st,en,req))
    validated.sort()
    if any(a[1]>b[0] for a,b in zip(validated,validated[1:])):
        return _hold("SLEEP_SPANS_OVERLAP_HOLD")
    if any((st<0<en) or (st<observer<en) for st,en,_ in validated):
        return _hold("SLEEP_CROSSES_OBSERVER_PAIR_HOLD")
    within=[x for x in validated if 0<=x[0] and x[1]<=observer]
    actual=sum(en-st for st,en,_ in within)
    requested=sum(req for _,_,req in within)
    if not within or actual<requested:
        return _hold("SLEEP_WINDOW_OR_REQUEST_INVALID_HOLD")

    tf=p.get("tf_calls")
    if not isinstance(tf,dict) or type(tf.get("count")) is not int:
        return _hold("TF_CALL_PROVENANCE_INVALID_HOLD")
    durations=tf.get("durations_ms")
    if (not isinstance(durations,list) or not durations or len(durations)>40
            or tf["count"]!=len(durations)
            or not all(type(v) in (int,float) and math.isfinite(v)
                       and 0<=v<=2000 for v in durations)):
        return _hold("TF_CALL_PROVENANCE_INVALID_HOLD")
    longest=round(max(durations)*1_000_000)
    # This is nominal, NOT a join to one specific TF invocation: the public
    # artifact intentionally omits each call's raw start/end and private PID.
    ratio=round(actual/longest,7) if longest>0 else 0
    clock=p.get("clock_anchor",{})
    if (not isinstance(clock,dict) or
            not all(_int(clock.get(k)) for k in
                ("wall_minus_mono_start_ns","wall_minus_mono_end_ns"))):
        return _hold("CLOCK_ANCHOR_INVALID_HOLD")
    drift=abs(clock["wall_minus_mono_start_ns"]-
              clock["wall_minus_mono_end_ns"])
    if drift>=50_000_000:
        return _hold("CLOCK_ANCHOR_DRIFT_UNVERIFIED_HOLD")

    return dict(_hold("TF_POLLING_DOMINATES_OBSERVER_WINDOW_CAUSALITY_HOLD"),
        tf_sleep_observed=True,
        same_observer_pair_sleep_count=len(within),
        excluded_sleep_count=len(validated)-len(within),
        sleep_request_ns=requested,
        sleep_wall_ns=actual,
        sleep_wakeup_excess_ns=actual-requested,
        first_rmw_source_gap_ns=source,
        first_observer_gap_ns=observer,
        longest_tf_call_ns=longest,
        sleep_to_longest_tf_ratio_nominal=ratio,
        clock_anchor_drift_ns=drift,
        nominal_ratio_is_single_call_causality=False,
        whole_first_source_gap_explained=False)
