#!/usr/bin/env python3
"""Sealed actual G07: distinguish native Supervisor scan watchdog from Observer.

Read-only existing /axia/safety/state JSON recorded by the existing Observer.
Native scan callback timing counters originate inside the real Supervisor node.
Do NOT infer healthy Guard, actual /odom receipt, or safety acceptance from this.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path


def _num(value):
    return type(value) in (int,float) and math.isfinite(value) and value>=0


def _first_gap(rows, kind, goal, limit):
    ordered=sorted((x["t"] for x in rows if isinstance(x,dict)
                    and x.get("kind")==kind and _num(x.get("t"))
                    and x["t"]>=goal))
    breaches=[(b-a)*1000 for a,b in zip(ordered,ordered[1:]) if b-a>limit]
    return round(breaches[0],3) if breaches else None


def _snap(e):
    if not isinstance(e,dict) or e.get("kind")!="supervisor" or not _num(e.get("t")):
        return None
    data=e.get("data")
    if not isinstance(data,dict):
        return None
    diag=data.get("health_diagnostics")
    if not isinstance(diag,dict):
        return None
    count=diag.get("scan_callback_gaps_over_timeout")
    age=diag.get("scan_age_sec")
    if type(count) is not int or count<0 or not _num(age):
        return None
    return {"t":e["t"],"count":count,"age":age,
            "scan_ok":diag.get("scan_ok"),
            "scan_fault_code":data.get("scan_fault_code") or diag.get("scan_fault_code"),
            "state":data.get("state")}


def inspect_safety_scan(events):
    report={
        "schema":"axia.d06.native_supervisor_scan_vs_observer_v1",
        "status":"NATIVE_SUPERVISOR_SCAN_TIMING_UNVERIFIED",
        "observer_scan_first_gap_ms":None,
        "observer_odom_first_gap_ms":None,
        "native_scan_callback_gaps_added_since_goal":None,
        "native_scan_age_max_ms_since_goal":None,
        "native_scan_300ms_breach_proven":False,
        "native_odom_receipt_ttl_proven":False,
        "guard_received_same_delay_proven":False,
        "safety_pass":False,"owner_l3_accepted":False,"certified_estop":False,
    }
    if not isinstance(events,list):
        return report
    goals=[e["t"] for e in events if isinstance(e,dict)
           and e.get("kind")=="owner_goal_published" and _num(e.get("t"))]
    if len(goals)!=1:
        return report
    goal=goals[0]
    report["observer_scan_first_gap_ms"]=_first_gap(events,"scan",goal,.30)
    report["observer_odom_first_gap_ms"]=_first_gap(events,"odom",goal,.30)
    all_states=[snap for e in events if (snap:=_snap(e)) is not None]
    before=[x for x in all_states if x["t"]<goal]
    after=[x for x in all_states if x["t"]>=goal]
    if not before or not after:
        return report
    baseline=max(before,key=lambda x:x["t"])
    a=sorted(after,key=lambda x:x["t"])
    # Counters are cumulative and can contain a PRE-GOAL gap. Compare only
    # to the last pre-goal snapshot, never mistake that for a Goal violation.
    change=max(x["count"] for x in a)-baseline["count"]
    if change<0:
        return report
    report["native_scan_callback_gaps_added_since_goal"]=change
    report["native_scan_age_max_ms_since_goal"]=round(max(x["age"] for x in a)*1000,3)
    violated=(change>0 or any(x["age"]>.3 or
              x["scan_fault_code"] in ("SCAN_TIMEOUT","scan_stale")
              for x in a))
    if violated:
        report["native_scan_300ms_breach_proven"]=True
        report["status"]="HOLD_NATIVE_SUPERVISOR_SCAN_TTL_BREACH"
    elif report["observer_scan_first_gap_ms"] is not None:
        report["status"]="OBSERVER_SCAN_GAP_NO_NATIVE_SCAN_TTL_BREACH_OBSERVED"
    else:
        report["status"]="NO_NATIVE_SCAN_TTL_BREACH_OBSERVED_NOT_ACCEPTED"
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--events",type=Path,required=True)
    args=p.parse_args()
    try:
        if args.events.is_symlink():
            raise ValueError("SYMLINK")
        events=[json.loads(line) for line in
                args.events.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError,UnicodeError,TypeError,ValueError):
        events=[]
    print("D06_G07_NATIVE_SUPERVISOR_SCAN_VS_OBSERVER "+
          json.dumps(inspect_safety_scan(events),sort_keys=True),flush=True)
    # Never upgrades the full original Owner/CI safety or accepted gate.
    return 0


if __name__=="__main__":
    raise SystemExit(main())
