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
            "cm_windows":info.get("cm_gap_windows"),
            "supervisor_windows":info.get("supervisor_gap_windows"),
            "cm_truncated":info.get("cm_gap_windows_truncated") is True,
            "supervisor_truncated":info.get("supervisor_gap_windows_truncated") is True,
            "latched":data.get("latched") is True}

def _gap_windows(raw):
    """Only bounded, self-consistent real callback interval metadata."""
    if not isinstance(raw,list) or len(raw)>8:
        return None
    clean=[]
    for item in raw:
        if not isinstance(item,dict):
            return None
        start=item.get("start_mono")
        end=item.get("end_mono")
        gap=item.get("gap_sec")
        if not all(type(x) in (int,float) and math.isfinite(x)
                   for x in (start,end,gap)):
            return None
        if end<=start or gap<=.15 or abs((end-start)-gap)>.00001:
            return None
        clean.append((round(start,6),round(end,6),gap))
    if len(set((a,b) for a,b,_ in clean))!=len(clean):
        return None
    return clean


def _scoped_new_gaps(baseline, latest, key, count, goal, active_end):
    """Count intervals entirely inside Goal..STOP, not a straddling 22s gap.

    Raw lifetime gap-counter delta alone can include a pre-Goal -> post-Goal
    first callback. When a bounded ring fails to cover all new increments,
    fail closed rather than mistaking missing records for no safety gap.
    """
    if count==0:
        return {"verified":True,"inside":0,"straddling":0,"max_ms":None}
    if active_end is None:
        return None
    old=_gap_windows(baseline.get(key+"_windows"))
    new=_gap_windows(latest.get(key+"_windows"))
    if old is None or new is None:
        return None
    old_keys={(start,end) for start,end,_ in old}
    changes=[row for row in new if (row[0],row[1]) not in old_keys]
    if len(changes)!=count:
        return None
    inside=[]
    crossing=0
    for start,end,duration in changes:
        if start>=goal and end<=active_end:
            inside.append(duration)
        elif start<goal<=end<=active_end:
            crossing+=1
        elif end<=goal:
            pass
        else:
            # A same-host clock anomaly or truncated boundary is unknown.
            return None
    return {"verified":True,"inside":len(inside),"straddling":crossing,
            "max_ms":round(max(inside)*1000,3) if inside else None}


def inspect_native_guard(events, *, active_end=None):
    report={
        "schema":"axia.d06.native_guard_vs_observer_receipt_v1",
        "status":"NATIVE_GUARD_RECEIPT_UNVERIFIED",
        "native_cm_gap_count_added_since_goal":None,
        "native_supervisor_gap_count_added_since_goal":None,
        "native_cm_goal_scoped_gap_count":None,
        "native_supervisor_goal_scoped_gap_count":None,
        "native_cm_boundary_straddling_gap_count":None,
        "native_cm_gap_window_coverage_verified":False,
        "native_supervisor_gap_window_coverage_verified":False,
        "native_cm_callback_max_gap_ms":None,
        "native_supervisor_callback_max_gap_ms":None,
        "native_guard_latch_observed":False,
        "active_goal_window_end_mono":None,
        "native_cm_last_receive_age_ms_at_latch":None,
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
    if active_end is not None:
        if not _num(active_end) or active_end<=goal:
            return report
        report["active_goal_window_end_mono"]=active_end
    raw_guard=[e for e in events if isinstance(e,dict)
               and e.get("kind")=="guard" and _num(e.get("t"))
               and e["t"]>=goal
               and (active_end is None or e["t"]<=active_end)
               and isinstance(e.get("data"),dict)]
    first_latch=next((e for e in sorted(raw_guard,key=lambda row:row["t"])
                      if e["data"].get("latched") is True),None)
    if first_latch is not None:
        report["native_guard_latch_observed"]=True
        report["status"]="HOLD_NATIVE_GUARD_FIRST_LATCH"
        diag=first_latch["data"].get("native_input_timing")
        if isinstance(diag,dict) and diag.get("schema")==SCHEMA:
            age=diag.get("cm_last_receive_age_sec")
            if _num(age):
                report["native_cm_last_receive_age_ms_at_latch"]=round(age*1000,3)
    snapshots=sorted((x for row in events if (x:=_snapshot(row)) is not None),
                     key=lambda x:x["t"])
    before=[x for x in snapshots if x["t"]<goal]
    after=[x for x in snapshots
           if x["t"]>=goal and (active_end is None or x["t"]<=active_end)]
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
    cm_scope=_scoped_new_gaps(initial,final,"cm",cm,goal,active_end)
    sup_scope=_scoped_new_gaps(initial,final,"supervisor",sup,goal,active_end)
    if cm_scope is not None:
        report["native_cm_gap_window_coverage_verified"]=cm_scope["verified"]
        report["native_cm_goal_scoped_gap_count"]=cm_scope["inside"]
        report["native_cm_boundary_straddling_gap_count"]=cm_scope["straddling"]
        report["native_cm_callback_max_gap_ms"]=cm_scope["max_ms"]
    if sup_scope is not None:
        report["native_supervisor_gap_window_coverage_verified"]=sup_scope["verified"]
        report["native_supervisor_goal_scoped_gap_count"]=sup_scope["inside"]
        report["native_supervisor_callback_max_gap_ms"]=sup_scope["max_ms"]
    # Goal/STOP-scoped diagnostics never modify Guard's native fail-closed
    # policy. First actual latch ALWAYS wins, even if a gap straddles t0.
    if report["native_guard_latch_observed"]:
        report["status"]="HOLD_NATIVE_GUARD_FIRST_LATCH"
    elif cm_scope is None and cm>0:
        report["status"]="HOLD_NATIVE_GUARD_CM_INPUT_GAP_150MS"
    elif sup_scope is None and sup>0:
        report["status"]="HOLD_NATIVE_GUARD_SUPERVISOR_INPUT_GAP_150MS"
    elif cm_scope is not None and cm_scope["inside"]>0:
        report["status"]="HOLD_NATIVE_GUARD_CM_INPUT_GAP_150MS"
    elif sup_scope is not None and sup_scope["inside"]>0:
        report["status"]="HOLD_NATIVE_GUARD_SUPERVISOR_INPUT_GAP_150MS"
    else:
        report["status"]="NATIVE_GUARD_INPUT_GAPS_NOT_OBSERVED"
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--events",type=Path,required=True)
    p.add_argument("--verdict",type=Path)
    args=p.parse_args()
    try:
        if args.events.is_symlink():
            raise ValueError("SYMLINK")
        rows=[json.loads(line) for line in
              args.events.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError,UnicodeError,ValueError,TypeError):
        rows=[]
    active_end=None
    if args.verdict is not None:
        try:
            if args.verdict.is_symlink():
                raise ValueError("SYMLINK")
            verdict=json.loads(args.verdict.read_text(encoding="utf-8"))
            active_end=verdict.get("native_delivery_window_end_mono")
            if not _num(active_end):
                active_end=-1
        except (OSError,ValueError,UnicodeError,TypeError,AttributeError):
            active_end=-1
    result=inspect_native_guard(rows,active_end=active_end)
    print("D06_G07_NATIVE_GUARD_VS_OBSERVER "
          +json.dumps(result,sort_keys=True),flush=True)
    # This NEVER overrides original Safety Supervisor/Guard/G07 L2 oracle.
    return 0

if __name__=="__main__":
    raise SystemExit(main())
