#!/usr/bin/env python3
"""Real Gazebo RGBD + upstream YOLO + private D05 read-only ROS acceptance.

No fake frames. Verifies actual VALID person range, then disables only the
Depth bridge while RGB/YOLO stay live and requires UNKNOWN/null transition.
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

from d04_waffle_pi_rgb_preflight import _start, _stop_all, sync_ros_discovery_environment
from d04_yolo_person_runtime import model_yaml
from d05_rgbd_gazebo_scene import make_world, RGB_TOPIC, DEPTH_TOPIC, WIDTH, HEIGHT

STATUS_TOPIC = "/axia/d05/person_range_status"
DETECTION_TOPIC = "/yolo/cam0/detections"
DEBUG_TOPIC = "/yolo/cam0/debug_image"


def _stamp_ns(msg):
    return msg.header.stamp.sec*10**9 + msg.header.stamp.nanosec


def _image_meta(msg):
    return {"stamp_ns":_stamp_ns(msg),"frame_id":msg.header.frame_id,
            "width":msg.width,"height":msg.height,"encoding":msg.encoding,
            "step":msg.step,"byte_count":len(msg.data),
            "sha256":hashlib.sha256(msg.data).hexdigest()}


def _save_png(msg, filename: Path) -> bool:
    if msg.encoding.lower() not in ("rgb8","bgr8") or msg.width != WIDTH or msg.height != HEIGHT:
        return False
    try:
        import cv2
        import numpy as np
        data=np.frombuffer(msg.data,dtype=np.uint8).reshape((msg.height,msg.step))
        data=data[:,:msg.width*3].reshape((msg.height,msg.width,3))
        if msg.encoding.lower()=="rgb8":
            data=cv2.cvtColor(data,cv2.COLOR_RGB2BGR)
        return bool(cv2.imwrite(str(filename),data))
    except Exception:
        return False


def _monitor(out: Path, depth_bridge, wait_s: int = 180):
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image
    from std_msgs.msg import String
    from yolo_msgs.msg import DetectionArray

    rclpy.init()
    node=rclpy.create_node("axia_d05_real_person_range_verifier")
    evidence={"status_samples":[], "source_counts":{"rgb":0,"depth":0,"detections":0,"debug":0},
              "first_frame":{}, "person_examples":[], "valid_status":None,
              "unknown_after_loss":None, "depth_bridge_shutdown":None,
              "rgb_continued_after_loss":False, "yolo_continued_after_loss":False,
              "rgb_debug_png_saved":False}
    in_loss=False
    counts_before=None
    first_debug=False

    def image_cb(msg, channel):
        nonlocal first_debug
        evidence["source_counts"][channel]+=1
        if channel not in evidence["first_frame"]:
            evidence["first_frame"][channel]=_image_meta(msg)
        if channel == "debug" and not first_debug:
            first_debug=_save_png(msg,out/"person_yolo_debug.png")
            evidence["rgb_debug_png_saved"]=first_debug

    def detection_cb(msg):
        evidence["source_counts"]["detections"]+=1
        if len(evidence["person_examples"])>=8:
            return
        for d in msg.detections:
            if str(d.class_name).lower()=="person" and int(d.class_id)==0:
                evidence["person_examples"].append({
                    "stamp_ns":_stamp_ns(msg),"frame_id":msg.header.frame_id,
                    "confidence":float(d.score),
                    "center_x":float(d.bbox.center.position.x),
                    "center_y":float(d.bbox.center.position.y),
                    "size_x":float(d.bbox.size.x),
                    "size_y":float(d.bbox.size.y)})
                break

    def status_cb(msg):
        try:
            data=json.loads(msg.data)
        except (TypeError,ValueError):
            data={"status":"INVALID_JSON","distance_m":None}
        if len(evidence["status_samples"])<500:
            evidence["status_samples"].append(data)
        if not in_loss and data.get("status")=="VALID":
            if evidence["valid_status"] is None:
                evidence["valid_status"]=data
        if in_loss and data.get("status")=="UNKNOWN" and data.get("distance_m") is None:
            if evidence["unknown_after_loss"] is None and data.get("reason") in (
                    "STALE_INPUT","MISSING_INPUT","STAMP_SKEW"):
                evidence["unknown_after_loss"]=data

    subs=[
        node.create_subscription(Image,RGB_TOPIC,lambda m:image_cb(m,"rgb"),qos_profile_sensor_data),
        node.create_subscription(Image,DEPTH_TOPIC,lambda m:image_cb(m,"depth"),qos_profile_sensor_data),
        node.create_subscription(Image,DEBUG_TOPIC,lambda m:image_cb(m,"debug"),qos_profile_sensor_data),
        node.create_subscription(DetectionArray,DETECTION_TOPIC,detection_cb,qos_profile_sensor_data),
        node.create_subscription(String,STATUS_TOPIC,status_cb,10)
    ]
    try:
        deadline=time.monotonic()+wait_s
        while time.monotonic()<deadline and evidence["valid_status"] is None:
            rclpy.spin_once(node,timeout_sec=0.5)
        v=evidence["valid_status"]
        if v is None:
            evidence["blocker"]="NO_REAL_VALID_PERSON_RANGE"
            return evidence
        if not (v.get("safety_certified") is False
                and isinstance(v.get("distance_m"), (int,float))
                and math.isfinite(v["distance_m"]) and 1.0<v["distance_m"]<4.0
                and v.get("valid_count",0)>0
                and v.get("valid_fraction",0)>=0.5
                and v.get("frame_stamp_ns",0)>0
                and v.get("depth_stamp_ns",0)>0
                and v.get("detection_stamp_ns",0)>0):
            evidence["blocker"]="INVALID_VALID_DISTANCE_OR_SCENE_GEOMETRY"
            return evidence
        if (not evidence["person_examples"]
                or evidence["source_counts"]["rgb"]<1
                or evidence["source_counts"]["depth"]<1
                or evidence["source_counts"]["detections"]<1):
            evidence["blocker"]="MISSING_REAL_RAW_SENSOR_OR_YOLO_EVIDENCE"
            return evidence
        print("[D05][VALID] actual person range "+json.dumps(
            {"distance_m":v["distance_m"],"fraction":v["valid_fraction"],
             "bbox":v.get("bbox_roi_xyxy")}),flush=True)

        counts_before=dict(evidence["source_counts"])
        in_loss=True
        if depth_bridge.poll() is None:
            os.killpg(depth_bridge.pid,signal.SIGINT)
            try:
                depth_bridge.wait(timeout=12)
            except subprocess.TimeoutExpired:
                os.killpg(depth_bridge.pid,signal.SIGTERM)
                depth_bridge.wait(timeout=8)
        evidence["depth_bridge_shutdown"]={"exit_code":depth_bridge.returncode,
                                            "after_valid":True}
        print("[D05][FAULT] depth bridge ONLY stopped. No ROS fault injector, motion or Goal.",flush=True)
        deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=.3)
            after=evidence["source_counts"]
            evidence["rgb_continued_after_loss"]=after["rgb"]>counts_before["rgb"]
            evidence["yolo_continued_after_loss"]=after["detections"]>counts_before["detections"]
            if (evidence["unknown_after_loss"] is not None
                    and evidence["rgb_continued_after_loss"]
                    and evidence["yolo_continued_after_loss"]):
                break
        if evidence["unknown_after_loss"] is None:
            evidence["blocker"]="NO_UNKNOWN_NULL_AFTER_DEPTH_BRIDGE_LOSS"
        elif not evidence["rgb_continued_after_loss"]:
            evidence["blocker"]="RGB_DID_NOT_CONTINUE_DURING_DEPTH_LOSS"
        elif not evidence["yolo_continued_after_loss"]:
            evidence["blocker"]="YOLO_DID_NOT_CONTINUE_DURING_DEPTH_LOSS"
        else:
            evidence["passed"]=True
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return evidence


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--model",type=Path,required=True)
    p.add_argument("--actor",type=Path,required=True)
    p.add_argument("--private-sha",required=True)
    p.add_argument("--wait-s",type=int,default=180)
    a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    result={"gate":"G-D05-REAL-RGBD-VALID-TO-UNKNOWN",
            "status":"BLOCKED","private_sha":a.private_sha,
            "p1_g00_g04_accepted":False,"goal_sent":False,
            "fault_injected":False,"cmd_vel_published":False,
            "certified_estop":False}
    env=os.environ.copy()
    env["ROS_DOMAIN_ID"]="62"
    env["ROS_AUTOMATIC_DISCOVERY_RANGE"]="LOCALHOST"
    env["GZ_PARTITION"]="axia_d05_rgbd_"+str(os.getpid())
    env["LIBGL_ALWAYS_SOFTWARE"]="1"
    env["GALLIUM_DRIVER"]="llvmpipe"
    env.pop("EGL_PLATFORM",None)
    sync_ros_discovery_environment(env)
    processes=[]
    try:
        model=a.model.resolve();actor=a.actor.resolve()
        if not model.is_file() or not actor.is_file():
            raise FileNotFoundError("Pinned external model/actor not present")
        model_sha=hashlib.sha256(model.read_bytes()).hexdigest()
        actor_sha=hashlib.sha256(actor.read_bytes()).hexdigest()
        if model_sha!="4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf":
            raise ValueError("Unpinned ONNX weights")
        if actor_sha!="49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e":
            raise ValueError("Unpinned actor mesh")
        result["model_sha256"]=model_sha
        result["actor_sha256"]=actor_sha
        from ament_index_python.packages import get_package_share_directory
        share=Path(get_package_share_directory("turtlebot3_gazebo"))
        env["GZ_SIM_RESOURCE_PATH"]=str(share/"models")+":"+env.get("GZ_SIM_RESOURCE_PATH","")
        world=out/"d05_actual_person_rgbd.sdf"
        world.write_text(make_world(actor_mesh=actor),encoding="utf-8")
        result["world_sha256"]=hashlib.sha256(world.read_bytes()).hexdigest()
        yolo_params=out/"yolo_registered_rgbd.yaml"
        base=model_yaml(model)
        if base.count("rgb_topic: /camera/image_raw")!=1:
            raise RuntimeError("Pinned D04 YOLO configuration changed")
        yolo_params.write_text(base.replace("rgb_topic: /camera/image_raw",
                                             "rgb_topic: "+RGB_TOPIC),encoding="utf-8")
        _start("gazebo_server",["xvfb-run","-a","-s","-screen 0 1280x720x24",
               "gz","sim","-r","-s","-v3",str(world)],env,out,processes)
        _start("rgb_bridge",["ros2","run","ros_gz_image","image_bridge",RGB_TOPIC],
               env,out,processes)
        depth_bridge=_start("depth_bridge",["ros2","run","ros_gz_image","image_bridge",DEPTH_TOPIC],
                            env,out,processes)
        _start("yolo",["ros2","launch","yolo_bringup","yolo.launch.py",
               "params_file:="+str(yolo_params)],env,out,processes)
        _start("d05_observer",["ros2","run","axia_d05_depth_demo","d05_range_observer",
               "--ros-args","-p","rgb_topic:="+RGB_TOPIC,
               "-p","depth_topic:="+DEPTH_TOPIC,
               "-p","detections_topic:="+DETECTION_TOPIC,
               "-p","aligned_to_rgb:=true",
               "-p","max_skew_s:=0.05","-p","max_age_s:=0.5",
               "-p","min_confidence:=0.15"],env,out,processes)
        print("[D05][L2] Gazebo single RGBD + actual YOLO + private observer launched",flush=True)
        actual=_monitor(out,depth_bridge,wait_s=a.wait_s)
        result.update(actual)
        if actual.get("passed") is True:
            result["status"]="PASS_REAL_GAZEBO_PERSON_RANGE_VALID_TO_UNKNOWN"
        else:
            result["blocker"]=actual.get("blocker","MISSING_ACTUAL_EVIDENCE")
    except Exception as exc:
        result["blocker"]=type(exc).__name__+":"+str(exc)[:500]
        print("[D05][BLOCKED] "+result["blocker"],flush=True)
    finally:
        _stop_all(processes,result)
        # Never export licensed weights or private source to CI artifacts.
        files=sorted(f for f in out.iterdir() if f.is_file() and f.name!="SHA256SUMS")
        (out/"verdict.json").write_text(json.dumps(result,indent=2,
                                                ensure_ascii=False,allow_nan=False)+"\n")
        files=sorted(f for f in out.iterdir() if f.is_file() and f.name!="SHA256SUMS")
        (out/"SHA256SUMS").write_text("".join(hashlib.sha256(f.read_bytes()).hexdigest()
                   +"  "+f.name+"\n" for f in files),encoding="utf-8")
        print(json.dumps({k:result.get(k) for k in
            ("status","blocker","valid_status","unknown_after_loss",
             "rgb_continued_after_loss","yolo_continued_after_loss")},allow_nan=False),flush=True)
    return 0 if result["status"]=="PASS_REAL_GAZEBO_PERSON_RANGE_VALID_TO_UNKNOWN" else 2

if __name__=="__main__":
    raise SystemExit(main())
