#!/usr/bin/env python3
"""D06 actual ROS L1 smoke for read-only RViz observer. NO Gazebo or Goal."""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    out=a.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    os.environ["ROS_DOMAIN_ID"]=str(80+os.getpid()%120)
    os.environ["ROS_AUTOMATIC_DISCOVERY_RANGE"]="LOCALHOST"
    monitor=Path(__file__).resolve().with_name("d06_readonly_monitor.py")
    proc=subprocess.Popen([sys.executable,"-u",str(monitor),"--out",str(out/"observer")],
        env=os.environ.copy(),start_new_session=True,
        stdout=(out/"monitor.log").open("w"),stderr=subprocess.STDOUT)
    result={"gate":"D06_READONLY_OBSERVER_REAL_ROS_L1","status":"BLOCKED",
      "ros_actual":False,"gazebo_actual":False,"goal_sent":False,
      "cmd_vel_published":False,"certified_estop":False,"stages":[]}
    node=None
    try:
        import rclpy
        from rclpy.qos import qos_profile_sensor_data
        from sensor_msgs.msg import LaserScan
        from nav_msgs.msg import Odometry
        from visualization_msgs.msg import MarkerArray
        rclpy.init()
        node=rclpy.create_node("d06_ros_l1_visual_observer_test")
        pub_scan=node.create_publisher(LaserScan,"/scan",qos_profile_sensor_data)
        pub_odom=node.create_publisher(Odometry,"/odom",qos_profile_sensor_data)
        markers=[]
        node.create_subscription(MarkerArray,"/axia/d06/rviz/bubble",
                                 lambda m: markers.append(m),10)
        def pump(seconds,dist=None):
            end=time.monotonic()+seconds
            while time.monotonic()<end:
                scan=LaserScan()
                stamp=node.get_clock().now().to_msg()
                scan.header.stamp=stamp
                scan.header.frame_id="base_footprint"
                scan.angle_min=-math.pi/2
                scan.angle_increment=math.pi/360
                scan.angle_max=scan.angle_min+359*scan.angle_increment
                scan.range_min=.05;scan.range_max=8.
                scan.ranges=[float("inf")]*360
                if dist is not None:
                    for i in range(360):
                        if abs(scan.angle_min+i*scan.angle_increment)<.09:
                            scan.ranges[i]=float(dist)
                    pub_scan.publish(scan)
                odo=Odometry()
                odo.header.stamp=stamp
                odo.header.frame_id="odom"
                odo.child_frame_id="base_footprint"
                pub_odom.publish(odo)
                rclpy.spin_once(node,timeout_sec=.05)
                time.sleep(.05) # approx 10 Hz, no CPU saturation
        # Give discovery a moment before publishing stages.
        pump(1.5,dist=None)
        for name,distance,expected in (
                ("clear",1.2,"CLEAR"),("slow",.65,"SLOWDOWN"),
                ("stop",.3,"STOP")):
            pump(2.5,distance)
            path=out/"observer"/"readonly_samples.jsonl"
            rows=[]
            if path.exists():
                for raw in path.read_text().splitlines():
                    if raw.strip(): rows.append(json.loads(raw))
            matched=[r for r in rows if r["annotated_zone_NOT_CM_VERDICT"]==expected
                     and r["front_m"] is not None and abs(r["front_m"]-distance)<.02]
            if not matched:raise AssertionError(f"{name}: real ROS scan observer failed ({len(rows)} entries)")
            result["stages"].append({"name":name,"observed":len(matched),
                                      "front_m":matched[-1]["front_m"],
                                      "status":"PASS"})
            print(f"D06_REAL_ROS_L1_ANNOTATION_STAGE {name} front_m={distance} observed={len(matched)}",flush=True)
        if len(markers)<3:raise AssertionError(f"MarkerArray missing, count={len(markers)}")
        if not all(len(x.markers)>=2 for x in markers[-3:]):
            raise AssertionError("RViz bubbles not published")
        n_pub=node.count_publishers("/cmd_vel")
        if n_pub!=0:raise AssertionError(f"FORBIDDEN cmd_vel publisher count={n_pub}")
        result["marker_arrays_received"]=len(markers)
        result["cmd_vel_publisher_count"]=n_pub
        result["status"]="PASS_READONLY_REAL_ROS_L1"
        result["ros_actual"]=True
        print("D06_READONLY_REAL_ROS_L1_PASS NONSAFETY_MARKER_ONLY NO_GOAL NO_CMD_VEL",flush=True)
    except Exception as exc:
        result["blocker"]=f"{type(exc).__name__}:{exc}"
        print("D06_READONLY_REAL_ROS_L1_BLOCKED "+result["blocker"],flush=True)
    finally:
        if node is not None:
            node.destroy_node()
            import rclpy
            if rclpy.ok():rclpy.shutdown()
        if proc.poll() is None:
            os.killpg(proc.pid,signal.SIGINT)
        try:proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=4)
        result["monitor_rc"]=proc.returncode
        (out/"verdict.json").write_text(json.dumps(result,indent=2)+"\n")
        print("D06_READONLY_ROS_L1_VERDICT "+json.dumps(result,sort_keys=True),flush=True)
    return 0 if result["status"]=="PASS_READONLY_REAL_ROS_L1" and result["monitor_rc"]==0 else 2

if __name__=="__main__":
    raise SystemExit(main())
