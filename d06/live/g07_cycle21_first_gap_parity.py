#!/usr/bin/env python3
"""Pure Cycle21 first CM RMW-output vs observer callback gap attribution.

Analyzes a *sanitized relative-time numeric fixture* of a historic Owner Goal.
This is a no-ROS/no-Goal CI regression, not an observed new Gazebo/WSLg run.
Only source vs source, receive vs receive, callback vs callback time
differences are calculated. The host SYSTEM clock step remains unexcluded.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

SCHEMA="axia.g07.cycle21.first_gap_numeric_fixture_v1"
KINDS=("pre_guard","supervised","guard","clock","supervisor","odom","scan")
HARD_CM_MS=150.0
RELEASE_CM_MS=120.0

def _num(x):
    return type(x) in (int,float) and math.isfinite(x)

def _default(status="EVIDENCE_UNVERIFIED_HOLD"):
    return {
        "schema":"axia.g07.cycle21.first_multichannel_attribution_v1",
        "status":status,
        "safety_pass":False,
        "owner_goal_authorized":False,
        "owner_l3_accepted":False,
        "certified_estop":False,
        "no_ros_no_goal":True,
        "cm_input_callback_latency_proven":False,
        "cm_internal_cause_proven":False,
        "tf_lookup_block_proven":False,
        "whole_system_cpu_freeze_proven":False,
        "host_clock_step_excluded":False,
        "single_causal_root_proven":False,
        "first_guard_internal_cm_hard_ttl_ms":HARD_CM_MS,
        "cm_release_target_ms":RELEASE_CM_MS,
        "owner_release_status":"AXIA_MVP_DEMO_ACCEPTED=HOLD",
    }

def _ordered(rows,field):
    if not isinstance(rows,list):
        return False
    vals=[r.get(field) if isinstance(r,dict) else None for r in rows]
    return all(_num(x) for x in vals) and all(a<b for a,b in zip(vals,vals[1:]))

def _gap(rows,field):
    vals=[r[field] for r in rows]
    return max((b-a for a,b in zip(vals,vals[1:])),default=None)

def _selected_quiet(rows,mid):
    # Adjacent selected observer callbacks that straddle first CM midpoint.
    v=[r["callback_offset_ms"] for r in rows]
    before=[x for x in v if x<=mid]
    after=[x for x in v if x>mid]
    if not before or not after:
        return None
    return (max(before),min(after))

def classify_first_gap(doc):
    out=_default()
    if not isinstance(doc,dict) or doc.get("schema")!=SCHEMA:
        return out
    if doc.get("first_guard_transition")!="UPSTREAM_STALE_AFTER_MOTION":
        return _default("FIRST_SAFETY_TRANSITION_NOT_PROVEN_HOLD")
    first_age=doc.get("first_guard_cm_age_ms")
    if (not _num(first_age) or first_age<=HARD_CM_MS
        or doc.get("guard_hard_ttl_ms")!=HARD_CM_MS
        or doc.get("cm_release_target_ms")!=RELEASE_CM_MS):
        return _default("GUARD_HARD_TTL_EVIDENCE_UNVERIFIED_HOLD")
    # This fixture explicitly says the host-clock step was not excluded.
    # A naked true is not proof of a reliable clock domain.
    if doc.get("host_clock_step_excluded") is not False:
        return _default("CLOCK_STEP_EVIDENCE_UNVERIFIED_HOLD")
    rpc=doc.get("native_stop_rpc")
    if (not isinstance(rpc,dict)
        or rpc.get("overlaps_first_cm_gap") is not False
        or rpc.get("relative_relation")!="FIRST_GAP_AFTER_RPC"
        or not _num(rpc.get("nearest_distance_ms"))):
        return _default("STOP_RPC_FIRST_GAP_RELATION_UNVERIFIED_HOLD")
    streams=doc.get("events_by_kind")
    if not isinstance(streams,dict) or any(not isinstance(streams.get(k),list) for k in KINDS):
        return out
    for name in KINDS:
        if not _ordered(streams[name],"callback_offset_ms"):
            return _default("OBSERVER_EVENT_ORDER_UNVERIFIED_HOLD")
    cm=streams["pre_guard"]
    upstream=streams["supervised"]
    if len(cm)<2 or len(upstream)<2:
        return _default("CM_OR_SUPERVISOR_RMW_DATA_MISSING_HOLD")
    for kind in ("pre_guard","supervised"):
        for key in ("rmw_source_offset_ms","publication_sequence_relative"):
            if not _ordered(streams[kind],key):
                return _default("RMW_SOURCE_SEQUENCE_INVALID_HOLD")
    if not _ordered(cm,"rmw_receive_offset_ms"):
        return _default("CM_RECEIPT_SEQUENCE_INVALID_HOLD")
    first=next(((a,b) for a,b in zip(cm,cm[1:])
                if b["rmw_source_offset_ms"]-a["rmw_source_offset_ms"]>=HARD_CM_MS),None)
    if first is None:
        return _default("FIRST_CM_RMW_SOURCE_GAP_NOT_REPRODUCED_HOLD")
    a,b=first
    if b["publication_sequence_relative"]-a["publication_sequence_relative"]!=1:
        return _default("CM_INTERMEDIATE_PUBLICATIONS_UNVERIFIED_HOLD")
    gap_source=b["rmw_source_offset_ms"]-a["rmw_source_offset_ms"]
    gap_receive=b["rmw_receive_offset_ms"]-a["rmw_receive_offset_ms"]
    gap_callback=b["callback_offset_ms"]-a["callback_offset_ms"]
    if not (gap_source>=HARD_CM_MS and gap_receive>=0 and gap_callback>=0):
        return _default("CM_TIME_DOMAIN_GAP_INVALID_HOLD")
    inside=[r for r in upstream
            if a["rmw_source_offset_ms"]<r["rmw_source_offset_ms"]<b["rmw_source_offset_ms"]]
    if len(inside)<2:
        return _default("SUPERVISOR_SOURCE_COVERAGE_MISSING_HOLD")
    source_edges=[a["rmw_source_offset_ms"]]+[x["rmw_source_offset_ms"] for x in inside]+[b["rmw_source_offset_ms"]]
    max_coverage=max(r-l for l,r in zip(source_edges,source_edges[1:]))
    # Largest *upstream callback* interval is matched to its own source pair,
    # not erroneously compared to a global unrelated source gap.
    sup_a,sup_b=max(zip(upstream,upstream[1:]),
        key=lambda p:p[1]["callback_offset_ms"]-p[0]["callback_offset_ms"])
    sup_callback=sup_b["callback_offset_ms"]-sup_a["callback_offset_ms"]
    sup_source=sup_b["rmw_source_offset_ms"]-sup_a["rmw_source_offset_ms"]
    mid=(a["callback_offset_ms"]+b["callback_offset_ms"])/2
    quiets={kind:_selected_quiet(streams[kind],mid) for kind in KINDS}
    valid=[v for v in quiets.values() if v is not None]
    if len(valid)!=len(KINDS):
        return _default("SELECTED_CROSS_CHANNEL_COVERAGE_INCOMPLETE_HOLD")
    start=max(x[0] for x in valid)
    end=min(x[1] for x in valid)
    quiet_ms=max(0.0,end-start)
    if not _num(quiet_ms):
        return out
    def r6(x):return round(x,6)
    return {
        **out,
        "status":"FIELD_CM_SOURCE_GAP_AND_OBSERVER_JITTER_CANDIDATE_HOLD",
        "first_guard_transition":"UPSTREAM_STALE_AFTER_MOTION",
        "first_guard_cm_age_ms":r6(first_age),
        "cm_source_gap_ms":r6(gap_source),
        "cm_receive_gap_ms":r6(gap_receive),
        "cm_observer_gap_ms":r6(gap_callback),
        "cm_publication_seq_delta":1,
        "upstream_publications_inside_cm_gap":len(inside),
        "upstream_max_source_coverage_gap_ms":r6(max_coverage),
        "upstream_continued_while_cm_source_gap":True,
        "cm_receive_minus_source_gap_ms":r6(gap_receive-gap_source),
        "cm_observer_minus_source_gap_ms":r6(gap_callback-gap_source),
        "observer_only_explanation":"INCONSISTENT_WITH_SOURCE_GAP",
        "supervisor_callback_gap_ms":r6(sup_callback),
        "same_supervisor_pair_source_gap_ms":r6(sup_source),
        "supervisor_pair_callback_minus_source_gap_ms":r6(sup_callback-sup_source),
        "selected_cross_channel_quiet_window_ms":r6(quiet_ms),
        "selected_quiet_channels_count":len(valid),
        "cross_channel_quiet_attribution":"OBSERVER_SHARED_DELAY_CANDIDATE_NOT_PROOF",
        "scan_selected_callback_gap_ms":r6(_gap(streams["scan"],"callback_offset_ms")),
        "odom_selected_callback_gap_ms":r6(_gap(streams["odom"],"callback_offset_ms")),
        "native_stop_rpc_overlaps_first_cm_gap":False,
        "native_stop_rpc_relative_relation":"FIRST_GAP_AFTER_RPC",
        "native_stop_rpc_nearest_gap_distance_ms":r6(rpc["nearest_distance_ms"]),
        "remaining_unknowns":[
          "CM_INPUT_SUBSCRIBER_CALLBACK_ARRIVAL",
          "CM_TF_LOOKUP_PROCESSING_DURATION",
          "CM_EXECUTOR_AND_SCHEDULER_AT_FIRST_GAP",
          "HOST_CLOCK_STEP_EXCLUSION_NOT_PROVEN",
        ],
    }

def main():
    if len(sys.argv)!=2:
        print("USAGE: python3 g07_cycle21_first_gap_parity.py sanitized_numeric_fixture.json",file=sys.stderr)
        return 2
    p=Path(sys.argv[1])
    try:
        if p.is_symlink() or not p.is_file():
            raise ValueError("INPUT_UNTRUSTED")
        doc=json.loads(p.read_text(encoding="utf-8"))
        r=classify_first_gap(doc)
    except (OSError,ValueError,UnicodeError) as exc:
        r=_default("INPUT_UNVERIFIED_HOLD_"+type(exc).__name__)
    print("AXIA_G07_CYCLE21_FIRST_MULTICHANNEL_GAP "+json.dumps(r,sort_keys=True))
    print("AXIA_MVP_DEMO_ACCEPTED=HOLD")
    return 0 if r["status"]=="FIELD_CM_SOURCE_GAP_AND_OBSERVER_JITTER_CANDIDATE_HOLD" else 3

if __name__=="__main__":
    raise SystemExit(main())
