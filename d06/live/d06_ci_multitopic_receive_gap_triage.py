"""Read-only post-run first PRE_STOP multi-topic timing / RMW receive diagnosis.

No ROS actions, no safety TTL changes. DOES NOT imply the native Guard saw the
same gap or that CPU scheduling caused it. A failing CI oracle always HOLD.
"""
from __future__ import annotations
import math

LIMITS={"clock":.3,"cm":.15,"guard":.15,"odom":.3,"scan":.3,"source":.15,"supervisor":.15}

def _number(v):
    return type(v) in (int,float) and math.isfinite(v) and v>=0

def classify(data):
    out={"schema":"axia.g07.multi_topic_receive_gap_triage_v1",
         "status":"HOLD_MISSING_TIMING_PROVENANCE",
         "first_timing_channel":None,"first_timing_stage":None,
         "first_timing_gap_ms":None,
         "cm_rmw_source_gap_ms":None,"cm_rmw_received_gap_ms":None,
         "cm_receive_attribution":"UNVERIFIED",
         "over_limit_channels":[],
         "first_timing_violation_proven":False,
         "cm_publisher_stopped_proven":False,
         "native_guard_latch_observed":None,
         "scheduler_or_rmw_root_cause_proven":False,
         "whole_gazebo_l2_pass":False,"safety_pass":False,
         "owner_l3_accepted":False,"certified_estop":False}
    if type(data) is not dict:return out
    first=data.get("first_observer_violation")
    periods=data.get("seven_channel_max_gap_sec")
    pair=data.get("first_cm_rmw_pair")
    if type(first) is not dict or type(periods) is not dict or type(pair) is not dict:
        return out
    if (set(periods)!=set(LIMITS)
        or not all(_number(periods[k]) for k in LIMITS)
        or first.get("channel") not in LIMITS
        or first.get("stage") not in ("PRE_STOP","POST_STOP","SHUTDOWN")
        or not all(_number(first.get(k)) for k in
                   ("from_mono_sec","to_mono_sec","gap_sec","limit_sec"))):
        return out
    if first["to_mono_sec"]<first["from_mono_sec"]:
        return out
    if abs(first["to_mono_sec"]-first["from_mono_sec"]-first["gap_sec"])>1e-5:
        return out
    if not all(_number(pair.get(k)) for k in
               ("rmw_source_gap_sec","rmw_received_gap_sec","observer_callback_gap_sec")):
        return out
    if type(pair.get("publication_sequence_gap")) is not int:
        return out
    over=sorted(k for k,limit in LIMITS.items() if periods[k]>limit)
    r={**out,"over_limit_channels":over,"first_timing_channel":first["channel"],
       "first_timing_stage":first["stage"],
       "first_timing_gap_ms":round(first["gap_sec"]*1000,6),
       "first_timing_violation_proven":first["gap_sec"]>first["limit_sec"],
       "cm_rmw_source_gap_ms":round(pair["rmw_source_gap_sec"]*1000,6),
       "cm_rmw_received_gap_ms":round(pair["rmw_received_gap_sec"]*1000,6),
       "native_guard_latch_observed":data.get("native_guard_latch_observed")}
    if (pair["publication_sequence_gap"]==1
        and pair["rmw_source_gap_sec"]<=LIMITS["cm"]
        and pair["rmw_received_gap_sec"]>LIMITS["cm"]
        and pair["observer_callback_gap_sec"]>LIMITS["cm"]
        and r["first_timing_violation_proven"] and over):
        r.update(status="HOLD_MULTITOPIC_DELIVERY_GAP_RECEIPT_CANDIDATE",
                 cm_receive_attribution="RMW_RECEIVE_DELAY_CANDIDATE")
    return r
