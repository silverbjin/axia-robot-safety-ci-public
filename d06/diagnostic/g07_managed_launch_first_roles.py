#!/usr/bin/env python3
"""G25 native 26s managed launch first survivors: redacted numerical custody.

Read-only. Never prints raw ps argv, private path, PID, Goal UUID or bag.
One active session's existing Student teardown_processes.txt is the source.
No new node/ROS process, process management action or shutdown budget change.
"""
import argparse
import json
import re
from pathlib import Path

_ROLES=(
    ("safety_supervisor",("p2_supervisor_node",)),
    ("base_guard",("p2_base_guard_node",)),
    ("collision_monitor",("collision_monitor",)),
    ("ros_gz_bridge",("parameter_bridge","ros_gz_bridge")),
    ("gazebo",("gz sim","gz-sim","gzserver")),
    ("rviz2",("rviz2",)),
    ("tf_publisher",("robot_state_publisher",)),
    ("nav2_node",("amcl","controller_server","planner_server",
                  "bt_navigator","lifecycle_manager")),
    ("ros2_launch",("ros2 launch","launch_service","launch_ros")),
)


def _hold(status,**kwargs):
    return {"schema":"axia.g07.managed_launch_first_retained_roles.v1",
            "status":status,"release":"HOLD",
            "root_cause_proven":False,"clean_exit_proven":False,
            "timing_safety_pass":False,"certified_estop":False,
            "owner_wsl2_l3_accepted":False,
            "managed_exit_grace_sec":26,
            **kwargs}


def classify(text,*,managed_timeout=False):
    if managed_timeout is not True:
        return _hold("NO_MANAGED_EXIT_TIMEOUT_OBSERVED_HOLD",
                     retained_process_count=0,roles={})
    if (not isinstance(text,str) or len(text.encode("utf-8"))>65536
            or not text or len(text.splitlines())>130):
        return _hold("MANAGED_EXIT_ROLE_SNAPSHOT_MISSING_HOLD",
                     retained_process_count=None,roles={})
    counts={}
    states={}
    parsed=0
    for line in text.splitlines():
        columns=line.strip().split(maxsplit=3)
        if len(columns)!=4 or not (columns[0].isdigit() and columns[1].isdigit()):
            continue
        stat=columns[2]
        if not re.fullmatch(r"[A-Za-z+<NLsl]{1,12}",stat):
            continue
        cmd=columns[3].lower()
        role=next((name for name,patterns in _ROLES
                   if any(v in cmd for v in patterns)),"other")
        counts[role]=counts.get(role,0)+1
        states[stat[0]]=states.get(stat[0],0)+1
        parsed+=1
    if parsed==0:
        return _hold("MANAGED_EXIT_ROLE_SNAPSHOT_MISSING_HOLD",
                     retained_process_count=None,roles={})
    return _hold("MANAGED_LAUNCH_26S_RETAINED_PROCESSES_HOLD",
                 retained_process_count=parsed,
                 roles=dict(sorted(counts.items())),
                 process_state_counts=dict(sorted(states.items())),
                 original_ps_argv_discarded=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--managed-timeout",action="store_true")
    a=p.parse_args()
    if (a.input.is_file() and not a.input.is_symlink()
            and a.input.stat().st_size<=65536):
        text=a.input.read_text(errors="replace")
    else:
        text=None
    result=classify(text,managed_timeout=a.managed_timeout)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("AXIA_G07_G25_MANAGED_LAUNCH_FIRST_ROLES "+
          json.dumps(result,sort_keys=True),flush=True)
    return 0  # Diagnostic may not ever override strict native L2 failure.


if __name__=="__main__":
    raise SystemExit(main())
