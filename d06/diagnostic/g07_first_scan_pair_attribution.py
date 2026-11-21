#!/usr/bin/env python3
"""Fail-closed first Scan callback/RMW/independent rosbag boundary audit.

Native evidence has three distinct clocks:
  - ROS callback host monotonic (only delta, never subtract from RMW);
  - RMW source/received ns (intervals only, do not compare absolutes);
  - independent rosbag recorder receive system ns (intervals only).
The same Scan Header simulation stamp joins the two recorder observations,
NOT a DDS publication sequence across processes. A recorded max Clock/Odom
gap is NOT a match to the first Scan/Clock window.
This diagnostic NEVER grants Goal, releases Owner or changes any TTL.
"""
import argparse
import json
import math
from pathlib import Path


def _finite_pos(value):
    return type(value) in (int,float) and math.isfinite(value) and value>0


def _bounded_ms(value):
    return _finite_pos(value) and value<10000


def _load(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size>65536:
        return {}
    try:
        value=json.loads(path.read_text())
        return value if isinstance(value,dict) else {}
    except (OSError,UnicodeError,ValueError):
        return {}


def assess(pregoal,bag):
    """Pure evidence classifier. No absolute cross-domain timestamp math."""
    result={
        "schema":"axia.g07.first_scan_rmw_bag_attribution.v1",
        "release":"HOLD","root_cause":"UNDETERMINED",
        "root_cause_proven":False,"executor_root_proven":False,
        "publisher_root_proven":False,"gazebo_bridge_root_proven":False,
        "exact_publication_cross_process_proven":False,
        "same_first_clock_rosbag_pair_proven":False,
        "same_first_odom_rosbag_pair_proven":False,
        "owner_l3_accepted":False,"certified_estop":False,
        "safety_ttl_changed":False,
        "first_violation_topic":None,"first_violation_ms":None,
        "first_scan_observer_gap_ms":None,"scan_header_sim_gap_ms":None,
        "independent_exact_scan_bag_gap_ms":None,
        "independent_bag_clock_session_max_ms":None,
        "independent_bag_odom_session_max_ms":None,
        "rmw_source_gap_ms":None,"rmw_received_gap_ms":None,
        "rmw_publication_seq_gap":None,
        "rmw_interval_class":"RMW_INTERVAL_UNAVAILABLE_HOLD",
        "scan_rosbag_pair_class":"EXACT_SCAN_HEADER_PAIR_UNAVAILABLE_HOLD",
        "first_safety_state_transition":"UNVERIFIED",
        "pregoal_goal_sent":"UNVERIFIED"
    }
    if not isinstance(pregoal,dict) or not isinstance(bag,dict):
        return result
    if pregoal.get("goal_sent") is False and bag.get("goal_sent") is False:
        result["pregoal_goal_sent"]=False
        result["first_safety_state_transition"]="NOT_CAPTURED_BEFORE_GOAL"
    first=pregoal.get("first_delivery_violation")
    if isinstance(first,dict) and first.get("channel") in (
            "clock","odom","scan","safety_scan"):
        gap=first.get("gap_ms")
        if _bounded_ms(gap) and gap>300:
            result["first_violation_topic"]=first["channel"]
            result["first_violation_ms"]=round(float(gap),6)

    scan=pregoal.get("first_scan_timing_boundary")
    if not isinstance(scan,dict) or scan.get("topic") not in ("scan","safety_scan"):
        return result
    observer=scan.get("gap_ms")
    header=scan.get("header_sim_gap_ms")
    if not _bounded_ms(observer) or not _bounded_ms(header):
        return result
    result["first_scan_observer_gap_ms"]=round(float(observer),6)
    result["scan_header_sim_gap_ms"]=round(float(header),6)

    # The bag classifier already requires two UNIQUE exact header stamps.
    # These are the same Scan headers, but publication GID/seq is not known
    # in the rosbag: no cross-process DDS publication exact pair claim.
    matched=(bag.get("matched_exact_first_header_pair") is True
             and bag.get("same_header_pair_rosbag_timebase_only") is True
             and _bounded_ms(bag.get("expected_first_scan_header_gap_ms"))
             and abs(bag["expected_first_scan_header_gap_ms"]-header)<.01)
    if matched and _bounded_ms(bag.get("independent_bag_scan_gap_ms")):
        bag_ms=bag["independent_bag_scan_gap_ms"]
        result["independent_exact_scan_bag_gap_ms"]=round(float(bag_ms),6)
        if observer>300 and bag_ms<=300:
            result["scan_rosbag_pair_class"]=(
                "OBSERVER_CALLBACK_GAP_NOT_SEEN_IN_BAG_CANDIDATE_HOLD")
        elif bag_ms>300:
            result["scan_rosbag_pair_class"]=(
                "BAG_EXACT_SCAN_RX_GAP_CANDIDATE_HOLD")
        else:
            result["scan_rosbag_pair_class"]="BAG_EXACT_SCAN_PAIR_WITHIN_TTL_HOLD"
        # Session max of Clock/Odom is NOT a same-header first pair join.
        for topic in ("clock","odom"):
            value=bag.get("independent_bag_"+topic+"_max_gap_ms")
            if _bounded_ms(value):
                result["independent_bag_"+topic+"_session_max_ms"]=round(float(value),6)

    rmw=pregoal.get("first_scan_rmw_pair")
    if not isinstance(rmw,dict) or not matched:
        return result
    source=rmw.get("source_gap_ms")
    receive=rmw.get("received_gap_ms")
    seq=rmw.get("publication_seq_gap")
    rmw_obs=rmw.get("observer_gap_ms")
    rmw_head=rmw.get("header_sim_gap_ms")
    if (not all(_bounded_ms(x) for x in (source,receive,rmw_obs,rmw_head))
            or type(seq) is not int or seq!=1
            or abs(float(rmw_obs)-observer)>.01
            or abs(float(rmw_head)-header)>.01):
        return result
    result["rmw_source_gap_ms"]=round(float(source),6)
    result["rmw_received_gap_ms"]=round(float(receive),6)
    result["rmw_publication_seq_gap"]=seq
    if source>300:
        result["rmw_interval_class"]="SOURCE_INTERVAL_OVERRUN_CANDIDATE_HOLD"
    elif receive>300:
        result["rmw_interval_class"]="RMW_RECEIVED_INTERVAL_OVERRUN_CANDIDATE_HOLD"
    elif observer>300:
        result["rmw_interval_class"]=(
            "AFTER_RMW_TIMESTAMP_BEFORE_CALLBACK_CANDIDATE_HOLD")
    else:
        result["rmw_interval_class"]="RMW_EXACT_PAIR_WITHIN_TTL_HOLD"
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pregoal",type=Path,required=True)
    p.add_argument("--bag",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    v=assess(_load(a.pregoal),_load(a.bag))
    # Strict numeric allowlist above; no scan ranges, UUID, raw bag or paths.
    s=json.dumps(v,sort_keys=True,allow_nan=False,indent=2)+"\n"
    if len(s.encode())>8192:
        raise SystemExit("G07_DIAGNOSTIC_OUTPUT_SIZE_HOLD")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(s)
    print("AXIA_G07_FIRST_SCAN_RMW_BAG_ATTRIBUTION "+json.dumps(v,sort_keys=True))
    return 0  # Diagnostic status=HOLD; actual strict safety gate remains separate.


if __name__=="__main__":
    raise SystemExit(main())
