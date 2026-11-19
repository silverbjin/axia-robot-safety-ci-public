#!/usr/bin/env python3
"""Owner single-run first REAL Scan receive boundary vs bounded actual RMW rows.

Read-only diagnostic. Never infer a DDS bug or Collision Monitor safety TTL
from an observer receive gap. Exposes uncertainty explicitly.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

LIMIT_SEC=.5
OBSERVER="axia_d08_official_physical_replan_no_goal"
INDEPENDENT="axia_d08_independent_rx_no_goal"
MAX_ROWS_READ=24000


def _read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError,ValueError,TypeError):
        return {}


def collect_first_scan_boundary(run_dir):
    """Read existing Owner proof; first event by monotonic time, not largest gap."""
    root=Path(run_dir)/"live_evidence"
    candidates=[]
    checked=[]
    paths=[root/"official_path_phases"/"verdict.json"]
    paths.extend(sorted((root/"owner_replan_cycles").glob("cycle_[0-9][0-9][0-9][0-9]/verdict.json")))
    for path in paths:
        if not path.is_file():
            continue
        try:
            data=json.loads(path.read_text())
        except (OSError,ValueError):
            continue
        checked.append(str(path.relative_to(root)))
        w=data.get("first_scan_timing_boundary")
        if not isinstance(w,dict):
            continue
        try:
            start=float(w["previous_host_monotonic_sec"])
            end=float(w["current_host_monotonic_sec"])
            gap=float(w["receive_gap_sec"])
        except (KeyError,TypeError,ValueError,OverflowError):
            continue
        if not all(math.isfinite(v) for v in (start,end,gap)):
            continue
        if gap <= LIMIT_SEC or end<=start or abs((end-start)-gap)>.03:
            continue
        candidates.append({
            "kind":"ROS_LASERSCAN_FIRST_RECEIVE_GAP",
            "scope":str(path.parent.relative_to(root)),
            "host_start_sec":round(start,6),
            "host_end_sec":round(end,6),
            "gap_sec":round(gap,6),
            "previous_ros_stamp_ns":w.get("previous_ros_stamp_ns"),
            "current_ros_stamp_ns":w.get("current_ros_stamp_ns"),
            "header_sim_gap_sec":w.get("header_sim_gap_sec"),
            "limit_sec":LIMIT_SEC,
            "owner_goal_sent":False,
            "source_vs_transport_proven":False})
    # The existing initial-pose recovery is BEFORE Path/Goal and must be
    # preserved separately. It is not hidden or counted as an accepted run.
    preflight=_read(root/"official_nav2_before_path.json")
    recovery=((preflight.get("real_amcl_and_tf") or {})
             .get("live_scan_odom_at_localization") or {}).get("no_goal_pre_goal_recovery") or {}
    early=(recovery.get("historical_first_gaps") or {}).get("scan")
    if isinstance(early,dict):
        try:
            end=float(early["first_at_host_monotonic"])
            gap=float(early["gap_sec"])
            if math.isfinite(end) and math.isfinite(gap) and gap>LIMIT_SEC:
                candidates.append({
                    "kind":"ROS_LASERSCAN_FIRST_RECEIVE_GAP",
                    "scope":"initial_amcl_pregoal_recovery",
                    "host_start_sec":round(end-gap,6),
                    "host_end_sec":round(end,6),
                    "gap_sec":round(gap,6),
                    "limit_sec":LIMIT_SEC,
                    "owner_goal_sent":False,
                    "startup_or_recovery":True,
                    "source_vs_transport_proven":False})
        except (KeyError,TypeError,ValueError,OverflowError):
            pass
    if candidates:
        candidates.sort(key=lambda r:(r["host_end_sec"],r["host_start_sec"]))
        first=dict(candidates[0])
        first["available_first_boundaries_count"]=len(candidates)
        first["inspected_cycle_verdicts"]=checked[:64]
        first["retains_initial_recovery_boundary"]=any(
            c["scope"]=="initial_amcl_pregoal_recovery" for c in candidates)
        return first
    return {"kind":"NO_FIRST_SCAN_VIOLATION_IN_AVAILABLE_VERDICTS",
            "scope":"D08_NO_GOAL_READONLY",
            "inspected_cycle_verdicts":checked[:64],
            "observed_cycle_verdict_count":len(checked),
            "cause":"UNDETERMINED",
            "owner_wsl2_accepted":False}


def _stream_bracket(events,start,end):
    rows=sorted(events,key=lambda e:float(e["host_monotonic_sec"]))
    before=[r for r in rows if float(r["host_monotonic_sec"])<=start]
    after=[r for r in rows if float(r["host_monotonic_sec"])>=end-1e-6]
    if not before or not after:
        return {"bracketed":False,"gap_sec":None,"samples":len(rows)}
    a=float(before[-1]["host_monotonic_sec"])
    b=float(after[0]["host_monotonic_sec"])
    # Reject unrelated startup/teardown gaps >2s, even if the trace does
    # contain some samples on both sides of the first observer violation.
    if start-a>0.6 or b-end>0.6:
        return {"bracketed":False,"gap_sec":None,"samples":len(rows)}
    return {"bracketed":True,"gap_sec":round(b-a,6),
            "before_at":round(a,6),"after_at":round(b,6),
            "samples":len(rows),"event_matches_laserscan_header":False}


def correlate_first_boundary(first,events,capture_complete):
    """Classify candidates ONLY. A result is never L3 safety acceptance."""
    base={"status":"D08_OWNER_FIRST_SCAN_GAP_RMW_TRIAGE_NOT_SAFETY_PASS",
          "cause":"UNDETERMINED",
          "candidate":"EVIDENCE_INCOMPLETE",
          "first_500ms_violation_retained":first.get("kind")=="ROS_LASERSCAN_FIRST_RECEIVE_GAP",
          "owner_wsl2_accepted":False,
          "certified_estop":False,
          "cm_internal_receive_ttl_verified":False,
          "guard_ttl_verified":False,
          "rmw_trace_capture_complete":bool(capture_complete),
          "source_stamp_is_not_laserscan_header_stamp":True,
          "first_observer_gap":first}
    if first.get("kind")!="ROS_LASERSCAN_FIRST_RECEIVE_GAP":
        base["candidate"]="NO_FIRST_GAP_IN_AVAILABLE_VERDICTS"
        return base
    try:
        start=float(first["host_start_sec"]);end=float(first["host_end_sec"])
    except (KeyError,ValueError,TypeError):
        return base
    if not capture_complete or not 0<end-start<10:
        return base
    valid=[]
    for row in events[:MAX_ROWS_READ]:
        try:
            t=float(row["host_monotonic_sec"])
        except (KeyError,TypeError,ValueError):
            continue
        if not math.isfinite(t) or row.get("direction") not in ("publish","take"):
            continue
        valid.append(row)
    pubs=[r for r in valid if r["direction"]=="publish" and
          ("bridge" in (r.get("node") or "").lower()
           or (r.get("process") or "") in ("parameter_bridg","parameter_bridge"))]
    indep=[r for r in valid if r["direction"]=="take" and r.get("node")==INDEPENDENT]
    observer=[r for r in valid if r["direction"]=="take" and r.get("node")==OBSERVER]
    base["publisher"]=p=_stream_bracket(pubs,start,end)
    base["independent_ros"]=i=_stream_bracket(indep,start,end)
    base["original_observer"]=o=_stream_bracket(observer,start,end)
    base["publisher_window_bracketed"]=p["bracketed"]
    base["independent_window_bracketed"]=i["bracketed"]
    base["observer_window_bracketed"]=o["bracketed"]
    # Matching RMW source timestamp is corroborating evidence only: NOT
    # necessarily identical LaserScan.header.stamp or verified DDS residence.
    source_pub={}
    for x in pubs:
        key=x.get("source_timestamp")
        if key is not None:
            source_pub.setdefault(key,[]).append(x)
    near=[]
    for x in indep+observer:
        at=float(x["host_monotonic_sec"])
        if not start-.15<=at<=end+.15:
            continue
        pub=source_pub.get(x.get("source_timestamp"),[])
        if len(pub)==1:
            dt=at-float(pub[0]["host_monotonic_sec"])
            if 0<=dt<=10 and len(near)<24:
                near.append({"receiver_node":x.get("node"),
                             "source_timestamp":x.get("source_timestamp"),
                             "source_to_take_sec":round(dt,6),
                             "receiver_at":round(at,6)})
    base["bounded_same_rmw_source_stamp_pairs_near_first_gap"]=near
    if not(p["bracketed"] and i["bracketed"] and o["bracketed"]):
        return base
    if p["gap_sec"]>LIMIT_SEC:
        base["candidate"]="RMW_PUBLISH_OR_UPSTREAM_SCHEDULING_DELAY_CANDIDATE"
    elif i["gap_sec"]>LIMIT_SEC:
        base["candidate"]="BRIDGE_RMW_OR_SHARED_HOST_RECEIVE_DELAY_CANDIDATE"
    elif o["gap_sec"]>LIMIT_SEC:
        base["candidate"]="OBSERVER_RMW_RECEIVE_OR_PROCESS_DELAY_CANDIDATE"
    else:
        base["candidate"]="OBSERVER_EXECUTOR_OR_DISPATCH_DELAY_CANDIDATE"
    base["first_gap_window_causally_bracketed_only"]=True
    return base


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--phase",choices=("select","finalize"),required=True)
    p.add_argument("--rows",type=Path)
    p.add_argument("--trace-summary",type=Path)
    args=p.parse_args()
    first=collect_first_scan_boundary(args.run)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    if args.phase=="select":
        obj=first
    else:
        rows=[]
        if args.rows and args.rows.is_file():
            with args.rows.open() as f:
                for n,line in enumerate(f):
                    if n>=MAX_ROWS_READ:break
                    try:rows.append(json.loads(line))
                    except ValueError:pass
        summary=_read(args.trace_summary) if args.trace_summary else {}
        source=(summary.get("rmw_scan_source_stamp_join") or {})
        obj=correlate_first_boundary(first,rows,
            bool(source.get("bounded_capture_complete") and rows))
        obj["source_sha"]="OWNER_RUN_SOURCE_PINNED_EXTERNALLY"
        obj["trace_event_count"]=len(rows)
        obj["raw_ctf_in_archive"]=False
        obj["native_gazebo_probe_in_owner_check"]=True
    args.out.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    print("D08_OWNER_FIRST_BOUNDARY_RMW_CAUSE_UNDETERMINED")
    print("D08_OWNER_FIRST_BOUNDARY_RMW_CANDIDATE="+obj.get("candidate","UNDETERMINED"))
if __name__=="__main__":
    main()
