#!/usr/bin/env python3
"""Exact SHA private official Nav2 + Gazebo 3x PRELOCAL runner; NO Goal/Fault.

Uses the existing protected private CI bridge. Prints allowlisted status only.
Real Goal, Start, cancellation, local WSL2 acceptance and E-Stop are NOT proved.
"""
import argparse
import json
from pathlib import Path
import private_ci_bridge as bridge

PIN = "b7eed78b9855ab1bd8eb96285abbe30c4379af72"
_BASE = "d86ee9860de8924f6a5b2c5828d493fb7ef7f9eb"


def run(root):
    result = {"scope":"EXACT_SHA_OFFICIAL_GAZEBO_3X_PRELOCAL_NO_GOAL",
              "private_sha_verified":False, "goal_sent":False,
              "fault_injected":False,"start_called":False,
              "gate_accepted":False,"certified_estop_verified":False,
              "status":"BLOCKED"}
    if bridge.PIN != _BASE:
        print("AXIA_PR52_GAZEBO3 "+json.dumps(result,sort_keys=True),flush=True)
        return 3
    bridge.PIN=PIN
    try:
        bridge.run_gate(Path(root),"gazebo3-prepause")
        result["status"]="GAZEBO3_READONLY_PASS"
        result["private_sha_verified"]=True
    except bridge.GateBlocked:
        result["reason"]="PRIVATE_GAZEBO3_GATE_BLOCKED"
    except Exception:
        result["reason"]="PRIVATE_RUNNER_ERROR"
    print("AXIA_PR52_GAZEBO3 "+json.dumps(result,sort_keys=True),flush=True)
    return 0 if result["status"]=="GAZEBO3_READONLY_PASS" else 3


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--private-root",required=True,type=Path)
    args=parser.parse_args()
    raise SystemExit(run(args.private_root))
