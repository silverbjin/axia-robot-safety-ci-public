#!/usr/bin/env python3
"""Fail-closed exact Cycle16 L2 gate for ONE WSLg candidate, never L3 acceptance.

Authoritative CI run is checked independently by Owner bootstrap with gh api.
This pure checker never operates ROS, modifies Guard/CM or removes past attempts.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

PRIVATE="01d45d46b6eb6a05b1bd313d73f1fc3549575545"
TREE="38de92dda3c17221b337f140bbc1b2aecd805da4"
CI_RUN=43727149856
L2_WORKFLOW="fa05a437db3b55d3e5e242322a4b66b7f71ae601"
RUNTIME_DIGEST="sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e"
EXACT={
    "schema":"axia.g07.cycle16_owner_ci_gate_v3",
    "status":"ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY",
    "ci_l2_run_id":CI_RUN,
    "ci_l2_workflow_sha":L2_WORKFLOW,
    "ci_l2_conclusion":"success",
    "instructor_source_sha":PRIVATE,
    "instructor_tree_sha":TREE,
    "runtime_base_digest":RUNTIME_DIGEST,
    "actual_gazebo_harmonic_nav2_one_goal":True,
    "real_gui_windows_before_goal":True,
    "real_scan_during_goal":True,
    "first_guard_latch":None,
    "navigation_shutdown_ack":True,
    "localization_shutdown_ack":True,
    "exact_goal_canceled":True,
    "cm_exit_code":0,
    "native_s02_positive_contacts":0,
    "original_rosbag_topic_count":14,
    "owner_manual_attempts_allowed":1,
    "owner_wslg_verified":False,
    "owner_l3_accepted":False,
    "full_demo_accepted":False,
    "certified_estop":False,
    "private_originals_uploaded_to_public":False,
}
LIMITS_MS={
    "cm":120,"guard":120,"source":120,"supervisor":120,
    "scan":240,"odom":240,"clock":240
}
def verify_cycle16_gate(row):
    hold={"status":"HOLD_INVALID_CYCLE16_CI_L2_OR_MARGIN",
          "manual_attempt_allowed":False, "owner_l3_accepted":False,
          "certified_estop":False, "full_demo_accepted":False,
          "no_ros_no_goal":True}
    if type(row) is not dict:
        return hold
    if any(type(row.get(k)) is not type(v) or row.get(k)!=v for k,v in EXACT.items()):
        return hold
    periods=row.get("max_intervals_ms")
    if type(periods) is not dict or set(periods)!=set(LIMITS_MS):
        return hold
    if any(type(periods[k]) not in (int,float) or not math.isfinite(periods[k])
           or not 0<=periods[k]<LIMITS_MS[k] for k in LIMITS_MS):
        return hold
    dwell=row.get("odom_stopped_dwell_sec")
    if type(dwell) not in (int,float) or not math.isfinite(dwell) or dwell<1.0:
        return hold
    return {**hold,"status":"ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY",
            "manual_attempt_allowed":True,"ci_run":CI_RUN,
            "safety_hard_cm_ms":150,"release_target_cm_ms":120,
            "field_wslg_verified":False,"owner_attempts_remaining":1}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gate",type=Path,required=True)
    p.add_argument("--private-sha",required=True)
    p.add_argument("--ci-run",required=True,type=int)
    p.add_argument("--private-tree",default=TREE)
    args=p.parse_args()
    row=None
    if args.private_sha==PRIVATE and args.private_tree==TREE and args.ci_run==CI_RUN:
        try:
            if args.gate.is_symlink() or not args.gate.is_file():
                raise ValueError("UNTRUSTED_GATE")
            row=json.loads(args.gate.read_text(encoding="utf-8"))
        except (OSError,ValueError,UnicodeError):
            row=None
    result=verify_cycle16_gate(row)
    print("AXIA_G07_CYCLE16_OWNER_GATE "+json.dumps(result,sort_keys=True),flush=True)
    print("AXIA_G07_OWNER_NOT_ACCEPTED WSLG_NOT_RUN CERTIFIED_ESTOP=false",flush=True)
    return 0 if result["manual_attempt_allowed"] else 3

if __name__=="__main__":
    raise SystemExit(main())
