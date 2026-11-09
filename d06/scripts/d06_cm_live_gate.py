#!/usr/bin/env python3
"""D06 official Jazzy Nav2 Collision Monitor L1 test, isolated ROS test topics.

Publishes synthetic LaserScan and Twist to TEST INPUT topics only, never to
the robot's /cmd_vel or /safety/scan. No Gazebo, motors, Goal or stop claim.
PASS requires actual official nav2_collision_monitor output and state.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


def _zone_scan(stamp, distance):
    from sensor_msgs.msg import LaserScan
    scan=LaserScan()
    scan.header.frame_id="base_footprint"
    scan.header.stamp=stamp
    scan.angle_min=-math.pi/2
    scan.angle_increment=math.pi/360
    scan.angle_max=scan.angle_min + scan.angle_increment*359
    scan.time_increment=0.0
    scan.scan_time=0.066
    scan.range_min=0.05
    scan.range_max=8.0
    scan.ranges=[float("inf")]*360
    for i in range(360):
        angle=scan.angle_min+i*scan.angle_increment
        if abs(angle)<0.09:
            scan.ranges[i]=float(distance)
    return scan


def _run_stage(node, pubs, seen, *, name, distance, expected, seconds=3.0):
    from geometry_msgs.msg import Twist
    start=time.monotonic()
    observed=[]
    state_events=[]
    seen["out"].clear()
    seen["state"].clear()
    while time.monotonic()-start<seconds:
        stamp=node.get_clock().now().to_msg()
        pubs["scan"].publish(_zone_scan(stamp,distance))
        cmd=Twist();cmd.linear.x=0.20
        pubs["cmd"].publish(cmd)
        import rclpy
        rclpy.spin_once(node,timeout_sec=0.07)
        if time.monotonic()-start>0.75:
            observed.extend(seen["out"])
            state_events.extend(seen["state"])
        seen["out"].clear()
        seen["state"].clear()
    # Only evaluate recent output after monitor has received at least one scan.
    recent=observed[-18:]
    recent_actions=state_events[-18:]
    if not recent or not recent_actions:
        raise AssertionError(f"{name}: no actual output/state from official Collision Monitor")
    output_samples=[x[0] for x in recent]
    yaw_samples=[x[1] for x in recent]
    expected_actions={"CLEAR":0,"SLOWDOWN":2,"STOP":1}
    action=expected_actions[expected]
    matched_states=[x for x in recent_actions if x[0]==action]
    if not matched_states:
        raise AssertionError(f"{name}: official CM action {action} absent, seen={recent_actions[-8:]}")
    if expected=="CLEAR":
        ok=all(abs(x-0.20)<0.012 for x in output_samples[-6:])
    elif expected=="SLOWDOWN":
        ok=all(0.001 < x <= 0.20*0.30+0.010 for x in output_samples[-6:])
    else:
        ok=all(abs(x)<0.01 for x in output_samples[-6:]) and all(
            abs(x)<0.02 for x in yaw_samples[-6:])
    if not ok:
        raise AssertionError(f"{name}: actual output samples violate {expected}: {output_samples[-10:]}")
    return {
        "stage":name,"input_front_distance_m":distance,"input_cmd_linear_mps":0.2,
        "expected_action":expected, "actual_action_codes":sorted({x[0] for x in recent_actions}),
        "actual_polygon_names":sorted({x[1] for x in recent_actions}),
        "output_linear_mps":output_samples[-10:],
        "output_angular_rps":yaw_samples[-10:],
        "out_message_count":len(observed),"state_count":len(state_events),
        "status":"PASS"
    }


def _start_monitor(argv, env, output_dir):
    log=open(output_dir/"collision_monitor.log","w",encoding="utf-8")
    try:
        return subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,
                                start_new_session=True)
    finally:
        log.close()


def _activate(env, proc):
    for action in ("configure","activate"):
        last=""
        for attempt in range(20):
            if proc.poll() is not None:
                raise RuntimeError(f"Collision Monitor exited before {action}: {proc.returncode}")
            try:
                r=subprocess.run(["ros2","lifecycle","set","/collision_monitor",action],
                                 env=env,capture_output=True,text=True,timeout=8)
                last=f"rc={r.returncode} {r.stdout[-400:]} {r.stderr[-400:]}"
                if r.returncode==0 and "success" in r.stdout.lower():
                    break
            except subprocess.TimeoutExpired:
                last="lifecycle command timed out"
            time.sleep(0.55)
        else:
            raise RuntimeError(f"Collision Monitor cannot {action}: {last}")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--params",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    result={
        "gate":"G-D06-OFFICIAL-CM-ROS-L1",
        "status":"BLOCKED","ros_actual":False,"gazebo_actual":False,
        "p1_executed":False,"goal_sent":False,"cmd_vel_published":False,
        "certified_estop":False, "stages":[]
    }
    env=os.environ.copy()
    env["ROS_DOMAIN_ID"]=str(20+(os.getpid()%170))
    env["ROS_AUTOMATIC_DISCOVERY_RANGE"]="LOCALHOST"
    params=args.params.resolve(strict=True)
    result["params_sha256"]=hashlib.sha256(params.read_bytes()).hexdigest()
    node=None;proc=None
    try:
        import rclpy
        from rclpy.qos import qos_profile_sensor_data
        from sensor_msgs.msg import LaserScan
        from geometry_msgs.msg import Twist
        from nav2_msgs.msg import CollisionMonitorState
        rclpy.init(args=None)
        node=rclpy.create_node("axia_d06_official_cm_readonly_verifier")
        # All publications are to isolated test-INPUT topics, NOT final cmd_vel.
        seen={"out":[],"state":[]}
        def output_cb(msg):
            seen["out"].append((float(msg.linear.x),float(msg.angular.z)))
        def state_cb(msg):
            seen["state"].append((int(msg.action_type),str(msg.polygon_name)))
        scan_pub=node.create_publisher(LaserScan,"/axia/d06/test/scan",qos_profile_sensor_data)
        cmd_pub=node.create_publisher(Twist,"/axia/d06/test/cmd_in",10)
        sub_cmd=node.create_subscription(Twist,"/axia/d06/test/cmd_out",output_cb,10)
        sub_state=node.create_subscription(CollisionMonitorState,
            "/axia/d06/test/collision_monitor_state",state_cb,10)
        proc=_start_monitor(
            ["ros2","run","nav2_collision_monitor","collision_monitor",
             "--ros-args","--params-file",str(params)],env,out)
        _activate(env,proc)
        deadline=time.monotonic()+12
        while time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=0.1)
            if (node.count_publishers("/axia/d06/test/cmd_out")==1 and
                node.count_subscribers("/axia/d06/test/cmd_in")==1 and
                node.count_subscribers("/axia/d06/test/scan")==1):
                break
        result["graph"]={
            "final_test_output_publishers":node.count_publishers("/axia/d06/test/cmd_out"),
            "input_test_subscribers":node.count_subscribers("/axia/d06/test/cmd_in"),
            "scan_test_subscribers":node.count_subscribers("/axia/d06/test/scan"),
            "robot_cmd_publishers":node.count_publishers("/cmd_vel")
        }
        if (result["graph"]["final_test_output_publishers"]!=1 or
            result["graph"]["input_test_subscribers"]!=1 or
            result["graph"]["scan_test_subscribers"]!=1 or
            result["graph"]["robot_cmd_publishers"]!=0):
            raise AssertionError("CM test graph unsafe/incomplete: "+str(result["graph"]))
        pubs={"scan":scan_pub,"cmd":cmd_pub}
        for name,dist,expected in (
            ("clear_1p20m",1.20,"CLEAR"),
            ("slow_0p65m",0.65,"SLOWDOWN"),
            ("stop_0p30m",0.30,"STOP")):
            stage=_run_stage(node,pubs,seen,name=name,distance=dist,
                             expected=expected,seconds=3.0)
            result["stages"].append(stage)
            print("D06_ACTUAL_CM_STAGE "+json.dumps({
                "stage":name,"status":stage["status"],
                "linear_mps":stage["output_linear_mps"][-1],
                "action_codes":stage["actual_action_codes"]}),flush=True)
        result["status"]="PASS_OFFICIAL_JAZZY_CM_CLEAR_SLOWDOWN_STOP"
        result["ros_actual"]=True
    except Exception as exc:
        result["blocker"]=f"{type(exc).__name__}:{str(exc)[:600]}"
        print("D06_CM_L1_BLOCKED "+result["blocker"],flush=True)
    finally:
        if node is not None:
            try: node.destroy_node()
            except Exception: pass
            try:
                import rclpy
                if rclpy.ok(): rclpy.shutdown()
            except Exception: pass
        if proc is not None:
            if proc.poll() is None:
                try: os.killpg(proc.pid,signal.SIGINT)
                except ProcessLookupError: pass
                try:proc.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)
            result["monitor_exit_code"]=proc.returncode
        (out/"verdict.json").write_text(json.dumps(result,indent=2,
             ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
        (out/"SHA256SUMS").write_text("".join(
            hashlib.sha256(f.read_bytes()).hexdigest()+"  "+f.name+"\n"
            for f in sorted(out.iterdir()) if f.is_file() and f.name!="SHA256SUMS"))
        print("D06_CM_L1_VERDICT "+json.dumps({
            "status":result["status"],"blocker":result.get("blocker"),
            "ros_actual":result["ros_actual"],"gazebo_actual":False}),flush=True)
    return 0 if result["status"]=="PASS_OFFICIAL_JAZZY_CM_CLEAR_SLOWDOWN_STOP" else 2

if __name__=="__main__":
    raise SystemExit(main())
