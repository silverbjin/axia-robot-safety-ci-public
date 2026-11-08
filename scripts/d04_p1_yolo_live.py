#!/usr/bin/env python3
"""Real P1 + YOLO simultaneous read-only gate; never commands motion."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from d04_waffle_pi_rgb_preflight import _start, _stop_all, sync_ros_discovery_environment
from d04_yolo_person_runtime import (
    _watch_detections_and_images, model_yaml, valid_person, valid_rgb,
    PINNED_ONNX_SHA256, PINNED_YOLO_SHA)
from d04_p1_vision_overlay import make_overlay

DOMAIN = 40

def preflight_env(a):
    private = a.instructor.resolve()
    if not (private/"tools/p1_t05_graph_oracle.py").is_file():
        raise FileNotFoundError("Actual P1 graph oracle missing")
    if not (private/"ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p1.launch.py").is_file():
        raise FileNotFoundError("Actual P1 launch missing")
    if not a.onnx.is_file() or not a.actor.is_file():
        raise FileNotFoundError("Actual ONNX or human actor missing")
    model_sha=hashlib.sha256(a.onnx.read_bytes()).hexdigest()
    if model_sha!=PINNED_ONNX_SHA256:
        raise ValueError("ONNX model SHA mismatch")
    return private, model_sha

def graph_oracle(root,env,out,label,timeout=125):
    path=out/("graph_"+label+".json")
    try:
        r=subprocess.run([sys.executable,str(root/"tools/p1_t05_graph_oracle.py"),
                          "--output",str(path),"--timeout",str(timeout)],
                         cwd=root,env=env,capture_output=True,text=True,
                         timeout=timeout+15,check=False)
        (out/("graph_"+label+".log")).write_text(r.stdout+"\n"+r.stderr)
    except subprocess.TimeoutExpired:
        return {"passed":False,"reason":"ORACLE_TIMEOUT"}
    if not path.is_file():
        return {"passed":False,"reason":"NO_GRAPH_JSON","rc":r.returncode}
    v=json.loads(path.read_text())
    return {"passed":r.returncode==0 and v.get("verdict",{}).get("passed") is True,
            "rc":r.returncode,"verdict":v.get("verdict",{}),"graph":v.get("graph",{})}

def core_chain(graph):
    topics=("/cmd_vel_smoothed","/cmd_vel_supervised","/cmd_vel")
    return {k:graph[k] for k in topics if k in graph}

def sensor_sample(topic,kind,timeout=20):
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from rosgraph_msgs.msg import Clock
    from sensor_msgs.msg import LaserScan
    from nav_msgs.msg import Odometry
    classes={"clock":Clock,"scan":LaserScan,"odom":Odometry}
    rclpy.init()
    n=rclpy.create_node("axia_d04_sensor_probe_"+kind)
    count=[0]
    n.create_subscription(classes[kind],topic,lambda _:count.__setitem__(0,count[0]+1),qos_profile_sensor_data)
    try:
        end=time.monotonic()+timeout
        while time.monotonic()<end and count[0]<1:
            rclpy.spin_once(n,timeout_sec=0.3)
        return count[0]
    finally:
        n.destroy_node()
        rclpy.shutdown()

def execute(a):
    out=a.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    verdict={
        "gate":"G-D04-3_P1_YOLO_SIMULTANEOUS",
        "status":"BLOCKED_OR_INCONCLUSIVE",
        "p1_expected_sha":a.p1_sha,
        "yolo_source_sha":PINNED_YOLO_SHA,
        "goal_sent":False,"fault_injected":False,
        "cmd_vel_published_by_demo":False,
        "p1_g00_g04_accepted":False,
        "certified_estop_verified":False}
    processes=[]
    env=os.environ.copy()
    env["ROS_DOMAIN_ID"]="40"
    env["ROS_AUTOMATIC_DISCOVERY_RANGE"]="LOCALHOST"
    env["GZ_PARTITION"]="axia_d04_p1_"+str(os.getpid())
    env["LIBGL_ALWAYS_SOFTWARE"]="1"
    env["GALLIUM_DRIVER"]="llvmpipe"
    env["AXIA_P0_SIM_ONLY"]="1"
    env.pop("EGL_PLATFORM",None)
    sync_ros_discovery_environment(env)
    try:
        private,model_sha=preflight_env(a)
        sha=subprocess.check_output(["git","-C",str(private),"rev-parse","HEAD"],text=True).strip()
        if sha!=a.p1_sha:
            raise ValueError("Private P1 SHA mismatch: "+sha)
        verdict["p1_sha_verified"]=sha
        verdict["onnx_sha256"]=model_sha
        overlay=make_overlay(a.waffle,a.pi,a.world,a.actor,out/"overlay",cpu_renderer=a.cpu_renderer)
        verdict["overlay_manifest"]=overlay
        launch=[
            "ros2","launch",str(private/"ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p1.launch.py"),
            "robot_sdf:="+overlay["robot_sdf"],"world:="+overlay["world"],
            ("headless:=False" if a.gui else "headless:=True"),"use_rviz:=False","use_composition:=False",
            "autostart:=true","allow_fault_injection:=false"]
        _start("p1_gazebo_nav2",launch,env,out,processes)
        before=graph_oracle(private,env,out,"before",timeout=140)
        verdict["graph_before_verdict"]=before.get("verdict")
        if not before["passed"]:
            raise RuntimeError("P1 graph not ready before YOLO")
        verdict["clock_samples"]=sensor_sample("/clock","clock")
        verdict["scan_samples"]=sensor_sample("/scan","scan")
        verdict["odom_samples"]=sensor_sample("/odom","odom")
        if not all(verdict[k]>0 for k in ("clock_samples","scan_samples","odom_samples")):
            raise RuntimeError("Actual P1 clock/scan/odom not all received")
        _start("rgb_image_bridge",["ros2","run","ros_gz_image","image_bridge","/camera/image_raw"],env,out,processes)
        params=out/"yolo.yaml"
        params.write_text(model_yaml(a.onnx))
        _start("yolo_node",["ros2","launch","yolo_bringup","yolo.launch.py",
                           "params_file:="+str(params.resolve())],env,out,processes)
        if a.gui:\n            # Optional GUI observer, not part of safety gate or YOLO oracle.\n            _start("yolo_image_view",["ros2","run","image_view","image_view",\n                       "--ros-args","-r","image:=/yolo/cam0/debug_image"],env,out,processes)\n        during=graph_oracle(private,env,out,"during",timeout=65)
        verdict["graph_during_verdict"]=during.get("verdict")
        if not during["passed"]:
            raise RuntimeError("P1 graph disrupted by D04 vision sidecar")
        if core_chain(before["graph"])!=core_chain(during["graph"]):
            raise RuntimeError("P1 command chain changed by D04")
        verdict["graph_unchanged"]=True
        vision=_watch_detections_and_images(out,duration_s=120)
        verdict["vision"]=vision
        verdict["person_valid"]=bool(vision.get("person") and valid_person(vision["person"]))
        verdict["rgb_valid"]=bool(vision.get("first_image") and valid_rgb(vision["first_image"]))
        verdict["debug_saved"]=vision.get("debug_saved") is True
        if not all(verdict[k] for k in ("person_valid","rgb_valid","debug_saved")):
            raise RuntimeError("No actual person/bbox/debug in P1 mixed Gazebo")
        verdict["status"]="PASS_P1_GRAPH_UNCHANGED_REAL_PERSON"\n        if a.gui and a.display_hold>0:\n            time.sleep(min(a.display_hold,60))
    except Exception as exc:
        verdict["blocker"]=type(exc).__name__+": "+str(exc)[:400]
    finally:
        _stop_all(processes,verdict)
        (out/"verdict.json").write_text(json.dumps(verdict,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps({k:verdict.get(k) for k in (
            "gate","status","blocker","graph_before_verdict","graph_during_verdict",
            "graph_unchanged","clock_samples","scan_samples","odom_samples","person_valid",
            "rgb_valid","debug_saved")},ensure_ascii=False))
    return 0 if verdict["status"].startswith("PASS_") else 2

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("instructor","waffle","pi","world","actor","onnx","out"):
        p.add_argument("--"+k,required=True,type=Path)
    p.add_argument("--p1-sha",required=True)
    p.add_argument("--cpu-renderer",action="store_true")\n    p.add_argument("--gui",action="store_true",help="Show Gazebo and image_view if WSLg is available")\n    p.add_argument("--display-hold",type=int,default=0)
    raise SystemExit(execute(p.parse_args()))
