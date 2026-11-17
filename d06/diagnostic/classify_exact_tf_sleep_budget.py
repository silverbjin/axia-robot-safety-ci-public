"""Task01 exact-per-TF-call voluntary sleep budget, diagnostic-only.

Legacy first-gap #44049067368 has NO call start/end retained publicly and
must stay HOLD. Future numeric-only artifacts may prove that actual libc sleep
requests dominated a particular official Advanced TF invocation; they still
cannot establish why a TF transform was unavailable, the internal Buffer
clock, the RMW publisher SYSTEM-to-MONOTONIC join, or runnable wait without
real kernel scheduling evidence. Never produce CM120 release or Goal authority.
"""
from __future__ import annotations

from d06.diagnostic.export_public_cm120_first_gap import SCHEMA


def _hold(reason):
    return dict(status=reason, schema="axia.g07.task01.exact_tf_sleep_budget_v1",
        root_cause_proven=False, gate_c_authorized=False,
        cm120_release_pass=False,
        tf_buffer_wait_proven=False,
        scheduler_runqueue_wait_proven=False,
        source_publication_to_monotonic_alignment_proven=False,
        tf_buffer_clock_proven=False,
        requested_sleep_lower_bound_ns=None,
        nonrequested_wall_upper_bound_ns=None)


def _number(v):
    return type(v) is int


def classify_call_budget(doc):
    if not isinstance(doc,dict) or doc.get("schema")!=SCHEMA:
        return _hold("EXACT_TF_CALL_PUBLIC_PROVENANCE_INVALID_HOLD")
    if any(doc.get(k) is not False for k in
           ("root_cause_proven","gate_c_authorized","cm120_release_pass",
            "owner_wsl2_accepted",
            "source_publication_to_monotonic_alignment_proven")):
        return _hold("DIAGNOSTIC_RELEASE_FLAG_INVALID_HOLD")
    if not isinstance(doc.get("first_gap"),dict):
        return _hold("FIRST_SOURCE_GAP_NOT_REPRODUCED_HOLD")
    tf=doc.get("tf_calls",{})
    if not isinstance(tf,dict) or not isinstance(tf.get("spans"),list):
        return _hold("EXACT_TF_CALL_INTERVALS_NOT_PRESERVED_HOLD")
    calls=tf["spans"]
    if not calls or len(calls)>40 or tf.get("count")!=len(calls):
        return _hold("TF_CALL_COUNT_MISMATCH_HOLD")
    all_spans=doc.get("tf_sleep",{})
    if (not isinstance(all_spans,dict) or
        not isinstance(all_spans.get("spans"),list) or
        all_spans.get("count")!=len(all_spans["spans"])):
        return _hold("TF_SLEEP_INTERVAL_INVALID_HOLD")
    sleeps=all_spans["spans"]
    if len(sleeps)>64:
        return _hold("TF_SLEEP_INTERVAL_INVALID_HOLD")
    parsed_sleeps=[]
    for s in sleeps:
        if not isinstance(s,dict):
            return _hold("TF_SLEEP_INTERVAL_INVALID_HOLD")
        a,b,r,rc=(s.get(k) for k in ("start_rel_observer_ns",
                "end_rel_observer_ns","request_ns","rc"))
        if (not all(_number(x) for x in (a,b,r,rc))
            or b<=a or r<0 or r>100_000_000 or rc!=0
            or b-a<r):
            return _hold("TF_SLEEP_INTERVAL_INVALID_HOLD")
        parsed_sleeps.append((a,b,r))
    parsed_sleeps.sort()
    if any(a[1]>b[0] for a,b in zip(parsed_sleeps,parsed_sleeps[1:])):
        return _hold("TF_SLEEP_SPANS_OVERLAP_HOLD")
    parsed_calls=[]
    for c in calls:
        if not isinstance(c,dict):
            return _hold("TF_CALL_INTERVAL_INVALID_HOLD")
        a,b,cpu,declared,observed,r,w,complete=(
            c.get("start_rel_observer_ns"),c.get("end_rel_observer_ns"),
            c.get("thread_cpu_ns"),c.get("sleep_count_declared"),
            c.get("sleep_count_observed"),c.get("sleep_request_ns"),
            c.get("sleep_wall_ns"),c.get("coverage_complete"))
        if (not all(_number(x) for x in (a,b,cpu,observed,r,w))
            or declared is not None and not _number(declared)
            or type(complete) is not bool
            or b<=a or cpu<0 or cpu>b-a or observed<0 or r<0 or w<0
            or r>b-a or w>b-a):
            return _hold("TF_CALL_INTERVAL_INVALID_HOLD")
        parsed_calls.append((a,b,cpu,declared,observed,r,w,complete))
    # New public evidence intentionally omits PIDs/TIDs; the *producer*
    # matched exact official CM PID/TID BEFORE exporting these numeric spans.
    # If a consumer cannot prove disjoint invocation windows, HOLD.
    ordered=sorted(parsed_calls,key=lambda x:x[0])
    if any(a[1]>b[0] for a,b in zip(ordered,ordered[1:])):
        return _hold("TF_CALL_OVERLAP_OR_AMBIGUITY_HOLD")
    assigned=[[] for _ in ordered]
    for s in parsed_sleeps:
        owners=[i for i,c in enumerate(ordered)
                if c[0]<=s[0] and s[1]<=c[1]]
        if len(owners)!=1:
            return _hold("TF_SLEEP_OUTSIDE_EXACT_CALL_HOLD")
        assigned[owners[0]].append(s)
    for call,inner in zip(ordered,assigned):
        a,b,cpu,declared,observed,request,wall,complete=call
        if (declared is None or not complete
            or declared!=len(inner) or observed!=len(inner)
            or request!=sum(s[2] for s in inner)
            or wall!=sum(s[1]-s[0] for s in inner)):
            return _hold("TF_SLEEP_PER_CALL_COVERAGE_INCOMPLETE_HOLD")
    if all_spans.get("coverage_proven") is not True:
        return _hold("TF_SLEEP_PER_CALL_COVERAGE_INCOMPLETE_HOLD")
    # Select the largest official TF invocation (not a mean of unrelated
    # calls), then put a conservative upper bound on ALL nonrequested wall.
    selected=max(ordered,key=lambda c:c[1]-c[0])
    a,b,cpu,declared,observed,request,wall,complete=selected
    tf_wall=b-a
    return dict(_hold("EXACT_TF_CALL_SLEEP_BUDGET_OBSERVED_CAUSALITY_HOLD"),
        calls_with_complete_sleep_provenance=len(ordered),
        selected_call_wall_ns=tf_wall,
        selected_call_sleep_count=observed,
        requested_sleep_lower_bound_ns=request,
        nonrequested_wall_upper_bound_ns=tf_wall-request,
        sleep_wall_ns=wall,
        sleep_wakeup_excess_ns=wall-request,
        requested_sleep_wall_fraction=round(request/tf_wall,7),
        observed_sleep_wall_fraction=round(wall/tf_wall,7),
        scheduler_runqueue="UNAVAILABLE_WITHOUT_KERNEL_SCHEDSTAT",
        exact_call_scope_not_first_rmw_causality=True)
