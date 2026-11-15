"""Read-only first timing violation attribution; no ROS, Goal or safety changes.

RMW source (system clock), receipt (RMW) and observer callback (steady) intervals
must not be subtracted as absolute timestamps. Intervals alone permit candidate
attribution; no claim of proven kernel/observer scheduler root cause.
"""
from __future__ import annotations
import math

LIMITS={"source":.15,"cm":.15,"guard":.15,"supervisor":.15,
        "scan":.30,"odom":.30,"clock":.30}

def _number(v):
    return type(v) in (int,float) and math.isfinite(v) and v>=0

def classify(record):
    answer={"schema":"axia.g07.first_multichannel_rmw_gap_v1",
        "status":"HOLD_UNVERIFIED_FIRST_DELIVERY","first_violation_channel":None,
        "first_violation_phase":None,"first_violation_ms":None,
        "thresholds_sec":LIMITS.copy(),"violated_channels":[],
        "cm_source_gap_ms":None,"cm_receive_gap_ms":None,
        "cm_observer_gap_ms":None,"cm_publication_sequence_increment":None,
        "cm_publisher_stopped_proven":False,
        "observer_scheduler_root_proven":False,
        "attribution":"MISSING_RMW_SOURCE_RECEIVE_PROVENANCE",
        "safety_pass":False,"owner_l3_accepted":False,"certified_estop":False}
    if not isinstance(record,dict):
        return answer
    tt=record.get("original_safety_ttl_sec")
    gaps=record.get("observer_max_gap_sec")
    first=record.get("first_timing_violation")
    pair=record.get("cm_rmw")
    if (not isinstance(tt,dict) or tt!=LIMITS or not isinstance(gaps,dict)
        or set(gaps)!=set(LIMITS) or not isinstance(first,dict)):
        return answer
    if any(not _number(gaps[k]) for k in LIMITS):
        return answer
    answer["violated_channels"]=[k for k in LIMITS if gaps[k]>=LIMITS[k]]
    ch=first.get("channel")
    if (ch not in LIMITS or not _number(first.get("first_violation_at"))
        or not _number(first.get("first_violation_from"))
        or not _number(first.get("measured_gap_sec"))
        or first["measured_gap_sec"]<LIMITS[ch] or
        first["first_violation_at"]<first["first_violation_from"]):
        return answer
    if abs((first["first_violation_at"]-first["first_violation_from"])-
            first["measured_gap_sec"])>1e-5:
        return answer
    answer.update(
        status="HOLD_MULTICHANNEL_DELIVERY_BEFORE_STOP"
               if first.get("phase")=="PRE_STOP" else "HOLD_DELIVERY_IN_OTHER_PHASE",
        first_violation_channel=ch,first_violation_phase=first.get("phase"),
        first_violation_ms=round(first["measured_gap_sec"]*1000,6))
    if not isinstance(pair,dict):
        return answer
    for key in ("first_cm_source_gap_sec","first_cm_received_gap_sec",
                "first_cm_observer_gap_sec"):
        if not _number(pair.get(key)):
            return answer
    seq=pair.get("publication_sequence_increment")
    if type(seq) is not int or seq<1:
        return answer
    source=pair["first_cm_source_gap_sec"]
    recv=pair["first_cm_received_gap_sec"]
    observed=pair["first_cm_observer_gap_sec"]
    answer.update(cm_source_gap_ms=round(source*1000,6),
                  cm_receive_gap_ms=round(recv*1000,6),
                  cm_observer_gap_ms=round(observed*1000,6),
                  cm_publication_sequence_increment=seq)
    if (seq==1 and source<.15 and recv>=.15 and observed>=.15
        and abs(recv-observed)<.06):
        answer["attribution"]="RMW_RECEIVE_OR_OBSERVER_SCHEDULING_CANDIDATE"
    else:
        answer["attribution"]="RMW_DELIVERY_OR_SOURCE_UNRESOLVED"
    return answer
