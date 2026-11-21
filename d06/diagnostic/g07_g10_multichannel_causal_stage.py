#!/usr/bin/env python3
"""First native G07 multi-channel same-pair interval classifier (L0, fail closed).

Original real CI #44870974857 first Scan and #44870371777 first CM.
No cross-clock absolute subtraction, no inference that separate rosbag
Header stamps prove an identical DDS publication GID. Diagnostic ONLY:
does not modify callback groups, DDS transport, Executor, safety TTL or Goal.
"""
import math

def _interval(x):
    return type(x) in (int,float) and math.isfinite(x) and 0 < x < 10000

def assess(row):
    result=dict(schema="axia.g07.g10.same_pair_interval_boundary.v1",
        release="HOLD",root_cause="UNDETERMINED",root_cause_proven=False,
        publisher_root_proven=False,rmw_transport_root_proven=False,
        whole_process_halt_proven=False,host_executor_root_proven=False,
        exact_cross_process_dds_publication_proven=False,
        certified_estop=False,owner_l3_accepted=False,safety_ttl_changed=False,
        first_boundary="EXACT_PAIR_UNVERIFIED_HOLD",
        other_callback_progress_during_gap=False,
        not_proven=["RMW_RECEPTION_VS_TAKE","HOST_EXECUTOR_ROOT","GZ_BRIDGE_ROOT"])
    if not isinstance(row,dict) or row.get("topic") not in ("scan","cm"):
        return result
    if type(row.get("seq_gap")) is not int or row["seq_gap"]!=1:
        return result
    keys=("observer_ms","rmw_source_ms","rmw_received_ms")
    if any(not _interval(row.get(k)) for k in keys):
        return result
    independent=(row.get("rosbag_same_header_ms") if row["topic"]=="scan"
                 else row.get("independent_same_seq_received_ms"))
    if not _interval(independent):
        return result
    if row["topic"]=="scan" and not _interval(row.get("header_sim_ms")):
        return result
    for key in ("clock_callbacks_inside","odom_callbacks_inside"):
        v=row.get(key)
        if v is not None and (type(v) is not int or v<0 or v>1_000_000):
            return result
    source=row["rmw_source_ms"]
    receive=row["rmw_received_ms"]
    observer=row["observer_ms"]
    result["other_callback_progress_during_gap"]=(
        (row.get("clock_callbacks_inside") or 0)>0 or
        (row.get("odom_callbacks_inside") or 0)>0)
    if source>300:
        result["first_boundary"]="SOURCE_PERIOD_BREACH_CANDIDATE_HOLD"
    elif receive>300 and observer>300 and independent<=300:
        result["first_boundary"]="ORIGINAL_SUBSCRIBER_RECEIVE_OR_TAKE_LATE_HOLD"
    elif observer>300 and receive<=300:
        result["first_boundary"]="AFTER_RMW_RECEIVE_BEFORE_CALLBACK_CANDIDATE_HOLD"
    elif observer<=300 and receive<=300 and source<=300 and independent<=300:
        result["first_boundary"]="NO_BREACH_IN_THIS_PAIR_NOT_ACCEPTANCE_HOLD"
    else:
        result["first_boundary"]="MIXED_INTERVAL_OR_INDEPENDENT_DELAY_HOLD"
    return result
