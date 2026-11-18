#!/usr/bin/env python3
"""CI-only bounded renderer CPU load, never on owned official CM core.

The G07 owned CPU policy reserves lowest allowed for RViz/Xvfb, second
for official collision_monitor, middle for Scenario Verifier, last bag.
This pure helper chooses the renderer core and a <=30%% duty workload.
No ROS publishers, Goal, Guard, TTL or native Nav2 parameter modifications.
"""
from __future__ import annotations
import argparse
import os
import sys
import time

def choose_renderer_load_cpu(cpus):
    ordered=sorted(set(cpus))
    if len(ordered)<4 or any(type(v) is not int or v<0 for v in ordered):
        raise ValueError("D06_LOAD_TOPOLOGY_FOUR_CORE_MINIMUM")
    return ordered[0]

def renderer_duty_cycle():
    return (0.008,0.024)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cpu",action="store_true",help="print the allowed GUI core")
    p.add_argument("--load",action="store_true",help="run bounded CI renderer-like workload")
    p.add_argument("--seconds",type=float,default=210)
    a=p.parse_args()
    try:
        allowed=os.sched_getaffinity(0)
        if a.cpu:
            print(choose_renderer_load_cpu(allowed),flush=True)
            return 0
        if not a.load or a.seconds<=0 or a.seconds>240:
            raise ValueError("D06_LOAD_UNAUTHORIZED_ARGUMENT")
        if os.environ.get("GITHUB_ACTIONS")!="true" or os.environ.get("AXIA_G07_CI_SIM_GOAL_ALLOWED")!="1":
            raise ValueError("D06_LOAD_CI_ONLY_NO_OWNER")
        if len(os.sched_getaffinity(0))!=1:
            raise ValueError("D06_LOAD_NOT_ON_RENDERER_ONLY_CORE")
        work,pause=renderer_duty_cycle()
        until=time.monotonic()+a.seconds
        x=1.0
        while time.monotonic()<until:
            chunk=time.monotonic()+work
            while time.monotonic()<chunk:
                x=(x*1.00000001+0.1)%99999.0
            time.sleep(pause)
        return 0
    except (ValueError,OSError) as exc:
        print("D06_RENDERER_LOAD_BLOCKED "+type(exc).__name__,file=sys.stderr)
        return 3

if __name__=="__main__":
    raise SystemExit(main())
