#!/usr/bin/env python3
"""D06 PUBLIC CI only: read private sealed G07 L2 cleanup, print SAFE summary.

Never publishes ROS, changes Goal/Guard/TTL or reports accepted Owner L3.
The private source, rosbag, runner logs and checkout stay in sealed CI workspace.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

FAIL_MARKERS = (
    "G07_MOVING_GOAL_ORDERED_SHUTDOWN_BLOCKED",
    "G07_CI_OWNER_BAG_FORCED_TEARDOWN",
    "G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET",
    "P2_L2_FORCED_SIGKILL",
    "G07_REAL_SHUTDOWN_L2_NO_NAV2_ACK",
    "G07_REAL_SHUTDOWN_L2_CM_PROCESS_NONCLEAN",
)

def _json(path: Path):
    try:
        if path.is_symlink() or not path.is_file():
            return {}
        obj=json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj,dict) else {}
    except (ValueError,OSError,UnicodeError):
        return {}

def _text(path: Path):
    try:
        if path.is_symlink() or not path.is_file():
            return ""
        return path.read_text(encoding="utf-8",errors="replace")
    except OSError:
        return ""

def review_cleanup(root: Path, log_file: Path, rc_file: Path) -> dict:
    """First observed exit marker. Status is NEVER Owner acceptance."""
    root,log_file,rc_file=Path(root),Path(log_file),Path(rc_file)
    trace=_text(log_file)
    try:
        rc=int(_text(rc_file).strip())
    except ValueError:
        rc=None
    original=_json(root/"g07_ci_moving"/"ci_moving_goal_result.json")
    startup=_json(root/"startup_verdict.json")
    pregoal=_json(root/"g07_ci_pregoal"/"owner_pregoal_l2.json")
    # A later cleanup rc=3 must NEVER mask an earlier pre-Goal failure.
    # No Goal marker/result means the shutdown path is only a consequence.
    if not original or original.get("goal_sent") is not True:
        if startup.get("status") in ("BLOCKED","ERROR") or startup.get("failed_gate"):
            phase="PRE_GOAL_STARTUP"
            code="HOLD_PRE_GOAL_STARTUP"
            gate=(str(startup.get("failed_gate"))[:90] if startup.get("failed_gate")
                  else "UNCLASSIFIED_STARTUP_FAILURE")
        elif (startup.get("status")=="SMOKE_READY"
              and (root/"g07_ci_pregoal.log").is_file()):
            phase="PRE_GOAL_PHYSICAL"
            code="HOLD_PRE_GOAL_PHYSICAL"
            gate=("PREG0AL_PHYSICAL_L2"
                  if pregoal.get("status")!="P2_G07_OWNER_PREGOAL_L2_READY_NO_GOAL"
                  else "ACTUAL_GOAL_NOT_STARTED")
        else:
            phase="PRE_GOAL_UNCLASSIFIED"
            code="HOLD_PRE_GOAL_UNCLASSIFIED"
            gate=None
        return {
            "schema":"axia.d06.ci_actual_g07_cleanup_first_boundary_v1",
            "status":code,
            "first_failure_phase":phase,
            "first_failure_gate":gate,
            "original_g07_motion_candidate":False,
            "runner_rc":rc,
            "first_cleanup_failure":None,
            "native_nav2_lifecycle_ack":False,
            "native_cm_clean_exit":False,
            "launch_graceful_exit_marker":False,
            "full_run_pass":False,
            "owner_l3_accepted":False,
            "certified_estop":False,
            "no_raw_private_output":True,
        }
    shutdown=_json(root/"g07_ordered_shutdown.json")
    audit=_json(root/"g07_shutdown_audit.json")
    teardown=_text(root/"teardown.txt")
    hits=[(trace.index(m),m) for m in FAIL_MARKERS if m in trace]
    first=min(hits)[1] if hits else None
    if first is None and rc!=0:
        if shutdown.get("status")!="NAV2_LIFECYCLE_SHUTDOWN_ACK":
            first="ORDERED_SHUTDOWN_ACK_MISSING_OR_UNVERIFIED"
        elif "P2_L2_FORCED" in teardown:
            first="LAUNCH_GRACEFUL_TEARDOWN_UNVERIFIED"
        elif audit.get("status")!="SHUTDOWN_CLEAN_CANDIDATE":
            first="CM_EXIT_AUDIT_MISSING_OR_NONCLEAN"
        else:
            first="POST_GOAL_RC_NONZERO_CAUSE_UNVERIFIED"
    nav_ack=(shutdown.get("status")=="NAV2_LIFECYCLE_SHUTDOWN_ACK"
             and shutdown.get("navigation_ack") is True
             and shutdown.get("localization_ack") is True)
    cm_exit=(audit.get("status")=="SHUTDOWN_CLEAN_CANDIDATE"
             and audit.get("cm_exit_code")==0)
    clean=(rc==0 and nav_ack and cm_exit
           and "P2_L2_GRACEFUL_TEARDOWN" in teardown
           and not hits)
    return {
        "schema":"axia.d06.ci_actual_g07_cleanup_first_boundary_v1",
        "first_failure_phase":"POST_GOAL_CLEANUP",
        "first_failure_gate":None,
        "status":("CI_G07_L2_CLEANUP_CANDIDATE_ONLY"
                  if clean else "HOLD_POST_GOAL_CLEANUP"),
        "original_g07_motion_candidate":(
            original.get("status")=="CI_GAZEBO_MOVING_GOAL_CANDIDATE"
            and original.get("guard_latched") is False),
        "runner_rc":rc,
        "first_cleanup_failure":first,
        "native_nav2_lifecycle_ack":nav_ack,
        "native_cm_clean_exit":cm_exit,
        "launch_graceful_exit_marker": "P2_L2_GRACEFUL_TEARDOWN" in teardown,
        "full_run_pass":clean,
        "owner_l3_accepted":False,
        "certified_estop":False,
        "no_raw_private_output":True,
    }

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--runner-log",type=Path,required=True)
    p.add_argument("--runner-rc",type=Path,required=True)
    args=p.parse_args()
    outcome=review_cleanup(args.root,args.runner_log,args.runner_rc)
    print("D06_G07_SHUTDOWN_FIRST_FAILURE "+
          json.dumps(outcome,sort_keys=True),flush=True)
    return 0 if outcome["full_run_pass"] else 3

if __name__=="__main__":
    raise SystemExit(main())
