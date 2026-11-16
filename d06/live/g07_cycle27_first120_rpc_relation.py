#!/usr/bin/env python3
"""First 120ms CM source-gap vs native STOP RPC, read-only actual L2 evidence.

A prior 150ms hard-TTL classifier missed >=120ms and <150ms releases.
No ROS, no Goal, no source/Guard changes. RMW timestamps are SYSTEM epoch;
callback and STOP RPC timestamps MONOTONIC. Only compare within a domain.
"""
import argparse
import json
import math
from pathlib import Path
import sys

CM_RELEASE_MS=120
def number(v):
    return type(v) in (int,float) and math.isfinite(v)

def hold(status,**extra):
    return {
        "schema":"axia.g07.cycle27.cm_120ms_first_rpc_relation_v1",
        "status":status,
        "owner_goal_authorized":False,
        "owner_l3_accepted":False,
        "certified_estop":False,
        "cm_input_callback_cause_proven":False,
        "rpc_caused_cm_gap_proven":False,
        "no_new_ros_goal":True,
        "source_clock_domain":"RMW_HOST_SYSTEM_RELATIVE_ONLY",
        "callback_rpc_clock_domain":"HOST_MONOTONIC_RELATIVE_ONLY",
        "host_system_clock_step_excluded":False,
        **extra,
    }

def classify(events,report):
    if type(events) is not list or type(report) is not dict:
        return hold("ORIGINAL_EVENTS_OR_RESULT_MISSING_HOLD")
    starts=[e.get("t") for e in events if type(e) is dict
            and e.get("kind")=="owner_goal_published" and number(e.get("t"))]
    if len(starts)!=1:
        return hold("GOAL_MARKER_MISSING_HOLD")
    start=starts[0]
    channel={"pre_guard":[],"supervised":[]}
    for event in events:
        if type(event) is not dict:
            return hold("ORIGINAL_EVENT_MALFORMED_HOLD")
        kind=event.get("kind")
        if kind not in channel:
            continue
        t=event.get("t")
        src=event.get("rmw_source_ns")
        recv=event.get("rmw_received_ns")
        seq=event.get("rmw_publication_seq")
        if not (number(t) and t>=start and type(src) is int and src>0
            and type(recv) is int and recv>=src and type(seq) is int and seq>=0):
            return hold("RMW_METADATA_MISSING_OR_INVALID_HOLD")
        channel[kind].append({"t":t,"source":src,"recv":recv,"seq":seq})
    cm=channel["pre_guard"]
    sup=channel["supervised"]
    if len(cm)<2:
        return hold("CM_SOURCE_METADATA_MISSING_HOLD")
    for rows in channel.values():
        if any(b["t"]<=a["t"] or b["source"]<=a["source"] or
               b["seq"]<=a["seq"] for a,b in zip(rows,rows[1:])):
            return hold("RMW_SEQUENCE_OR_CLOCK_DOMAIN_UNVERIFIED_HOLD")
    first=next(((a,b) for a,b in zip(cm,cm[1:])
                if b["source"]-a["source"] >= CM_RELEASE_MS*1000000),None)
    if first is None:
        return hold("NO_CM_120MS_SOURCE_GAP_SCOPED_CI_ONLY")
    a,b=first
    if not sup:
        return hold("SUPERVISOR_COVERAGE_UNVERIFIED_HOLD")
    inside=[e for e in sup if a["source"]<e["source"]<b["source"]]
    if len(inside)<2 or b["seq"]-a["seq"]!=1:
        return hold("CM_SOURCE_GAP_OR_UPSTREAM_SEQUENCE_UNVERIFIED_HOLD",
            first_cm_source_gap_ms=round((b["source"]-a["source"])/1e6,6))
    rpc=report.get("stop_native_rpc_monotonic_window")
    if not isinstance(rpc,dict) or not number(rpc.get("started_at")) or not number(rpc.get("ended_at")):
        return hold("CM_SOURCE_120MS_GAP_RPC_WINDOW_MISSING_HOLD")
    rpc_start=rpc["started_at"]
    rpc_end=rpc["ended_at"]
    if rpc_end<rpc_start or rpc_start<start:
        return hold("CM_SOURCE_120MS_GAP_RPC_MONOTONIC_UNVERIFIED_HOLD")
    left=a["t"];right=b["t"]
    overlap=max(left,rpc_start)<min(right,rpc_end)
    if overlap:
        relation="OVERLAPS_RPC"
        distance=0.
    elif right<=rpc_start:
        relation="BEFORE_RPC"
        distance=(rpc_start-right)*1000
    elif rpc_end<=left:
        relation="AFTER_RPC"
        distance=(left-rpc_end)*1000
    else:
        return hold("CM_SOURCE_120MS_GAP_RPC_RELATION_UNVERIFIED_HOLD")
    return hold("CM_SOURCE_120MS_GAP_"+relation+"_HOLD",
        first_cm_source_gap_ms=round((b["source"]-a["source"])/1e6,6),
        first_cm_receive_gap_ms=round((b["recv"]-a["recv"])/1e6,6),
        first_cm_observer_gap_ms=round((right-left)*1000,6),
        cm_publication_seq_delta=1,
        upstream_publications_inside_gap=len(inside),
        upstream_max_source_coverage_gap_ms=round(max(
            (z-y)/1e6 for y,z in zip(
                [a["source"]]+[r["source"] for r in inside],
                [r["source"] for r in inside]+[b["source"]])
        ),6),
        native_stop_rpc_overlap_candidate=overlap,
        native_rpc_nearest_distance_ms=round(distance,6),
        first_cm_gap_callback_offset_from_goal_ms=round((left-start)*1000,6),
        native_rpc_duration_ms=round((rpc_end-rpc_start)*1000,6),
    )

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--events",required=True,type=Path)
    p.add_argument("--result",required=True,type=Path)
    args=p.parse_args()
    try:
        if (args.events.is_symlink() or args.result.is_symlink()
            or args.events.stat().st_size>25*1024*1024
            or args.result.stat().st_size>2*1024*1024):
            raise ValueError("SOURCE_UNTRUSTED_OR_UNBOUNDED")
        rows=[json.loads(ln) for ln in args.events.read_text().splitlines()]
        report=json.loads(args.result.read_text())
        output=classify(rows,report)
    except (OSError,ValueError,UnicodeError) as exc:
        output=hold("ORIGINAL_DIAGNOSTIC_UNVERIFIED_"+type(exc).__name__)
    print("AXIA_G07_CYCLE27_FIRST_CM_120MS_SOURCE_RPC "+
          json.dumps(output,sort_keys=True),flush=True)
    print("AXIA_G07_CYCLE27_SCOPED_DIAGNOSTIC_ONLY_OWNER_WSL2_NOT_AUTHORIZED")
    print("AXIA_MVP_DEMO_ACCEPTED=HOLD")
    return 0 if output["status"].startswith("CM_SOURCE_120MS_GAP_") or                 output["status"]=="NO_CM_120MS_SOURCE_GAP_SCOPED_CI_ONLY" else 3

if __name__=="__main__":
    raise SystemExit(main())
