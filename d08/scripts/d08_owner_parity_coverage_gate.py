#!/usr/bin/env python3
"""Fail-closed CI coverage gate: real YOLO+D05+official Nav2 must run.

A green Nav2-only eight-cycle does NOT prove WSL2 Owner --live-person-range.
No WSLg/NVIDIA hardware, CM/Guard 120/150ms or moving-Goal success claimed.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

REQUIRED=("l0-human-proxy-red-green",
          "real-gazebo-rgb-pinned-upstream-yolo-ros")


def check_required_coverage(results):
    results=results if isinstance(results,dict) else {}
    statuses={job:results.get(job,"missing") for job in REQUIRED}
    missing={job:status for job,status in statuses.items() if status!="success"}
    passed=not missing
    return {
        "status":("D08_PUBLIC_OWNER_PARITY_COVERAGE_L2_PASS_NOT_WSL2"
                  if passed else "RELEASE_HOLD_COVERAGE_INCOMPLETE"),
        "ready_for_wsl2":passed,
        "l3_tested":False,
        "no_goal_only":True,
        "verified_scope":("PUBLIC_XVFB_JAZZY_GAZEBO_NAV2_REAL_YOLO_RGBD_D05"
                          if passed else "INCOMPLETE"),
        "required_jobs":statuses,
        "missing_or_nonpassing":missing,
        "cm_internal_120ms_verified":False,
        "guard_150ms_verified":False,
        "moving_goal_e2e_verified":False,
        "certified_estop":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--l0",required=True)
    p.add_argument("--live-yolo-d05",required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("D08_COVERAGE_OUTPUT_ALREADY_EXISTS")
    result=check_required_coverage({
        REQUIRED[0]:args.l0, REQUIRED[1]:args.live_yolo_d05})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(result["status"]+" "+json.dumps({
        "required_jobs":result["required_jobs"],
        "ready_for_wsl2":result["ready_for_wsl2"]},sort_keys=True),flush=True)
    return 0 if result["ready_for_wsl2"] else 2


if __name__=="__main__":
    raise SystemExit(main())
