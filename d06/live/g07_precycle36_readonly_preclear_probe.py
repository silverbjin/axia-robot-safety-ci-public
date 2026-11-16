#!/usr/bin/env python3
"""NO_GOAL: actual static-world LaserScan/odom preclear evidence only.

Does NOT move a Gazebo entity, start a Nav2 Goal, publish cmd_vel, or weaken
the original private Owner's pregoal physical 0.75m-front/1.20m-side gate.
A prior OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE must be resolved separately
from Gazebo/RViz GUI rendering. Output reports real distances, never a PASS.
"""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
import statistics
import time

def front_side(scan, bearing):
    """Return exact original pre-Goal front and side geometry or None."""
    increment=getattr(scan,"angle_increment",None)
    angle_min=getattr(scan,"angle_min",None)
    lo=getattr(scan,"range_min",None)
    hi=getattr(scan,"range_max",None)
    if not all(type(x) in (int,float) and math.isfinite(x)
               for x in (increment,angle_min,lo,hi,bearing)):
        return None
    if not (0<increment<1 and 0<=lo<hi and -math.pi<=bearing<=math.pi):
        return None
    front=[];side=[]
    for i,val in enumerate(scan.ranges):
        if type(val) not in (int,float) or not math.isfinite(val) or not lo<=val<=hi:
            continue
        rad=angle_min+i*increment
        delta=math.atan2(math.sin(rad-bearing),math.cos(rad-bearing))
        if abs(rad)<=.18:front.append(float(val))
        if abs(delta)<=.12:side.append(float(val))
    return (min(front),min(side)) if front and side else None

def label_preclear(front,side):
    if (type(front) not in (float,int) or type(side) not in (float,int)
        or not math.isfinite(front) or not math.isfinite(side)):
        return "MISSING_REAL_SCAN"
    if front<=.75 or side<=1.2:
        return "OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE"
    return "OWNER_PREGOAL_STATIC_CLEAR_CANDIDATE_NO_GOAL"

def run(output,seconds):
    if not (os.environ.get("AXIA_P0_SIM_ONLY")=="1"
            and os.environ.get("ROS_DISTRO")=="jazzy"
            and os.environ.get("GZ_PARTITION","").startswith("axia_p2_")):
        raise ValueError("NO_GOAL_SIM_SCOPE_MISSING")
    from sensor_msgs.msg import LaserScan
    from nav_msgs.msg import Odometry
    from rclpy.qos import qos_profile_sensor_data
    import rclpy
    bearing=math.atan2(.75,.19)  # Original verified 2026-11-15 frozen source.
    rclpy.init()
    node=rclpy.create_node("axia_g07_rollback_preclear_readonly")
    rows=[];odom=[]
    def on_scan(msg):
        pair=front_side(msg,bearing)
        if pair:
            rows.append({"mono":round(time.monotonic(),6),
                         "ros_stamp_sec":msg.header.stamp.sec+
                                          msg.header.stamp.nanosec*1e-9,
                         "front_m":round(pair[0],6),"side_m":round(pair[1],6)})
    def on_odom(msg):
        odom.append([round(time.monotonic(),6),
                     round(msg.twist.twist.linear.x,6),
                     round(msg.twist.twist.angular.z,6)])
    node.create_subscription(LaserScan,"/safety/scan",on_scan,qos_profile_sensor_data)
    node.create_subscription(Odometry,"/odom",on_odom,qos_profile_sensor_data)
    try:
        until=time.monotonic()+seconds
        while time.monotonic()<until:
            rclpy.spin_once(node,timeout_sec=.15)
    finally:
        node.destroy_node();rclpy.shutdown()
    fronts=[x["front_m"] for x in rows]
    sides=[x["side_m"] for x in rows]
    front=min(fronts[-10:]) if len(fronts)>=3 else None
    side=min(sides[-10:]) if len(sides)>=3 else None
    report={"schema":"axia.g07.rollback.initial_scan_readonly_v1",
            "status":label_preclear(front,side),"sample_count":len(rows),
            "front_min_last10_m":front,"side_min_last10_m":side,
            "front_threshold_m":.75,"side_threshold_m":1.2,
            "original_scan_bearing_rad":bearing,"last_scan_samples":rows[-10:],
            "odom_samples":odom[-10:],
            "goal_sent":False,"fault_injected":False,
            "gazebo_entity_moved":False,"owner_accepted":False,
            "gui_render_verified":False,"certified_estop":False}
    with output.open("x",encoding="utf-8") as file:
        json.dump(report,file,indent=2,sort_keys=True);file.write("\n")
    print("AXIA_G07_ROLLBACK_PREGOAL_READONLY "+json.dumps({
        k:report[k] for k in ("status","sample_count",
        "front_min_last10_m","side_min_last10_m",
        "goal_sent","gui_render_verified")},sort_keys=True),flush=True)
    return 0 if len(rows)>=3 else 3

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seconds",type=int,default=10)
    args=p.parse_args()
    if not 5<=args.seconds<=30 or args.output.is_symlink() or args.output.exists():
        raise SystemExit(3)
    try:
        raise SystemExit(run(args.output,args.seconds))
    except (OSError,ValueError) as exc:
        print("AXIA_G07_ROLLBACK_PREGOAL_DIAGNOSTIC_HOLD "+
              type(exc).__name__+":"+str(exc),flush=True)
        raise SystemExit(3)

if __name__=="__main__":
    main()
