#!/usr/bin/env python3
"""Pure public CI-only G07 adversarial load phase oracle (no ROS or Goal).
Never infer shutdown success from a goal; stop extra CPU contention ONLY
after actual one Goal CLEAR/SLOWDOWN/STOP and odom STOP dwell were proven.
The original native Nav2 lifecycle shutdown and CM clean exit remain mandatory.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def classify_goal_phase(report):
    if not isinstance(report,dict):
        return "CONTINUE_GOAL_STRESS"
    if (report.get("status")=="CI_GAZEBO_MOVING_GOAL_CANDIDATE"
        and report.get("goal_sent") is True
        and report.get("real_gazebo_world") is True
        and report.get("guard_latched") is False
        and type(report.get("odom_stopped_dwell_sec")) in (int,float)
        and 1.0<=report["odom_stopped_dwell_sec"]<100.0
        and report.get("owner_l3_accepted") is False):
        return "STOP_AFTER_VERIFIED_GOAL_ORACLE"
    return "CONTINUE_GOAL_STRESS"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--goal-report",type=Path,required=True)
    a=p.parse_args()
    try:
        if a.goal_report.is_symlink():
            raise ValueError("INVALID_PATH")
        data=json.loads(a.goal_report.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError):
        data=None
    value=classify_goal_phase(data)
    print(value,flush=True)
    return 0 if value=="STOP_AFTER_VERIFIED_GOAL_ORACLE" else 1

if __name__=="__main__":
    raise SystemExit(main())
