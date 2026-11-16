#!/usr/bin/env python3
"""Cycle33 EXACT public L2 receipt + Owner old-failure-preserving admission.

No ROS, Goal, GUI, private clone, lock writes or claimed E-Stop. A prior
failed DIFFERENT source SHA is retained, never rearmed automatically.
Only exact NEW source/tree + real Goal L2 + seven timing bounds permits
ONE controlling-TTY Owner WSLg candidate; Owner acceptance still HOLD.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

PRIVATE="420fd276ec1018f7fcc3f14873693cad02f080b4"
TREE="5ca77fb0bedd597b89b791e0931b42ea5a9cbdc9"
CI_RUN=43824411236
L2_WORKFLOW="f96add0db55ffba28943c5d3739703c3fc503a0b"
RUNTIME_DIGEST="sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e"
PRIOR_FAILED_SOURCE="01d45d46b6eb6a05b1bd313d73f1fc3549575545"
EXACT={
 "schema":"axia.g07.cycle33_owner_ci_gate_v1",
 "status":"ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY",
 "ci_l2_run_id":CI_RUN, "ci_l2_workflow_sha":L2_WORKFLOW,
 "ci_l2_conclusion":"success","instructor_source_sha":PRIVATE,
 "instructor_tree_sha":TREE,"runtime_base_digest":RUNTIME_DIGEST,
 "actual_gazebo_harmonic_nav2_one_goal":True,
 "real_gui_windows_before_goal":True,"real_scan_during_goal":True,
 "first_guard_latch":None, "navigation_shutdown_ack":True,
 "localization_shutdown_ack":True,"exact_goal_canceled":True,
 "cm_exit_code":0,"native_s02_positive_contacts":0,
 "original_rosbag_topic_count":14,
 "previous_owner_first_guard_cm_ttl_breach_acknowledged":True,
 "previous_owner_failed_source_sha":PRIOR_FAILED_SOURCE,
 "new_source_field_fix_causality_proven":False,
 "owner_manual_attempts_allowed":1,
 "owner_wslg_verified":False,"owner_l3_accepted":False,
 "full_demo_accepted":False,"certified_estop":False,
 "private_originals_uploaded_to_public":False,
}
BOUNDS_MS={"cm":120,"guard":120,"source":120,"supervisor":120,
 "scan":240,"odom":240,"clock":240}
def hold(status):
    return {"schema":"axia.g07.owner_l3_admission_v1","status":status,
            "manual_attempt_allowed":False,"owner_l3_accepted":False,
            "full_demo_accepted":False,"certified_estop":False,
            "no_ros_no_goal":True,"old_owner_evidence_preserved":True,
            "source_cm_gap_cause_proven":False}

def verify_gate(row):
    if type(row) is not dict or any(
        type(row.get(k)) is not type(v) or row[k]!=v for k,v in EXACT.items()):
        return hold("CYCLE33_CI_L2_SOURCE_OR_PROOF_INVALID_HOLD")
    periods=row.get("max_intervals_ms")
    if type(periods) is not dict or set(periods)!=set(BOUNDS_MS):
        return hold("CYCLE33_SEVEN_CHANNELS_MISSING_HOLD")
    if any(type(periods[k]) not in (int,float) or not math.isfinite(periods[k])
           or not 0<=periods[k]<BOUNDS_MS[k] for k in BOUNDS_MS):
        return hold("CYCLE33_SEVEN_CHANNEL_MARGIN_EXCEEDED_HOLD")
    rmw=row.get("cm_rmw_source_max_ms")
    if type(rmw) not in (int,float) or not math.isfinite(rmw) or not 0<rmw<120:
        return hold("CYCLE33_CM_RMW_SOURCE_MARGIN_EXCEEDED_HOLD")
    dwell=row.get("odom_stopped_dwell_sec")
    iterations=row.get("native_s02_observed_iterations")
    if (type(dwell) not in (int,float) or not math.isfinite(dwell) or dwell<1.
        or type(iterations) is not int or iterations<100):
        return hold("CYCLE33_ODOM_DWELL_OR_CONTACT_WINDOW_INVALID_HOLD")
    return {**hold("ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY"),
            "manual_attempt_allowed":True,"owner_attempts_remaining":1,
            "ci_run":CI_RUN,"ci_source_sha":PRIVATE,
            "release_target_cm_ms":120,"guard_hard_ttl_ms":150,
            "ci_cm_observer_max_ms":round(periods["cm"],6),
            "ci_cm_rmw_source_max_ms":round(rmw,6),
            "field_wslg_verified":False}

def assess_owner_home(gate,home:Path):
    result=verify_gate(gate)
    if not result["manual_attempt_allowed"]:
        return result
    if (not isinstance(home,Path) or home.is_symlink()
        or not home.is_dir() or str(home)=="/"):
        return hold("CYCLE33_OWNER_HOME_INVALID_HOLD")
    root=home/".axia_g07_final_owner_attempts"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        return hold("CYCLE33_ATTEMPT_STATE_UNTRUSTED_HOLD")
    attempt=root/(PRIVATE+"-"+str(CI_RUN))
    if attempt.is_symlink() or (attempt.exists() and not attempt.is_dir()):
        return hold("CYCLE33_ATTEMPT_STATE_UNTRUSTED_HOLD")
    if attempt.is_dir():
        return hold("CYCLE33_ALREADY_ATTEMPTED_SAME_SOURCE_RUN_HOLD")
    # Never delete, write, or depend on old SHA attempts for authorization.
    return result

def _read_gate(p:Path):
    try:
        if p.is_symlink() or not p.is_file():
            return None
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError):
        return None

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gate",required=True,type=Path)
    p.add_argument("--private-sha",required=True)
    p.add_argument("--private-tree",default=TREE)
    p.add_argument("--ci-run",required=True,type=int)
    p.add_argument("--home",type=Path)
    args=p.parse_args()
    row=(_read_gate(args.gate)
         if args.private_sha==PRIVATE and args.private_tree==TREE
         and args.ci_run==CI_RUN else None)
    outcome=(assess_owner_home(row,args.home)
             if args.home is not None else verify_gate(row))
    print("AXIA_G07_CYCLE33_OWNER_GATE "+json.dumps(outcome,sort_keys=True),flush=True)
    print("AXIA_G07_OWNER_WSLG_NOT_YET_VERIFIED CERTIFIED_ESTOP=false",flush=True)
    print("AXIA_MVP_DEMO_ACCEPTED=HOLD",flush=True)
    return 0 if outcome["manual_attempt_allowed"] else 3

if __name__=="__main__":
    raise SystemExit(main())
