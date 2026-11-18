#!/usr/bin/env python3
"""D06 sealed real Gazebo L2: FIRST official Nav2 lifecycle transition log.

Strictly read-only; prints ONLY allowed official node names, native ACK status
and phase flags. No private launch lines, raw rosbag or solution paths published.
A LAST REQUESTED node is NOT a proven blocked node without explicit error.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

NODES = frozenset((
    "controller_server", "planner_server", "smoother_server",
    "behavior_server", "bt_navigator", "waypoint_follower",
    "velocity_smoother", "collision_monitor", "map_server",
    "amcl", "route_server", "docking_server",
))
ACTIONS=("Deactivating","Cleaning up","Shutting down")
TRANSITION=re.compile(
    r"\b(Deactivating|Cleaning up|Shutting down)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
EXPLICIT_ERROR=re.compile(
    r"Failed to change state for node:\s*([A-Za-z_][A-Za-z0-9_]*)")
NATIVE_FAILURE=re.compile(
    r"^BLOCKED_LIFECYCLE_(NAVIGATION|LOCALIZATION)_(SERVICE_TIMEOUT|REJECTED|SERVICE_MISSING)$")

def inspect_native_shutdown(log: str, native: dict):
    outcome = {
        "schema":"axia.d06.g07_native_shutdown_first_transition_v1",
        "status":"HOLD_NATIVE_SHUTDOWN_FIRST_BOUNDARY_UNVERIFIED",
        "failed_manager":None,
        "native_failure":"UNVERIFIED",
        "manager_shutdown_begin_seen":False,
        "manager_completion_message_seen":False,
        "last_requested_action":None,
        "last_requested_node":None,
        "explicit_failed_node":None,
        "blocked_node_proven":False,
        "transition_lines_seen":0,
        "safety_pass":False,
        "owner_l3_accepted":False,
        "certified_estop":False,
    }
    if not isinstance(log,str) or not isinstance(native,dict):
        return outcome
    status=native.get("status")
    matched=NATIVE_FAILURE.fullmatch(status) if isinstance(status,str) else None
    if not matched:
        return outcome
    manager=matched.group(1).lower()
    outcome["failed_manager"]=manager
    outcome["native_failure"]=matched.group(2)
    tag=re.compile(r"\[\s*lifecycle_manager_"+manager+r"\s*\]")
    for line in log.splitlines():
        if not tag.search(line):
            continue
        if "Shutting down managed nodes" in line:
            # If logs contain multiple sessions, keep the latest observed stage.
            outcome.update(manager_shutdown_begin_seen=True,
                           manager_completion_message_seen=False,
                           last_requested_action=None,last_requested_node=None,
                           explicit_failed_node=None,blocked_node_proven=False,
                           transition_lines_seen=0)
        if "Managed nodes have been shut down" in line:
            outcome["manager_completion_message_seen"]=True
        error=EXPLICIT_ERROR.search(line)
        if error and error.group(1) in NODES:
            outcome["explicit_failed_node"]=error.group(1)
            outcome["blocked_node_proven"]=True
        found=TRANSITION.search(line)
        if found and found.group(1) in ACTIONS and found.group(2) in NODES:
            outcome["last_requested_action"]=found.group(1)
            outcome["last_requested_node"]=found.group(2)
            outcome["transition_lines_seen"]+=1
    if outcome["manager_completion_message_seen"]:
        outcome["status"]="HOLD_NATIVE_ACK_UNVERIFIED_AFTER_MANAGER_COMPLETION_LOG"
    else:
        outcome["status"]="HOLD_NAV2_NATIVE_MANAGER_TRANSITION_UNVERIFIED"
    return outcome


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--launch-log",type=Path,required=True)
    p.add_argument("--native-json",type=Path,required=True)
    args=p.parse_args()
    try:
        if args.launch_log.is_symlink() or args.native_json.is_symlink():
            raise ValueError("SYMLINK_SOURCE")
        log=args.launch_log.read_text(encoding="utf-8",errors="replace")
        original=json.loads(args.native_json.read_text(encoding="utf-8"))
    except (ValueError,OSError,UnicodeError):
        log,original="",{}
    result=inspect_native_shutdown(log,original)
    print("D06_G07_NATIVE_NAV2_SHUTDOWN_FIRST_TRANSITION "+
          json.dumps(result,sort_keys=True),flush=True)
    # Read-only diagnostic never overrides original safety/cleanup failure.
    return 0


if __name__=="__main__":
    raise SystemExit(main())
