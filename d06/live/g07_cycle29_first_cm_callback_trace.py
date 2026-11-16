#!/usr/bin/env python3
"""Read-only official Nav2 Collision Monitor callback/first RMW gap correlation.

Inputs:
  - original real Goal callback events and oracle result (PRIVATE CI only);
  - LTTng UST official CM callback register/start/end events, with vpid/vtid;
  - host wall_epoch and monotonic anchor pairs taken around ONE CI Goal.
Only sanitized numeric aggregation may be printed. Do NOT persist/publish
raw trace, ROS bag, Goal UUID, private source or private user paths.

LTTng clock domain was proved HOST_WALL_EPOCH in L1 #43808668688.
Never subtract RMW SYSTEM absolute timestamps from callback MONOTONIC. Use
RMW source-source *durations* and normalize host callback trace epoch via
explicit wall-minus-mono anchor; verify offset drift <50ms.
A long callback or empty callback window is only a CAUSAL CANDIDATE.
"""
from __future__ import annotations
from collections import defaultdict
import json
import math
from pathlib import Path

from d06.live.g07_cycle27_first120_rpc_relation import classify as first_margin

SUPPORTED=("ros2:rclcpp_callback_register","ros2:callback_start","ros2:callback_end")
TTL_RELEASE_MS=120.0

def _num(v):
    return type(v) in (int,float) and math.isfinite(v)

def _hold(status,**more):
    return {
        "schema":"axia.g07.cycle29.first_cm_callback_trace_v1",
        "status":status,
        "safety_pass":False,
        "owner_goal_authorized":False,
        "owner_l3_accepted":False,
        "certified_estop":False,
        "no_new_ros_goal":True,
        "cm_callback_causality_proven":False,
        "tf_lookup_block_proven":False,
        "host_clock_step_excluded":False,
        "ready_for_wsl2_owner_goal":False,
        "axia_demo_accepted":"AXIA_MVP_DEMO_ACCEPTED=HOLD",
        **more,
    }

def _anchor_domain(events,anchors):
    if not isinstance(anchors,dict):
        return None
    b,e=anchors.get("start"),anchors.get("end")
    if not isinstance(b,dict) or not isinstance(e,dict):
        return None
    keys=("mono_ns","wall_ns")
    if not all(type(pair.get(k)) is int and pair[k]>0 for pair in (b,e) for k in keys):
        return None
    if (b["mono_ns"]>=e["mono_ns"] or b["wall_ns"]>=e["wall_ns"] or
        abs((e["wall_ns"]-e["mono_ns"])-(b["wall_ns"]-b["mono_ns"]))>=50_000_000):
        return None
    ticks=[x.get("timestamp_ns") for x in events
           if isinstance(x,dict) and type(x.get("timestamp_ns")) is int]
    if not ticks:
        return None
    lo=min(ticks);hi=max(ticks)
    tolerance=2_000_000_000
    def inside(key):
        return b[key]-tolerance<=lo<=e[key]+tolerance and b[key]-tolerance<=hi<=e[key]+tolerance
    if inside("mono_ns"):
        return "HOST_MONOTONIC",0
    if inside("wall_ns"):
        return "LTTNG_WALL_EPOCH_MAPPED_MONOTONIC",b["wall_ns"]-b["mono_ns"]
    return None

def _first_source_pair(events):
    starts=[v.get("t") for v in events
            if isinstance(v,dict) and v.get("kind")=="owner_goal_published"
            and _num(v.get("t"))]
    if len(starts)!=1:
        return None
    goal=starts[0]; cm=[]
    for x in events:
        if not isinstance(x,dict) or x.get("kind")!="pre_guard" or not _num(x.get("t")):
            continue
        if x["t"]<goal:
            continue
        if not (type(x.get("rmw_source_ns")) is int and x["rmw_source_ns"]>0
                and type(x.get("rmw_publication_seq")) is int):
            continue
        cm.append(x)
    for a,b in zip(cm,cm[1:]):
        if (b["rmw_source_ns"]>a["rmw_source_ns"]
            and b["rmw_publication_seq"]==a["rmw_publication_seq"]+1
            and (b["rmw_source_ns"]-a["rmw_source_ns"])/1e6>=TTL_RELEASE_MS
            and b["t"]>a["t"]):
            return a,b
    return None

