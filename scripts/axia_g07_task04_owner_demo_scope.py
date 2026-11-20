#!/usr/bin/env python3
"""FV17z53O: preserve formal RMW HOLD without erasing physical demo evidence.

No fake ROS, no altered Guard TTL. A scope candidate is only possible when
the real Owner numeric verifier has proved EVERY original gate other than
a diagnosed RMW wall-time discontinuity, AND independently proven actual
Guard internal CM age <=150ms. NEVER returns Owner L3 acceptance.
"""
import argparse
import json
import re
from pathlib import Path

_REQUIRED=(
    "single_goal_actual_action","exact_goal_cancel","sqlite_14",
    "cm_source_and_observer_120ms","guard_internal_150ms",
    "s02_actual_native_contact_zero","cli_shared_moving_result",
    "no_unexpected_guard_latch","first_timing_violation_none",
    "odom_moved","odom_zero_dwell","cm_callback_120ms","guard_150ms",
    "scan_300ms","odom_300ms","clock_300ms","nav_lifecycle_ack",
    "loc_lifecycle_ack","collision_monitor_child_clean",
    "both_actual_gui_windows","exact_source_sha",
)

def assess_owner_demo_scope(record):
    hold={"schema":"axia.g07.owner.scoped_demo_numerical_v1",
          "status":"HOLD","first_failure_preserved":(
              record.get("first_failure") if isinstance(record,dict) else "INVALID"),
          "formal_safety_timing_accepted":False,
          "owner_wsl2_l3_accepted":False,
          "axia_mvp_demo_accepted":False,
          "certified_estop":False}
    if not isinstance(record,dict):
        return hold
    checks=record.get("checks")
    cm=record.get("cm120")
    if (record.get("status")!="HOLD"
            or record.get("scenario_scope")!="owner"
            or record.get("first_failure")!="cm_source_and_observer_120ms"
            or record.get("certified_estop") is not False
            or record.get("owner_wsl2_l3_accepted") is not False
            or not isinstance(checks,dict) or set(checks)!=set(_REQUIRED)
            or not isinstance(cm,dict)
            or cm.get("status")!="TASK02_RMW_TIMEBASE_DISCONTINUITY_HOLD"
            or checks["cm_source_and_observer_120ms"] is not False
            or any(checks[k] is not True for k in _REQUIRED
                   if k!="cm_source_and_observer_120ms")
            or record.get("gui_windows_seen")!=2
            or not isinstance(record.get("goal_uuid"),str)
            or not re.fullmatch(r"[0-9a-f]{32}",record["goal_uuid"])
            or not isinstance(record.get("source_sha"),str)
            or not re.fullmatch(r"[0-9a-f]{40}",record["source_sha"])
            or type(record.get("odom_moved_m")) not in (int,float)
            or record["odom_moved_m"]<.05
            or type(record.get("stopped_dwell_sec")) not in (int,float)
            or record["stopped_dwell_sec"]<1.0):
        return hold
    return {**hold,
            "status":"MVP_OWNER_PHYSICAL_NUMERICAL_CANDIDATE_FORMAL_TIMEBASE_HOLD",
            "formal_first_hold":"cm_source_and_observer_120ms",
            "formal_cm_timebase_diagnosis":cm["status"],
            "physical_goal_slow_stop_cancel_numerically_supported":True,
            "physical_observer_cm_callback_under_120ms":True,
            "guard_actual_internal_cm_age_under_150ms":True,
            "source_sha":record["source_sha"],
            "goal_uuid":record["goal_uuid"],
            "original_numeric_first_failure_retained":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--numeric",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    try:
        v=assess_owner_demo_scope(json.loads(a.numeric.read_text()))
    except (ValueError,OSError,TypeError):
        v=assess_owner_demo_scope(None)
    a.output.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n")
    print("AXIA_G07_FV17_OWNER_SCOPED_VERDICT "+json.dumps(
        {"status":v["status"],"formal_timing_accepted":False},
        sort_keys=True))
    return 0 if v["status"]=="MVP_OWNER_PHYSICAL_NUMERICAL_CANDIDATE_FORMAL_TIMEBASE_HOLD" else 3

if __name__=="__main__":
    raise SystemExit(main())
