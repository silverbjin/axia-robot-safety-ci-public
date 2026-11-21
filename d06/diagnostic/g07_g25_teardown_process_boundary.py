#!/usr/bin/env python3
"""G07 26s native launch survivor process role diagnostic; no raw args release.

The existing student smoke already writes teardown_processes.txt on forced
termination. This script ONLY extracts safe process-role counts. No timeout,
SIGINT, Goal, DDS, CM/Guard/Scan logic or native process changes.
"""
import argparse
import json
import re
from pathlib import Path

MAX_INPUT_BYTES=131072

def _role(command):
    c=command.lower()
    if ("ros2 launch" in c or "ros2/cli.py launch" in c
            or "bin/ros2 launch" in c):
        return "ros2_launch"
    if re.search(r"(?:^|[ /])gz\s+sim\s+(?:-s|--server)",c):
        return "gazebo_server"
    if "gz sim" in c:
        return "gazebo_process"
    if "collision_monitor" in c:
        return "collision_monitor"
    if "p2_base_guard_node" in c:
        return "guard"
    if "p2_supervisor_node" in c:
        return "supervisor"
    if "rviz2" in c:
        return "rviz_gui"
    if "robot_state_publisher" in c:
        return "robot_state_publisher"
    if "component_container" in c:
        return "component_container"
    if "nav2_" in c or "navigation" in c or "localization" in c:
        return "navigation_stack"
    if "python3" in c or "python " in c:
        return "python_other"
    return "other_redacted"

def assess(ps_text,teardown_text,ordered_and_run_log):
    out=dict(schema="axia.g07.g25.first_managed_teardown_process.v1",
      status="EXIT_SEQUENCE_NOT_PROVEN_HOLD",
      first_failure="NOT_PROVEN",
      release="HOLD",root_cause="UNDETERMINED",root_cause_proven=False,
      clean_child_exit_proven=False,owner_l3_accepted=False,
      certified_estop=False,safety_ttl_changed=False,
      active_non_zombie_count=0,roles={})
    log=ordered_and_run_log if isinstance(ordered_and_run_log,str) else ""
    if len(log)>131072: log=""
    slow=log.find("CI_MOVING_GOAL_TIMEOUT_SLOW")
    nonexit=log.find("G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET")
    if slow>=0 and (nonexit<0 or slow<nonexit):
        out["status"]="FIRST_SLOW_TIMEOUT_BEFORE_TEARDOWN_HOLD"
        out["first_failure"]="CI_MOVING_GOAL_TIMEOUT_SLOW"
        return out
    if nonexit<0:
        out["status"]="NO_26S_EXIT_BOUNDARY_OBSERVED_HOLD"
        return out
    out["first_failure"]="G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET"
    if (not isinstance(ps_text,str) or not ps_text.strip()
            or len(ps_text.encode("utf-8"))>MAX_INPUT_BYTES):
        out["status"]="TEARDOWN_PROCESS_ROLES_NOT_CAPTURED_HOLD"
        return out
    for line in ps_text.splitlines()[:1024]:
        fields=line.split(None,3)
        if (len(fields)!=4 or not fields[0].isdigit() or
                not fields[1].isdigit() or not re.fullmatch(r"[A-Za-z+<]+",fields[2])):
            continue
        # Ignore zombie PID: the student launch_active() also ignores Z/X.
        if fields[2][:1] in ("Z","X"):
            continue
        role=_role(fields[3])
        out["active_non_zombie_count"]+=1
        out["roles"][role]=out["roles"].get(role,0)+1
    if (out["active_non_zombie_count"]>0 and
            log.find("G07_MOVING_GOAL_ORDERED_SHUTDOWN_ACK_BEFORE_SIGINT")>=0 and
            isinstance(teardown_text,str) and
            "P2_L2_FORCED_TEARDOWN" in teardown_text):
        out["status"]="POST_ACK_LAUNCH_GROUP_ALIVE_HOLD"
    else:
        out["status"]="FIRST_LAUNCH_EXIT_PROCESS_CUSTODY_INCOMPLETE_HOLD"
    return out

def _read(path):
    if not path or not path.is_file() or path.is_symlink():
        return None
    if path.stat().st_size>MAX_INPUT_BYTES:
        return None
    return path.read_text(errors="replace")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--processes",type=Path,required=True)
    p.add_argument("--teardown",type=Path,required=True)
    p.add_argument("--stdout",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    out=assess(_read(args.processes),_read(args.teardown),_read(args.stdout))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("AXIA_G07_G25_FIRST_PROCESS_ROLES "+json.dumps(out,sort_keys=True),flush=True)
    return 0 # diagnostic status HOLD never a runtime acceptance

if __name__=="__main__":
    raise SystemExit(main())
