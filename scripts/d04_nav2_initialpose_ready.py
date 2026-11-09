#!/usr/bin/env python3
"""D04 SIMULATION ONLY: initialize official AMCL at exact TB3 Gazebo spawn pose.

Nav2 Jazzy needs /initialpose before map->odom TF exists and planner_server can
finish activation. It is NOT a navigation Goal or motor command. Run only in
the isolated D04 Gazebo workspace; never infer a certified safety stop.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

# Exact defaults of official nav2_bringup/tb3_simulation_launch.py (jazzy).
SPAWN_X = -2.00
SPAWN_Y = -0.50
LOC_ACTIVE = "/lifecycle_manager_localization/is_active"
NAV_ACTIVE = "/lifecycle_manager_navigation/is_active"


def initialize_map_localization(out: Path, timeout_s: int = 50) -> dict:
    import rclpy
    from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
    from rclpy.parameter import Parameter
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from std_srvs.srv import Trigger

    out.parent.mkdir(parents=True,exist_ok=True)
    evidence={
        "gate":"G-D04-NAV2-INITIALPOSE-READY",
        "passed":False,
        "spawn_pose":{"x":SPAWN_X,"y":SPAWN_Y,"yaw":0.0},
        "source":"official Jazzy tb3_simulation_launch.py default spawn",
        "localization_active":False,
        "navigation_active":False,
        "initialpose_published":0,
        "goal_sent":False,
        "fault_injected":False,
        "cmd_vel_published":False,
        "certified_estop":False,
    }
    rclpy.init()
    node=rclpy.create_node(
        "axia_d04_initialpose_ci_only",
        parameter_overrides=[Parameter("use_sim_time",Parameter.Type.BOOL,True)])
    pub=node.create_publisher(
        PoseWithCovarianceStamped,"/initialpose",
        QoSProfile(depth=5,reliability=ReliabilityPolicy.RELIABLE,
                   durability=DurabilityPolicy.VOLATILE))
    loc=node.create_client(Trigger,LOC_ACTIVE)
    nav=node.create_client(Trigger,NAV_ACTIVE)

    def check_active(client):
        if not client.service_is_ready():
            return False
        future=client.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(node,future,timeout_sec=1.2)
        return bool(future.done() and future.exception() is None
                    and future.result() is not None and future.result().success)

    try:
        last_send=0.0
        deadline=time.monotonic()+timeout_s
        while time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=0.1)
            if not evidence["localization_active"]:
                evidence["localization_active"]=check_active(loc)
            if evidence["localization_active"] and time.monotonic()-last_send>1.25:
                msg=PoseWithCovarianceStamped()
                msg.header.frame_id="map"
                msg.header.stamp=node.get_clock().now().to_msg()
                msg.pose.pose.position.x=SPAWN_X
                msg.pose.pose.position.y=SPAWN_Y
                msg.pose.pose.orientation.w=1.0
                msg.pose.covariance[0]=0.25
                msg.pose.covariance[7]=0.25
                msg.pose.covariance[35]=0.0685
                pub.publish(msg)
                evidence["initialpose_published"]+=1
                last_send=time.monotonic()
            if evidence["localization_active"] and check_active(nav):
                evidence["navigation_active"]=True
                evidence["passed"]=evidence["initialpose_published"]>0
                break
        if not evidence["passed"]:
            evidence["blocker"]="NAV2_NAVIGATION_NEVER_ACTIVE_AFTER_INITIALPOSE"
    finally:
        node.destroy_node()
        rclpy.shutdown()
        out.write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    return evidence


def request_initialpose_ready(env:dict,out:Path,timeout_s:int=65) -> dict:
    target=out/"nav2_initialpose_ready.json"
    log=out/"nav2_initialpose_ready.log"
    cmd=[sys.executable,str(Path(__file__).resolve()),"--out",str(target)]
    try:
        cp=subprocess.run(cmd,env=env,text=True,capture_output=True,
                          timeout=timeout_s,check=False)
        log.write_text(cp.stdout+"\n"+cp.stderr)
        result=json.loads(target.read_text()) if target.exists() else {}
        result["client_exit_code"]=cp.returncode
        result["passed"]=bool(result.get("passed") and cp.returncode==0)
        return result
    except (OSError,ValueError,subprocess.TimeoutExpired) as e:
        log.write_text("ERROR:"+type(e).__name__+"\n")
        return {"passed":False,"blocker":type(e).__name__}


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    try:
        result=initialize_map_localization(args.out)
    except Exception as exc:
        result={"passed":False,"blocker":type(exc).__name__+":"+str(exc)[:220]}
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result["passed"] else 2


if __name__=="__main__":
    raise SystemExit(main())
