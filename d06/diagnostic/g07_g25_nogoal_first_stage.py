#!/usr/bin/env python3
"""First recorded G25 NO_GOAL stage, never infer origin from final rc.

Only whitelisted phase codes; no raw logs, private PIDs or Paths.
This classifier does NOT prove that the process-group timeout's root cause
is a particular node. Earlier statuses are kept as separate first events.
"""
from pathlib import Path
import argparse
import json

EVENTS=(
    ("P2_BUILD_BLOCKED","BUILD_BLOCKED_BEFORE_TEARDOWN_HOLD"),
    ("P2_NO_GOAL_BLOCKED:","STARTUP_BLOCKED_BEFORE_TEARDOWN_HOLD"),
    ("P2_STAGED_NO_GOAL_BLOCKED","STARTUP_BLOCKED_BEFORE_TEARDOWN_HOLD"),
    ("G07_REAL_NAV2_ORDERED_SHUTDOWN_BLOCKED_BEFORE_SIGINT","NAV2_SHUTDOWN_ACK_BLOCKED_HOLD"),
    ("G07_MOVING_GOAL_ORDERED_SHUTDOWN_BLOCKED","NAV2_SHUTDOWN_ACK_BLOCKED_HOLD"),
    ("G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET","EARLY_SHUTDOWN_STAGE_UNVERIFIED_HOLD"),
)
MARKERS=(
    "G07_SHUTDOWN_L2_NO_GOAL REAL_CM_ACTIVE_BEFORE_SHUTDOWN",
    "G07_REAL_NAV2_ORDERED_SHUTDOWN_ACK_BEFORE_SIGINT",
    "G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET",
    "P2_L2_SMOKE_RC=3",
    "P2_L2_SMOKE_RC=0",
    "P2_NO_GOAL_BLOCKED:",
    "G07_REAL_NAV2_ORDERED_SHUTDOWN_BLOCKED_BEFORE_SIGINT",
    "P2_BUILD_BLOCKED",
)

def first_failure(stdout,*,role_status=None):
    result=dict(schema="axia.g07.g25.no_goal_first_stage.v1",
        status="NO_GOAL_SHUTDOWN_INCOMPLETE_HOLD",
        release="HOLD",root_cause="UNDETERMINED",root_cause_proven=False,
        clean_exit_proven=False,moving_goal_two_cycle_pass=False,
        certified_estop=False,owner_l3_accepted=False,
        safety_ttl_changed=False,first_marker=None,
        launch_roles_status=(role_status if type(role_status) is str else "UNVERIFIED"))
    if type(stdout) is not str or len(stdout)>8_000_000:
        result["status"]="NO_GOAL_STDOUT_MISSING_OR_INVALID_HOLD"
        return result
    lines=stdout.splitlines()
    first=None
    for n,line in enumerate(lines):
        for marker,status in EVENTS:
            if marker in line:
                if first is None or n<first[0]:
                    first=(n,marker,status)
    if first is None:
        return result
    _,marker,status=first
    result["first_marker"]=marker
    result["status"]=status
    if marker=="G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET":
        ack="G07_REAL_NAV2_ORDERED_SHUTDOWN_ACK_BEFORE_SIGINT" in stdout
        req="G07_SHUTDOWN_L2_NO_GOAL REAL_CM_ACTIVE_BEFORE_SHUTDOWN" in stdout
        if ack and req:
            result["status"]="POST_ACK_LAUNCH_LIVENESS_TIMEOUT_HOLD"
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stdout",type=Path,required=True)
    p.add_argument("--roles",type=Path)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    try:
        if args.stdout.stat().st_size>8_000_000:raise ValueError("oversize")
        source=args.stdout.read_text(errors="replace")
    except (OSError,ValueError):
        source=None
    role_status=None
    if args.roles and args.roles.is_file() and args.roles.stat().st_size<32768:
        try:
            role_status=json.loads(args.roles.read_text()).get("status")
        except (OSError,ValueError):pass
    answer=first_failure(source,role_status=role_status)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(answer,sort_keys=True,indent=2)+"\n")
    print("AXIA_G07_G25_NO_GOAL_FIRST_STAGE "+json.dumps(answer,sort_keys=True),flush=True)
    return 0
if __name__=="__main__":raise SystemExit(main())
