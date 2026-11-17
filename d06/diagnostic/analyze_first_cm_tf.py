"""AXIA G07 diagnostic ONLY: first CM RMW 120ms gap vs exact TF function time.

Reuses Cycle05's official CM topic-to-C++-callback identity and C05 clock
anchor. This classifies *time spent in TF function* but never invents
TF blocking, OS scheduling, Guard safety or release acceptance.
"""
from __future__ import annotations

import re
from d06.live.g07_cycle05_cm_callback_window import _first_pair, _anchor
from d06.live.g07_cycle31_cm_topic_callback_identity import resolve_cm_cmdvel_handles

TF_LINE=re.compile(
    r"^TF_ADV pid=(\d+) tid=(\d+) mono_start_ns=(\d+) "
    r"mono_end_ns=(\d+) thread_cpu_ns=(-?\d+) ok=([01])"
    r"(?: schedstat_valid=([01]) runqueue_ns=(\d+) sched_cpu_ns=(\d+)"
    r" voluntary_cs=(\d+) involuntary_cs=(\d+))?$"
)
TOPIC="/cmd_vel_supervised"
CM_PROCS={"collision_monitor","collision_monit"}

def hold(reason,**extra):
    return dict(status=reason,schema="axia.g07.cm120.tf_first_gap_v1",
                original_source_modified=False,goal_count_authorized=0,
                root_cause_proven=False,tf_wait_proven=False,
                scheduler_wait_proven=False,gate_c_authorized=False,
                cm120_release_pass=False,certified_estop=False,**extra)