def classify_callback_gap(events,report,traced,*,cm_pid,clock_anchors):
    """Fail closed on unknown vpid, source provenance, or tracing clock domain."""
    if not (isinstance(events,list) and isinstance(report,dict)
            and isinstance(traced,list) and type(cm_pid) is int and cm_pid>1):
        return _hold("CM_TRACE_INPUT_UNVERIFIED_HOLD")
    oracle=first_margin(events,report,require_oracle=True)
    if not oracle["status"].startswith("CM_SOURCE_120MS_GAP_") or not oracle.get(
            "scoped_original_oracle_gap_matched"):
        return _hold("FIRST_CM_RMW_ORACLE_UNVERIFIED_HOLD",
                     oracle_status=oracle["status"])
    pair=_first_source_pair(events)
    if pair is None:
        return _hold("FIRST_CM_RMW_ORACLE_UNVERIFIED_HOLD")
    a,b=pair
    derived_gap=(b["rmw_source_ns"]-a["rmw_source_ns"])/1e6
    if (not _num(oracle.get("first_cm_source_gap_ms")) or
        abs(derived_gap-oracle["first_cm_source_gap_ms"])>.01):
        return _hold("FIRST_CM_RMW_ORACLE_UNVERIFIED_HOLD")
    domain=_anchor_domain(traced,clock_anchors)
    if domain is None:
        return _hold("TRACE_CLOCK_CALIBRATION_UNVERIFIED_HOLD",
                     first_cm_source_gap_ms=round(derived_gap,6))
    domain_label,epoch_offset=domain

    seen_regs={}
    pairs=defaultdict(list);finished=[];unmatched=0
    for x in traced:
        if not isinstance(x,dict) or x.get("name") not in SUPPORTED:
            continue
        if (type(x.get("vpid")) is not int or x["vpid"]!=cm_pid
            or type(x.get("timestamp_ns")) is not int
            or x["timestamp_ns"]<0):
            continue
        handle=x.get("callback")
        if type(handle) not in (str,int) or str(handle)=="":
            continue
        key=str(handle)
        t=(x["timestamp_ns"]-epoch_offset)/1e9
        if x["name"]=="ros2:rclcpp_callback_register":
            sym=x.get("symbol")
            if isinstance(sym,str):
                seen_regs[key]=sym
        elif x["name"]=="ros2:callback_start":
            tid=x.get("vtid")
            if type(tid) is not int:
                return _hold("CM_CALLBACK_THREAD_IDENTITY_UNVERIFIED_HOLD")
            pairs[(tid,key)].append(t)
        elif x["name"]=="ros2:callback_end":
            tid=x.get("vtid")
            stack=pairs.get((tid,key))
            if type(tid) is not int or not stack:
                unmatched+=1
                continue
            started=stack.pop()
            if t<started:
                return _hold("CM_CALLBACK_MONOTONIC_ORDER_UNVERIFIED_HOLD")
            finished.append((started,t,key))
    pending=sum(len(stack) for stack in pairs.values())
    cmdhandles={key for key,sym in seen_regs.items()
                if any(k in sym.lower() for k in
                       ("cmdvel","cmd_vel","cmdvelincallback","collisionmonitor::cmd"))}
    cm_cmd=[(s,e) for s,e,k in finished if k in cmdhandles
            and e>=a["t"]-.05 and s<=b["t"]+.05]
    cmd_max=max(((e-s)*1000 for s,e in cm_cmd),default=None)
    all_intersect=[(s,e,k) for s,e,k in finished
                   if e>=a["t"]-.05 and s<=b["t"]+.05]
    if not cmdhandles:
        status="CM_CALLBACK_IDENTITY_UNVERIFIED_HOLD"
    elif cmd_max is not None and cmd_max>=TTL_RELEASE_MS:
        status="CM_CMDVEL_CALLBACK_OVER_120MS_CANDIDATE_HOLD"
    else:
        status="CM_INPUT_DELIVERY_OR_EXECUTOR_DELAY_CANDIDATE_HOLD"
    return _hold(
        status,
        first_cm_source_gap_ms=round(derived_gap,6),
        first_cm_observer_gap_ms=round((b["t"]-a["t"])*1000,6),
        first_gap_native_rpc_overlap_candidate=oracle.get("native_stop_rpc_overlap_candidate"),
        upstream_publications_inside_gap=oracle.get("upstream_publications_inside_gap"),
        trace_clock_domain=domain_label,
        registered_callback_count=len(seen_regs),
        registered_cmdvel_callback_count=len(cmdhandles),
        cm_finished_callback_count_near_first_gap=len(all_intersect),
        cm_cmdvel_callback_count_near_first_gap=len(cm_cmd),
        cm_cmdvel_max_duration_ms=round(cmd_max,6) if cmd_max is not None else None,
        cm_any_callback_max_duration_ms=(round(max((e-s)*1000 for s,e,k in all_intersect),6)
                                           if all_intersect else None),
        cm_unmatched_callback_end_count=unmatched,
        cm_pending_callback_start_count=pending,
        cause_scope="OFFICIAL_CM_CALLBACK_TRACE_CANDIDATE_ONLY",
    )
