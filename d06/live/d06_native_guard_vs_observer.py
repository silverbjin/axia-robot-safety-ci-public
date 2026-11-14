#!/usr/bin/env python3
"""D06 native Guard CM/Supervisor receipt versus read-only Observer.

Only existing G07 original event ledger. The G07-only Guard directly counts
per-source subscriber callback gaps and publishes them in the existing
/axia/p2/base_guard status, without changing safety policy or QoS.
No private raw logs, Goal/ROS actions, or automatic acceptance.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

SCHEMA="axia.g07.guard_native_callback_intervals_v1"

def _num(v):
    return type(v) in (float,int) and math.isfinite(v) and v>=0

def _counter(v):
    return type(v) is int and v>=0

def _snapshot(e):
    if not isinstance(e,dict) or e.get("kind")!="guard" or not _num(e.get("t")):
        return None
    data=e.get("data")
    if not isinstance(data,dict):
        return None
    info=data.get("native_input_timing")
    if not isinstance(info,dict) or info.get("schema")!=SCHEMA:
        return None
    cm=info.get("cm_callback_gaps_over_150ms")
    sup=info.get("supervisor_callback_gaps_over_150ms")
    if not (_counter(cm) and _counter(sup)):
        return None
    return {"t":e["t"],"cm":cm,"supervisor":sup,
            "cm_max":info.get("cm_callback_max_gap_sec"),
            "supervisor_max":info.get("supervisor_callback_max_gap_sec"),
            "latched":data.get("latched") is True}

def inspect_native_guard(events):
    report={
        "schema":"axia.d06.native_guard_vs_observer_receipt_v1",
        "status":"NATIVE_GUARD_RECEIPT_UNVERIFIED",
        "native_cm_gap_count_added_since_goal":None,
        "native_supervisor_gap_count_added_since_goal":None,
        "native_cm_callback_max_gap_ms":None,
        "native_supervisor_callback_max_gap_ms":None,
        "native_guard_latch_observed":False,
        "observer_cm_gap_proves_guard_delay":False,
        "safety_pass":False,
        "owner_l3_accepted":False,
        "certified_estop":False,
    }
    if not isinstance(events,list):
        return report
    goals=[e["t"] for e in events if isinstance(e,dict)
           and e.get("kind")=="owner_goal_published" and _num(e.get("t"))]
    if len(goals)!=1:
        return report
    goal=goals[0]
    raw_guard=[e for e in events if isinstance(e,dict)
               and e.get("kind")=="guard" and _num(e.get("t"))
               and e["t"]>=goal and isinstance(e.get("data"),dict)]
    if any(e["data"].get("latched") is True for e in raw_guard):
        report["native_guard_latch_observed"]=True
        report["status"]="HOLD_NATIVE_GUARD_FIRST_LATCH"
        return report
    snapshots=sorted((x for row in events if (x:=_snapshot(row)) is not None),
                     key=lambda x:x["t"])
    before=[x for x in snapshots if x["t"]<goal]
    after=[x for x in snapshots if x["t"]>=goal]
    if not before or not after:
        return report
    initial=before[-1]
    final=after[-1]
    cm=final["cm"]-initial["cm"]
    sup=final["supervisor"]-initial["supervisor"]
    if cm<0 or sup<0:
        return report
    report["native_cm_gap_count_added_since_goal"]=cm
    report["native_supervisor_gap_count_added_since_goal"]=sup
    if _num(final["cm_max"]):
        report["native_cm_callback_max_gap_ms"]=round(final["cm_max"]*1000,3)
    if _num(final["supervisor_max"]):
        report["native_supervisor_callback_max_gap_ms"]=round(final["supervisor_max"]*1000,3)
    # A CM >150ms gap is a real direct Guard callback delivery boundary,
    # even if a separate Observer's callbacks were regular.
    if cm>0:
        report["status"]="HOLD_NATIVE_GUARD_CM_INPUT_GAP_150MS"
    elif sup>0:
        report["status"]="HOLD_NATIVE_GUARD_SUPERVISOR_INPUT_GAP_150MS"
    else:
        report["status"]="NATIVE_GUARD_INPUT_GAPS_NOT_OBSERVED"
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--events",type=Path,required=True)
    args=p.parse_args()
    try:
        if args.events.is_symlink():
            raise ValueError("SYMLINK")
        rows=[json.loads(line) for line in
              args.events.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError,UnicodeError,ValueError,TypeError):
        rows=[]
    result=inspect_native_guard(rows)
    print("D06_G07_NATIVE_GUARD_VS_OBSERVER "
          +json.dumps(result,sort_keys=True),flush=True)
    # This NEVER overrides original Safety Supervisor/Guard/G07 L2 oracle.
    return 0

if __name__=="__main__":
    raise SystemExit(main())
