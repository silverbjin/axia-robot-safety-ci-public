#!/usr/bin/env python3
"""Actual upstream yolo_ros DetectionArray from a VERIFIED real Gazebo PPM.

This ROS sensor_msgs/Image REPLAY diagnostic is NOT live Gazebo RGB-D, not
a registered depth/D05 test, not moving Goal, not Guard/CM acceptance.
It distinguishes actual C++ yolo_ros postprocessing/NMS output from
offline raw ONNX person candidates on the same real-world pixels.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import time

def ppm_rgb(path:Path)->bytes:
    data=Path(path).read_bytes()
    m=re.match(rb"P6\s+640\s+480\s+255\s",data)
    if not m:
        raise ValueError("UI9_REPLAY_REQUIRES_ACTUAL_640X480_P6_PPM")
    pixels=data[m.end():]
    if len(pixels)!=640*480*3:
        raise ValueError("UI9_PPM_RGB_BYTES_INVALID")
    return pixels

def run(image_path:Path,out:Path,timeout_s:float)->int:
    import rclpy
    from sensor_msgs.msg import Image
    from yolo_msgs.msg import DetectionArray
    from rclpy.qos import qos_profile_sensor_data
    out=Path(out)
    if out.exists() or out.is_symlink():
        raise ValueError("UI9_REPLAY_EVIDENCE_MUST_NOT_EXIST")
    pixels=ppm_rgb(image_path)
    stats=Counter()
    confidences=[]
    rclpy.init()
    node=rclpy.create_node("axia_d08_ui9_real_gazebo_pixel_replay")
    pub=node.create_publisher(
        Image,"/axia/d08/rgbd/image",qos_profile_sensor_data)
    def detect_cb(msg):
        stats["detection_array_count"]+=1
        for d in msg.detections:
            label=str(d.class_name).lower()
            stats[label]+=1
            if label=="person" and int(d.class_id)==0:
                confidences.append(float(d.score))
    sub=node.create_subscription(
        DetectionArray,"/yolo/cam0/detections",detect_cb,
        qos_profile_sensor_data)
    start=time.monotonic()
    next_pub=start
    try:
        while time.monotonic()-start<timeout_s:
            now=time.monotonic()
            if now>=next_pub:
                msg=Image()
                msg.header.stamp=node.get_clock().now().to_msg()
                msg.header.frame_id="axia_d08_rgbd_optical"
                msg.height=480
                msg.width=640
                msg.encoding="rgb8"
                msg.is_bigendian=0
                msg.step=640*3
                msg.data=pixels
                pub.publish(msg)
                stats["published_actual_gazebo_frame_replays"]+=1
                next_pub=now+.2
            rclpy.spin_once(node,timeout_sec=.08)
            if confidences and stats["detection_array_count"]>=3:
                break
        passed=bool(confidences) and stats["detection_array_count"]>=1
        v={
            "status":"PASS_REAL_YOLO_ROS_DETECTIONARRAY_REPLAY" if passed
                     else "BLOCKED_UI9_REAL_YOLO_ROS_PERSON_ZERO",
            "provenance":"ROS_2_REAL_GAZEBO_PPM_PIXEL_REPLAY_L1_ONLY",
            "real_ros_yolo_ros_detection_array":stats["detection_array_count"]>0,
            "actual_gazebo_rgb_pixel_bytes":True,
            "roi_depth_d05_verified":False,"live_gazebo_concurrent":False,
            "moving_goal_sent":False,"certified_estop":False,
            "person_count":len(confidences),
            "person_max_score":max(confidences) if confidences else None,
            "umbrella_count":stats["umbrella"],
            "detection_array_count":stats["detection_array_count"],
            "replays_published":stats["published_actual_gazebo_frame_replays"]
        }
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n")
        print("UI9_REAL_YOLO_ROS_PERSON_DETECTION_L1_"+("PASS" if passed else "BLOCKED")+" "+
              json.dumps({k:v[k] for k in ("person_count","person_max_score",
                        "umbrella_count","detection_array_count")}),flush=True)
        return 0 if passed else 2
    finally:
        node.destroy_node()
        rclpy.shutdown()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ppm",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--timeout-s",type=float,default=55)
    a=p.parse_args()
    raise SystemExit(run(a.ppm,a.out,a.timeout_s))
if __name__=="__main__":main()
