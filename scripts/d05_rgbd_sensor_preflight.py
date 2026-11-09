#!/usr/bin/env python3
"""Actually start Gazebo Harmonic RGBD sensor and bridge real RGB/depth.

No YOLO yet. Proves sensor source before expensive C++ YOLO build.
A PASS here is not D05 person distance acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

from d04_waffle_pi_rgb_preflight import _start, _stop_all, sync_ros_discovery_environment
from d05_rgbd_gazebo_scene import make_world, RGB_TOPIC, DEPTH_TOPIC, WIDTH, HEIGHT

def _metadata(msg):
    stamp = msg.header.stamp.sec*10**9 + msg.header.stamp.nanosec
    out = {"stamp_ns":stamp, "frame_id":msg.header.frame_id,
           "width":msg.width,"height":msg.height,"encoding":msg.encoding,
           "is_bigendian":msg.is_bigendian,"step":msg.step,
           "payload_bytes":len(msg.data),
           "payload_sha256":hashlib.sha256(msg.data).hexdigest()}
    if msg.encoding == "32FC1" and msg.step>=msg.width*4 and len(msg.data)>=msg.step*msg.height:
        off=(msg.height//2)*msg.step+(msg.width//2)*4
        sample=struct.unpack_from(
            (">" if msg.is_bigendian else "<")+"f",msg.data,off)[0]
        out["center_depth_m"]=sample if math.isfinite(sample) else None
    return out

def _observe(timeout_s):
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image
    rclpy.init()
    node=rclpy.create_node("axia_d05_actual_rgbd_preflight")
    received={"rgb":[],"depth":[]}
    def cb(msg,kind):
        if len(received[kind])<8:
            received[kind].append(_metadata(msg))
    node.create_subscription(Image,RGB_TOPIC,lambda m:cb(m,"rgb"),qos_profile_sensor_data)
    node.create_subscription(Image,DEPTH_TOPIC,lambda m:cb(m,"depth"),qos_profile_sensor_data)
    try:
        deadline=time.monotonic()+timeout_s
        while time.monotonic()<deadline and not all(len(rows)>=3 for rows in received.values()):
            rclpy.spin_once(node,timeout_sec=.5)
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return received

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--timeout-s",type=int,default=80)
    a=parser.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    evidence={"gate":"G-D05-REAL-GAZEBO-RGBD-SENSOR",
              "status":"BLOCKED","person_range_accepted":False,
              "goal_sent":False,"fault_injected":False,
              "cmd_vel_published":False,"certified_estop":False}
    processes=[]
    env=os.environ.copy()
    env["ROS_DOMAIN_ID"]="61"
    env["ROS_AUTOMATIC_DISCOVERY_RANGE"]="LOCALHOST"
    env["GZ_PARTITION"]="axia_d05_sensor_"+str(os.getpid())
    env["LIBGL_ALWAYS_SOFTWARE"]="1"
    env["GALLIUM_DRIVER"]="llvmpipe"
    env.pop("EGL_PLATFORM",None)
    sync_ros_discovery_environment(env)
    try:
        from ament_index_python.packages import get_package_share_directory
        share=Path(get_package_share_directory("turtlebot3_gazebo"))
        env["GZ_SIM_RESOURCE_PATH"]=str(share/"models")+":"+env.get("GZ_SIM_RESOURCE_PATH","")
        world=out/"rgbd_sensor_only.sdf"
        world.write_text(make_world(),encoding="utf-8")
        evidence["world_sha256"]=hashlib.sha256(world.read_bytes()).hexdigest()
        _start("gazebo_server",["xvfb-run","-a","-s","-screen 0 1280x720x24",
           "gz","sim","-r","-s","-v3",str(world)],env,out,processes)
        for channel,topic in (("rgb_bridge",RGB_TOPIC),("depth_bridge",DEPTH_TOPIC)):
            _start(channel,["ros2","run","ros_gz_image","image_bridge",topic],env,out,processes)
        print("[D05][SENSOR] Waiting for actual Gazebo RGBD images...",flush=True)
        observed=_observe(a.timeout_s)
        evidence["ros_frames"]=observed
        pairs=[
            (rgb,depth) for rgb in observed["rgb"] for depth in observed["depth"]
            if rgb["frame_id"] and rgb["frame_id"]==depth["frame_id"]
            and rgb["width"]==depth["width"]==WIDTH
            and rgb["height"]==depth["height"]==HEIGHT
            and rgb["stamp_ns"]>0 and depth["stamp_ns"]>0
            and abs(rgb["stamp_ns"]-depth["stamp_ns"])<=50_000_000]
        evidence["matched_rgbd_pairs"]=len(pairs)
        if not pairs:
            evidence["blocker"]="NO_REAL_REGISTERED_RGBD_FRAME_PAIR"
        elif not any(d["encoding"]=="32FC1" and d.get("center_depth_m") is not None
                     and 0.15<=d["center_depth_m"]<=8.0
                     for _,d in pairs):
            evidence["blocker"]="NO_VALID_REAL_GAZEBO_DEPTH_PIXEL"
        else:
            evidence["status"]="PASS_REAL_GAZEBO_REGISTERED_RGBD_SENSOR_ONLY"
        listing=subprocess.run(["gz","topic","-l"],env=env,capture_output=True,text=True,
                               timeout=12,check=False)
        (out/"gz_topics.txt").write_text(listing.stdout+"\n"+listing.stderr)
    except Exception as exc:
        evidence["blocker"]=type(exc).__name__+":"+str(exc)[:350]
    finally:
        _stop_all(processes,evidence)
        (out/"verdict.json").write_text(json.dumps(evidence,indent=2,allow_nan=False)+"\n")
        files=sorted(f for f in out.iterdir() if f.is_file() and f.name!="SHA256SUMS")
        (out/"SHA256SUMS").write_text("".join(
            hashlib.sha256(f.read_bytes()).hexdigest()+"  "+f.name+"\n" for f in files))
        print(json.dumps({k:evidence.get(k) for k in
                         ("status","blocker","matched_rgbd_pairs","ros_frames")},
                         ensure_ascii=False,allow_nan=False),flush=True)
    return 0 if evidence["status"]=="PASS_REAL_GAZEBO_REGISTERED_RGBD_SENSOR_ONLY" else 2

if __name__=="__main__":
    raise SystemExit(main())
