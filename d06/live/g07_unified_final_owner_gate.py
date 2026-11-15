#!/usr/bin/env python3
"""Pure fail-closed AXIA G07 source-locked CI receipt check. NO ROS/Goal."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

INSTRUCTOR_SHA="db1eec05e01e1db0d0d2e0c05610806ef4e499f9"
INSTRUCTOR_TREE="005cc352d63067beb9d34397e51b51f7974ce7ef"
P4_RELEASE_SHA="2bb0a46dd1eccdce364ccc9faeb4d5650bfb99f2"
CI_L2_RUN=43685818018

def _number(v):
    return type(v) in (int,float) and math.isfinite(v) and v>=0

def verify_gate(gate):
    hold={"status":"HOLD_UNVERIFIED_CI_GUI_L2_OR_SOURCE",
          "manual_attempt_allowed":False,
          "owner_l3_accepted":False,"full_demo_accepted":False,
          "certified_estop":False}
    if type(gate) is not dict:
        return hold
    exact={
        "schema":"axia.g07.unified_final_owner_ci_gate_v1",
        "status":"ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY",
        "owner_manual_attempts_allowed":1,
        "ci_gui_l2_run_id":CI_L2_RUN,
        "ci_gui_l2_workflow_sha":P4_RELEASE_SHA,
        "ci_gui_l2_conclusion":"success",
        "earlier_p4_headless_ci_run_id":43674784552,
        "public_p4_release_sha":P4_RELEASE_SHA,
        "instructor_source_sha":INSTRUCTOR_SHA,
        "instructor_tree_sha":INSTRUCTOR_TREE,
        "runtime_base_digest":"sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e",
        "actual_gazebo_harmonic_nav2_one_goal":True,
        "real_gui_windows_before_goal":True,
        "real_scan_during_goal":True,
        "first_guard_latch":None,
        "native_s02_positive_contacts":0,
        "original_rosbag_topic_count":14,
        "navigation_shutdown_ack":True,
        "localization_shutdown_ack":True,
        "cm_exit_code":0,
        "actual_wslg_verified":False,
        "owner_l3_accepted":False,
        "certified_estop":False,
        "full_demo_accepted":False,
        "no_raw_private_uploaded":True,
    }
    if any(type(gate.get(k)) is not type(v) or gate.get(k)!=v
           for k,v in exact.items() if k in gate) or any(k not in gate for k in exact):
        return hold
    limits={
        "cm_max_ms":150, "cm_rmw_source_max_ms":150,
        "guard_max_ms":150, "supervisor_max_ms":150,
        "scan_max_ms":300, "odom_max_ms":300, "clock_max_ms":300,
    }
    if any(not _number(gate.get(k)) or gate[k]>=limit
           for k,limit in limits.items()):
        return hold
    if not _number(gate.get("odom_stopped_dwell_sec")) or gate["odom_stopped_dwell_sec"]<1.0:
        return hold
    return {**hold, "status":"ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY",
            "manual_attempt_allowed":True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gate",type=Path,required=True)
    p.add_argument("--private-sha",required=True)
    p.add_argument("--release-sha",required=True)
    args=p.parse_args()
    if args.private_sha!=INSTRUCTOR_SHA or args.release_sha!=P4_RELEASE_SHA:
        print("AXIA_G07_FINAL_OWNER_PIN_MISMATCH_HOLD_NO_ROS_NO_GOAL")
        return 3
    try:
        if args.gate.is_symlink(): raise ValueError("GATE_SYMLINK")
        gate=json.loads(args.gate.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError):
        gate=None
    result=verify_gate(gate)
    print("AXIA_G07_FINAL_OWNER_GATE "+json.dumps(result,sort_keys=True))
    return 0 if result["manual_attempt_allowed"] else 3

if __name__=="__main__":
    raise SystemExit(main())
