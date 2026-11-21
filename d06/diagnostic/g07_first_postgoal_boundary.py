#!/usr/bin/env python3
"""Fail-closed first post-Goal/termination boundary classifier.

Numeric fixtures grounded in strict actual native CI #44865087050 and
#44865216748. This file is L0 regression only and cannot turn L2 HOLD to PASS.
The order below is per-process log line order, not cross-clock timestamps.
"""
import json
import math
import re


def classify(events):
    out={
        "schema":"axia.g07.native_first_postgoal_boundary.v1",
        "release":"HOLD","root_cause":"UNDETERMINED",
        "root_cause_proven":False,"motion_acceptance_proven":False,
        "navigation_ack_before_failure":False,
        "certified_estop":False,"owner_l3_accepted":False,
        "safety_ttl_changed":False,
        "first_safety_state_transition":"NOT_PROVEN_FROM_LOG",
        "first_postgoal_failure":"NONE_RECORDED_NOT_ACCEPTED_HOLD",
        "exit_budget_s":None,"slow_zone_max_supervised_vx":None,
        "slow_zone_samples":None
    }
    if not isinstance(events,(list,tuple)) or len(events)>512 or not all(
            isinstance(v,str) and len(v)<5000 for v in events):
        return out
    def idx(pattern):
        return next((i for i,v in enumerate(events) if pattern in v),None)
    slow=idx("CI_MOVING_GOAL_TIMEOUT_SLOW")
    launch=idx("G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET")
    failures=[(i,k) for i,k in [(slow,"SLOW_POSITIVE_COMMAND_NOT_OBSERVED_HOLD"),
                                (launch,"POST_NAV_ACK_LAUNCH_PID_ALIVE_HOLD")]
              if i is not None]
    if not failures:
        return out
    first,k=min(failures)
    out["first_postgoal_failure"]=k
    goal=idx("ONE_SUPERVISOR_GOAL_SENT")
    if goal is None:
        goal=idx("G07_CI_SIM_GOAL_SENT")
    clear=idx("MOVING_CLEAR_REAL_GAZEBO_LIDAR_CM_PASS")
    if k=="SLOW_POSITIVE_COMMAND_NOT_OBSERVED_HOLD":
        diag=idx("AXIA_G07_CI_MOVING_SLOW_TIMEOUT_DIAGNOSTICS")
        if goal is None or clear is None or diag is None or not (goal<clear<diag<=first):
            out["first_postgoal_failure"]="SLOW_FIRST_ORDER_UNVERIFIED_HOLD"
            return out
        row=events[diag]
        m=re.search(r"max_supervised_in_slow_zone=(-?[0-9]+\.[0-9]+)",row)
        n=re.search(r"observations=([0-9]+)",row)
        if m and n:
            v=float(m.group(1)); nn=int(n.group(1))
            if math.isfinite(v) and -3<=v<=3 and 0<nn<=4096:
                out["slow_zone_max_supervised_vx"]=v
                out["slow_zone_samples"]=nn
        return out

    stop=idx("MOVING_STOP_REAL_GAZEBO_LIDAR_CM_PASS")
    ack=idx("G07_NAV2_ORDERED_SHUTDOWN_ACK_LOCALIZATION_AND_NAVIGATION")
    budget=idx("G07_CI_MANAGED_LAUNCH_EXIT_26S")
    if stop is not None and ack is not None and budget is not None and (
            stop<ack<budget<first):
        out["navigation_ack_before_failure"]=True
        out["exit_budget_s"]=26
    else:
        out["first_postgoal_failure"]="LAUNCH_FIRST_ORDER_UNVERIFIED_HOLD"
    return out


def main():
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser()
    p.add_argument("--events",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if not a.events.is_file() or a.events.is_symlink() or a.events.stat().st_size>30000:
        raise SystemExit("G07_FIRST_POSTGOAL_INPUT_MISSING_OR_OVERSIZE_HOLD")
    lines=a.events.read_text().splitlines()
    out=classify(lines)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("AXIA_G07_FIRST_POSTGOAL_HOLD "+json.dumps(out,sort_keys=True))
    return 0  # Diagnostic status is always HOLD; CI safety gate is separate.


if __name__=="__main__":
    raise SystemExit(main())
