#!/usr/bin/env python3
"""First real G07 ROS source-vs-RMW-receive-vs-Observer callback timing boundary.

Only reads sealed actual_ros_events.jsonl from existing G07 observer.
No ROS subscriptions, publishers, Goal, policy adjustment or private raw output.
CM/Guard safety truth must still come from original native Guard + rosbag.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

LIMITS={"scan":.3,"odom":.3,"supervised":.15,"pre_guard":.15}

def _f(x):
    return type(x) in (int,float) and math.isfinite(x)

def _ms(x):
    return round(1000*x,6) if _f(x) and x>=0 else None

def analyze_delivery(events):
    result={
        "schema":"axia.d06.first_source_receive_callback_g07_v1",
        "status":"NO_ACTUAL_GOAL",
        "first_boundary":None,
        "guard_received_same_delay_proven":False,
        "sensor_source_stalled_proven":False,
        "safety_pass":False,
        "owner_l3_accepted":False,
        "certified_estop":False,
    }
    if not isinstance(events,list):
        return result
    goals=[e["t"] for e in events if isinstance(e,dict)
           and e.get("kind")=="owner_goal_published" and _f(e.get("t"))]
    if len(goals)!=1:
        return result
    goal=goals[0]
    found=[]
    for kind,limit in LIMITS.items():
        rows=sorted((e for e in events
                     if isinstance(e,dict) and e.get("kind")==kind
                     and _f(e.get("t")) and e["t"]>=goal),
                    key=lambda e:e["t"])
        for a,b in zip(rows,rows[1:]):
            cb=b["t"]-a["t"]
            valid=all(type(r.get(key)) is int and r[key]>=0
                      for r in (a,b)
                      for key in ("rmw_source_ns","rmw_received_ns",
                                  "rmw_publication_seq"))
            src=(b["rmw_source_ns"]-a["rmw_source_ns"])/1e9 if valid else None
            rec=(b["rmw_received_ns"]-a["rmw_received_ns"])/1e9 if valid else None
            if (cb<=limit and (src is None or src<=limit)
                    and (rec is None or rec<=limit)):
                continue
            if not valid:
                classification="RMW_METADATA_UNVERIFIED"
            elif b["rmw_publication_seq"]-a["rmw_publication_seq"]!=1:
                classification="INTERMEDIATE_PUBLICATIONS_UNOBSERVED"
            elif src is None or rec is None or src<0 or rec<0:
                classification="RMW_METADATA_UNVERIFIED"
            elif src>limit:
                classification="PUBLISH_SOURCE_GAP"
            elif rec>limit:
                classification="RMW_RECEIVE_GAP"
            elif cb>limit:
                classification="OBSERVER_CALLBACK_GAP"
            else:
                continue
            found.append((b["t"],{
                "channel":kind,
                "classification":classification,
                "callback_gap_ms":_ms(cb),
                "source_gap_ms":_ms(src),
                "received_gap_ms":_ms(rec),
                "limit_ms":round(limit*1000,3),
            }))
            break
    if found:
        result["first_boundary"]=min(found,key=lambda x:x[0])[1]
        result["status"]="HOLD_G07_FIRST_SOURCE_RECEIVE_OR_OBSERVER_TIMING"
    else:
        result["status"]="NO_FIRST_DELIVERY_VIOLATION_OBSERVED_NOT_ACCEPTED"
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--events",type=Path,required=True)
    args=p.parse_args()
    try:
        if args.events.is_symlink():
            raise ValueError("SYMLINK")
        rows=[json.loads(line) for line in
              args.events.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError,ValueError,TypeError,UnicodeError):
        rows=[]
    outcome=analyze_delivery(rows)
    print("D06_G07_FIRST_SOURCE_RECEIVE_CALLBACK_BOUNDARY "+
          json.dumps(outcome,sort_keys=True),flush=True)
    # Diagnostic never upgrades the original safety/physical acceptance.
    return 0

if __name__=="__main__":
    raise SystemExit(main())
