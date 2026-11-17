"""One official CM cmd_vel callback interval vs first RMW publisher gap.

Pure diagnostic, reuses verified Cycle31 subscription handle resolver.
LTTng clocks and RMW MessageInfo SYSTEM timestamps are not subtracted.
A duration overlap is NOT TF wait/OS scheduling causality or release PASS.
"""
from __future__ import annotations
import math
from d06.live.g07_cycle31_cm_topic_callback_identity import (
    resolve_cm_cmdvel_handles,
)

TOPIC="/cmd_vel_supervised"
CM_NAMES={"collision_monitor","collision_monit"}
STMT={"ros2:rcl_subscription_init","ros2:rclcpp_subscription_init",
      "ros2:rclcpp_subscription_callback_added"}

def _hold(status,**extra):
    return dict(schema="axia.g07.c05.first_cm_cmd_callback_v1",status=status,
                no_new_goal_authorized=True,goal_sent_by_diagnostic=False,
                tf_lookup_causality_proven=False,
                scheduler_causality_proven=False,
                cm120_release_pass=False,
                owner_wsl2_accepted=False,certified_estop=False,
                **extra)

def _first_pair(observer):
    if not isinstance(observer,list) or len(observer)>100000:
        return None
    starts=[e.get("t") for e in observer
            if isinstance(e,dict) and e.get("kind")=="owner_goal_published"
            and type(e.get("t")) in (float,int)]
    if len(starts)!=1:
        return None
    goal=starts[0]
    candidates=[e for e in observer if isinstance(e,dict)
                and e.get("kind")=="pre_guard" and
                type(e.get("t")) in (float,int) and
                math.isfinite(e["t"]) and e["t"]>goal and
                type(e.get("rmw_source_ns")) is int and
                type(e.get("rmw_publication_seq")) is int]
    candidates.sort(key=lambda e:e["t"])
    for a,b in zip(candidates,candidates[1:]):
        ms=(b["rmw_source_ns"]-a["rmw_source_ns"])/1e6
        if b["rmw_publication_seq"]==a["rmw_publication_seq"]+1 and ms>=120.0 and a["t"]<b["t"]:
            return a,b,ms
    return None

def _anchor(trace,anchors):
    if not isinstance(anchors,dict) or not isinstance(trace,list):
        return None
    a,b=anchors.get("start"),anchors.get("end")
    if not isinstance(a,dict) or not isinstance(b,dict):
        return None
    for x in (a,b):
        if not all(type(x.get(k)) is int and x[k]>0 for k in ("mono_ns","wall_ns")):
            return None
    if (b["mono_ns"]<=a["mono_ns"] or b["wall_ns"]<=a["wall_ns"]):
        return None
    offset=a["wall_ns"]-a["mono_ns"]
    if abs(offset-(b["wall_ns"]-b["mono_ns"]))>=50_000_000:
        return None
    samples=[e["timestamp_ns"] for e in trace
             if e.get("name") in ("ros2:callback_start","ros2:callback_end")
             and type(e.get("timestamp_ns")) is int]
    if not samples:
        return None
    lo=min(samples);hi=max(samples)
    pad=2_000_000_000
    if a["mono_ns"]-pad<=lo<=hi<=b["mono_ns"]+pad:
        return 0
    if a["wall_ns"]-pad<=lo<=hi<=b["wall_ns"]+pad:
        return offset
    return None

def classify(observer,trace,anchors):
    pair=_first_pair(observer)
    if pair is None:
        return _hold("FIRST_CM_RMW_SOURCE_PAIR_UNVERIFIED_HOLD")
    a,b,source_gap=pair
    if not isinstance(trace,list) or len(trace)>100000:
        return _hold("CM_CALLBACK_TRACE_UNBOUNDED_OR_INVALID_HOLD")
    pids={e.get("vpid") for e in trace if isinstance(e,dict)
          and e.get("name")=="ros2:rcl_subscription_init"
          and e.get("topic_name")==TOPIC and e.get("procname") in CM_NAMES
          and type(e.get("vpid")) is int}
    if len(pids)!=1:
        return _hold("CM_INPUT_CALLBACK_OWNER_UNVERIFIED_HOLD")
    pid=next(iter(pids))
    try:
        handles,meta=resolve_cm_cmdvel_handles(trace,cm_pid=pid)
    except ValueError:
        return _hold("CM_INPUT_CALLBACK_TOPIC_LINK_INVALID_HOLD")
    if len(handles)!=1 or meta.get("topic_matched_subscriptions")!=1:
        return _hold("CM_INPUT_CALLBACK_HANDLE_UNVERIFIED_HOLD")
    cb=[e for e in trace if isinstance(e,dict) and e.get("vpid")==pid
        and e.get("name") in ("ros2:callback_start","ros2:callback_end")
        and str(e.get("callback")) in handles]
    if len(cb)<2:
        return _hold("CM_FIRST_GAP_CALLBACK_ABSENT_HOLD")
    offset=_anchor(cb,anchors)
    if offset is None:
        return _hold("TRACE_CLOCK_ANCHOR_UNVERIFIED_HOLD")
    cb.sort(key=lambda e:e["timestamp_ns"])
    active={}
    done=[]
    for event in cb:
        if type(event.get("timestamp_ns")) is not int or type(event.get("vtid")) is not int:
            return _hold("CM_CALLBACK_THREAD_TIMESTAMP_UNVERIFIED_HOLD")
        key=(event["vtid"],str(event["callback"]))
        t=(event["timestamp_ns"]-offset)/1e9
        if event["name"]=="ros2:callback_start":
            if key in active:
                return _hold("CM_CALLBACK_NESTING_UNVERIFIED_HOLD")
            active[key]=t
        elif key in active:
            st=active.pop(key)
            if t>=st:
                overlap=max(0,min(t,b["t"])-max(st,a["t"]))
                if overlap>0:
                    done.append((t-st,overlap))
    if not done:
        return _hold("CM_FIRST_GAP_CALLBACK_ABSENT_HOLD",
                     first_cm_rmw_source_gap_ms=round(source_gap,6))
    return _hold("CM_INPUT_CALLBACK_INTERVAL_OBSERVED_HYPOTHESIS_ONLY",
                 first_cm_rmw_source_gap_ms=round(source_gap,6),
                 first_cm_observer_wall_gap_ms=round((b["t"]-a["t"])*1000,6),
                 trace_clock_domain=("HOST_MONOTONIC" if offset==0
                                     else "LTTNG_WALL_EPOCH_MAPPED_MONOTONIC"),
                 matched_cm_cmd_callback_count=len(done),
                 max_matched_cm_cmd_callback_duration_ms=round(max(x[0] for x in done)*1000,6),
                 max_callback_overlap_first_gap_ms=round(max(x[1] for x in done)*1000,6),
                 official_cm_topic_to_callback_link_proven=True,
                 stage="DIAGNOSTIC_ONLY_NOT_SAFETY_RELEASE")
