#!/usr/bin/env python3
"""Public CI-only test of REAL native G07 physical no-Goal readiness.
Requires native Gazebo set_pose ACK and >=2 fresh physical LaserScan messages.
Never manufactures a scan, goal, cmd_vel, Guard verdict or Owner permission.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def ready(d):
    return (isinstance(d,dict)
            and d.get("status")=="P2_G07_OWNER_PREGOAL_L2_READY_NO_GOAL"
            and d.get("native_set_pose_ack") is True
            and type(d.get("post_ack_distinct_ros_scan_count")) is int
            and d["post_ack_distinct_ros_scan_count"]>=2
            and type(d.get("front_m")) in (float,int)
            and d["front_m"]>0.75
            and type(d.get("side_m")) in (float,int)
            and 0.55<=d["side_m"]<=0.95)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        if a.receipt.is_symlink():raise ValueError("SYMLINK")
        data=json.loads(a.receipt.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError):
        data=None
    if ready(data):
        print("D06_NATIVE_PHYSICAL_PREG0AL_READY_BEFORE_GUI_NO_GOAL")
        return 0
    print("D06_NATIVE_PHYSICAL_PREG0AL_NOT_YET_READY_NO_GOAL")
    return 3

if __name__=="__main__":
    raise SystemExit(main())