def analyze(observer,trace,tf_lines,anchors):
    if (not isinstance(observer,list) or not isinstance(trace,list)
        or not isinstance(tf_lines,list) or
        len(trace)>150000 or len(tf_lines)>20000):
        return hold("DIAGNOSTIC_INPUT_UNBOUNDED_HOLD")
    pair=_first_pair(observer)
    if pair is None:
        return hold("FIRST_120MS_RMW_SOURCE_PAIR_UNVERIFIED")
    a,b,source_ms=pair
    pids={e.get("vpid") for e in trace if isinstance(e,dict)
          and e.get("name")=="ros2:rcl_subscription_init"
          and e.get("topic_name")==TOPIC
          and e.get("procname") in CM_PROCS and type(e.get("vpid")) is int}
    if len(pids)!=1:
        return hold("CM_OFFICIAL_SUBSCRIPTION_OWNER_UNVERIFIED")
    pid=next(iter(pids))
    handles,metadata=resolve_cm_cmdvel_handles(trace,cm_pid=pid)
    if len(handles)!=1 or metadata.get("topic_matched_subscriptions")!=1:
        return hold("CM_TOPIC_TO_CALLBACK_HANDLE_UNVERIFIED")
    handle=next(iter(handles))
    events=[e for e in trace if isinstance(e,dict)
            and e.get("vpid")==pid and e.get("name") in
            ("ros2:callback_start","ros2:callback_end")
            and str(e.get("callback"))==handle]
    offset=_anchor(events,anchors)
    if offset is None:
        return hold("MONOTONIC_TRACE_CLOCK_ANCHOR_UNVERIFIED")
    events.sort(key=lambda e:e["timestamp_ns"])
    active={}
    callbacks=[]
    for e in events:
        if type(e.get("timestamp_ns")) is not int or type(e.get("vtid")) is not int:
            return hold("CM_CALLBACK_EVENT_FIELDS_MISSING")
        key=e["vtid"]
        t=(e["timestamp_ns"]-offset)/1e9
        if e["name"]=="ros2:callback_start":
            if key in active:return hold("CM_CALLBACK_NESTED_UNEXPECTED")
            active[key]=t
        elif key in active:
            start=active.pop(key)
            if t>=start and min(t,b["t"])>max(start,a["t"]):
                callbacks.append((key,start,t))
    if not callbacks:
        return hold("CM_FIRST_GAP_CALLBACK_MISSING")
    parsed=[]
    ready=False
    for line in tf_lines:
        if line.strip()=="AXIA_CM120_TF_DIAG_CM_LIBRARY_LOADED":
            ready=True
            continue
        m=TF_LINE.fullmatch(line.strip())
        if m is None:
            return hold("TF_DIAG_LINE_UNRECOGNIZED")
        ep,tid,s0,s1,cpu,ok=map(int,m.groups()[:6])
        if s1<s0 or cpu<0 or cpu>s1-s0 or ep<=1 or tid<=1:
            return hold("TF_INTERVAL_INVALID")
        sched=None
        if m.group(7) is not None:
            valid,wait_ns,run_ns,nvcsw,nivcsw=map(int,m.groups()[6:11])
            from d06.diagnostic.classify_tf_non_cpu import classify_tf_offcpu
            sched=classify_tf_offcpu(
                wall_ns=s1-s0,cpu_ns=cpu,schedstat_available=bool(valid),
                runqueue_ns=wait_ns,sched_cpu_ns=run_ns,
                voluntary_cs=nvcsw,involuntary_cs=nivcsw)
        parsed.append((ep,tid,s0/1e9,s1/1e9,cpu/1e9,bool(ok),sched))
    if not ready:return hold("CM_DIAG_LIBRARY_LOADING_UNVERIFIED")
    if not parsed:return hold("CM_ADVANCED_TF_SYMBOL_NOT_INTERPOSED")
    matched=[]
    for thread,start,end in callbacks:
        intervals=[e for e in parsed
                   if e[0]==pid and e[1]==thread and
                   e[2]>=start-.003 and e[3]<=end+.003 and e[3]>=e[2]]
        # Require a complete, nonoverlapping interval of the same live CM
        # callback thread; other process TF calls never count.
        intervals.sort(key=lambda x:x[2])
        if any(right[2]<left[3] for left,right in zip(intervals,intervals[1:])):
            return hold("TF_INTERVAL_NESTING_UNVERIFIED")
        covered=sum(t[3]-t[2] for t in intervals)
        if covered>end-start+.006:return hold("TF_TIME_EXCEEDS_CALLBACK_CLOCK_ERROR")
        if intervals:
            matched.append(dict(callback_ms=(end-start)*1000,
                    tf_function_wall_ms=covered*1000,
                    tf_thread_cpu_ms=sum(t[4] for t in intervals)*1000,
                    matched_tf_calls=len(intervals),
                    offcpu_provenance=(intervals[0][6] if len(intervals)==1 else
                        dict(status="MULTIPLE_TF_INTERVALS_OFFCPU_JOIN_UNVERIFIED",
                             root_cause_proven=False,gate_c_authorized=False,
                             release_pass=False)),
                    overlap_first_gap_ms=(min(end,b["t"])-max(start,a["t"]))*1000))
    if not matched:
        return hold("TF_NOT_LINKED_TO_FIRST_CM_GAP_CALLBACK_UNPROVEN",
                    first_source_gap_ms=round(source_ms,6))
    selected=max(matched,key=lambda x:x["overlap_first_gap_ms"])
    cb=selected["callback_ms"]
    tf=selected["tf_function_wall_ms"]
    cpu=selected["tf_thread_cpu_ms"]
    dominance=tf/cb if cb>0 else 0
    # Directly measured function cost, NOT proof that its wall time was
    # blocked waiting for TF (it may contain executor CPU preemption).
    label=("TF_FUNCTION_DOMINANT_WAIT_CAUSE_UNPROVEN"
           if tf>=40 and dominance>=.7 else
           "CM_OTHER_OR_QUEUING_DOMINANT_CAUSE_UNPROVEN")
    return hold(label,
        first_cm_rmw_source_gap_ms=round(source_ms,6),
        first_cm_observer_gap_ms=round((b["t"]-a["t"])*1000,6),
        cm_callback_wall_ms=round(cb,6),
        tf_function_wall_ms=round(tf,6),
        tf_thread_cpu_ms=round(cpu,6),
        other_elapsed_upper_ms=round(max(0,cb-tf),6),
        tf_wall_fraction_of_callback=round(dominance,4),
        cpu_vs_wall_difference_ms=round(max(0,tf-cpu),6),
        matched_tf_calls=selected["matched_tf_calls"],
        actual_tf_function_interval_recorded=True,
        s2_offcpu_provenance=(selected.get("offcpu_provenance") or
                             dict(status="S2_SCHEDULER_METRICS_NOT_COLLECTED_HOLD",
                                  root_cause_proven=False,
                                  gate_c_authorized=False)))
