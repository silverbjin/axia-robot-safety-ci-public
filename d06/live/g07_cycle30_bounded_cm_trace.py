#!/usr/bin/env python3
"""Cycle30: stream-filter huge LTTng callback traces to one OWNED official CM.

Real L2 #43809629649 yielded >500k all-ROS callback events before the
first-CM-gap classifier ran. Never raise on OTHER processes' trace volume.
Only materialize registered callback IDs from the exact CM vpid plus
start/end events near the first REAL CM RMW source gap. If relevant CM
window itself is overbounded, fail closed rather than silently truncate.

This is evidence-only. It does not change ROS, Nav2, Guard, Goal or CPU masks.
"""
from __future__ import annotations
import math

EVENTS={"ros2:callback_start","ros2:callback_end"}
REGISTER="ros2:rclcpp_callback_register"

def _valid_anchor(anchors):
    if type(anchors) is not dict:
        raise ValueError("CM_TRACE_ANCHOR_INVALID")
    a=anchors.get("start");b=anchors.get("end")
    if type(a) is not dict or type(b) is not dict:
        raise ValueError("CM_TRACE_ANCHOR_INVALID")
    for pair in (a,b):
        for key in ("mono_ns","wall_ns"):
            if type(pair.get(key)) is not int or pair[key]<=0:
                raise ValueError("CM_TRACE_ANCHOR_INVALID")
    if a["mono_ns"]>=b["mono_ns"] or a["wall_ns"]>=b["wall_ns"]:
        raise ValueError("CM_TRACE_ANCHOR_ORDER_INVALID")
    offset=a["wall_ns"]-a["mono_ns"]
    if abs(offset-(b["wall_ns"]-b["mono_ns"]))>=50_000_000:
        raise ValueError("CM_TRACE_ANCHOR_CLOCK_STEP_UNVERIFIED")
    return offset

def select_cm_first_window(iterator,*,cm_pid,first_pair,clock_anchors,
                           max_cm_callbacks=40000,max_cm_regs=2048):
    """Return (bounded CM-only event list, sanitized counts).

    Source gap and callback event timestamps remain in DIFFERENT domains.
    Clock offsets are applied to define callback-window membership, not
    to claim CM source publisher or ROS process root causality.
    """
    if type(cm_pid) is not int or cm_pid<=1:
        raise ValueError("CM_EXACT_OWNED_VPID_UNVERIFIED")
    if (type(max_cm_callbacks) is not int or not 1<=max_cm_callbacks<=100000
        or type(max_cm_regs) is not int or not 1<=max_cm_regs<=20000):
        raise ValueError("CM_WINDOW_LIMIT_UNVERIFIED")
    if type(first_pair) not in (tuple,list) or len(first_pair)!=2:
        raise ValueError("FIRST_CM_SOURCE_PAIR_UNVERIFIED")
    a,b=first_pair
    if not (isinstance(a,dict) and isinstance(b,dict)):
        raise ValueError("FIRST_CM_SOURCE_PAIR_UNVERIFIED")
    if not (type(a.get("t")) in (int,float) and type(b.get("t")) in (int,float)
            and math.isfinite(a["t"]) and math.isfinite(b["t"]) and
            0<a["t"]<b["t"]):
        raise ValueError("FIRST_CM_CALLBACK_WINDOW_UNVERIFIED")
    if not (type(a.get("rmw_source_ns")) is int and type(b.get("rmw_source_ns")) is int
            and type(a.get("rmw_publication_seq")) is int
            and type(b.get("rmw_publication_seq")) is int
            and b["rmw_publication_seq"]==a["rmw_publication_seq"]+1
            and (b["rmw_source_ns"]-a["rmw_source_ns"])/1e6>=120.0):
        raise ValueError("FIRST_CM_RMW_SOURCE_GAP_UNVERIFIED")
    offset=_valid_anchor(clock_anchors)
    # A 300ms cushion retains callback start/end for a bounded 120ms+
    # processing span, before/after the actual observer CM callback pair.
    lo_ns=int((a["t"]-.30)*1e9)
    hi_ns=int((b["t"]+.30)*1e9)
    chosen=[]
    counts={"total_events_seen":0,"cm_register_events_kept":0,
            "cm_callback_events_kept":0,"other_pid_events_skipped":0,
            "cm_callback_events_outside_window":0,"raw_trace_exported":False,
            "owner_goal_authorized":False,"owner_l3_accepted":False,
            "certified_estop":False,"no_ros_no_goal":True}
    for item in iterator:
        counts["total_events_seen"]+=1
        if not isinstance(item,dict) or item.get("name") not in EVENTS|{REGISTER}:
            continue
        if type(item.get("vpid")) is not int or item["vpid"]!=cm_pid:
            counts["other_pid_events_skipped"]+=1
            continue
        stamp=item.get("timestamp_ns")
        if type(stamp) is not int or stamp<0:
            raise ValueError("CM_TRACE_TIMESTAMP_UNVERIFIED")
        if item["name"]==REGISTER:
            counts["cm_register_events_kept"]+=1
            if counts["cm_register_events_kept"]>max_cm_regs:
                raise ValueError("CM_CALLBACK_REGISTRATION_UNBOUNDED")
            chosen.append(item)
            continue
        inside=(lo_ns<=stamp<=hi_ns or
                lo_ns+offset<=stamp<=hi_ns+offset)
        if not inside:
            counts["cm_callback_events_outside_window"]+=1
            continue
        counts["cm_callback_events_kept"]+=1
        if counts["cm_callback_events_kept"]>max_cm_callbacks:
            raise ValueError("CM_CALLBACK_WINDOW_UNBOUNDED")
        chosen.append(item)
    return chosen,counts
