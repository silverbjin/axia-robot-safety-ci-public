#!/usr/bin/env python3
"""D08 public ROS read-only *live* D05 person ROI distance adapter.

Actual yolo_msgs/DetectionArray + Gazebo Image RGB/32FC1 depth are REQUIRED.
The strict public D05 contract computes median meters or reasoned UNKNOWN.
No private instructor solution, fake Image, robot Goal or cmd_vel publisher.
"""
from __future__ import annotations
from collections import Counter, deque
import json
from pathlib import Path
import time

from d08_live_readonly_probe import (
    RGB_TOPIC, DEPTH_TOPIC, DETECTIONS_TOPIC,
    bbox_from_real_detection, stamp)
from d08_public_person_range import assess_public_person_range


def stage_contract(verdict, expected):
    """L0 gate; a missing detector is never a valid person-range pass."""
    if expected == "valid":
        if (verdict.get("status") != "VALID" or
            verdict.get("distance_m") is None or
            verdict.get("valid_count",0)<8 or
            verdict.get("registered_rgbd_from_actual_sensor") is not True or
            verdict.get("actual_yolo_person") is not True):
            raise ValueError("D08_LIVE_RANGE_NOT_VALID")
    elif expected == "unknown":
        if (verdict.get("status")!="UNKNOWN" or
            verdict.get("reason") not in (
                "NO_PERSON_CLASS_IN_ACTUAL_YOLO",
                "PERSON_LOST_AFTER_REAL_PROXY_MOVE") or
            verdict.get("actual_rgbd_samples",0)<3 or
            verdict.get("actual_yolo_detection_arrays",0)<2 or
            verdict.get("registered_rgbd_from_actual_sensor") is not True):
            raise ValueError("D08_LIVE_UNKNOWN_NOT_OBSERVED")
    else:
        raise ValueError("D08_RANGE_EXPECTATION_INVALID")
    if verdict.get("control_published") is not False:
        raise ValueError("D08_RANGE_PROBE_MUST_BE_READ_ONLY")
    return True


def run(out:Path, *, registration_sha:str, expected:str,
        timeout_s:float=55.,source_sha:str="",min_settle_s:float=1.):
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from rclpy.parameter import Parameter
    from sensor_msgs.msg import Image
    from yolo_msgs.msg import DetectionArray
    if expected not in ("valid","unknown"):
        raise ValueError("D08_RANGE_EXPECTATION_INVALID")
    out=Path(out)
    if out.exists() or out.is_symlink():
        raise ValueError("D08_RANGE_EVIDENCE_EXISTS")
    out.parent.mkdir(parents=True,exist_ok=True)
    rgb=deque(maxlen=12)
    depth=deque(maxlen=12)
    detections=deque(maxlen=16)
    reasons=Counter()
    classes=Counter()
    verdict={"status":"UNKNOWN","reason":"NOT_OBSERVED",
             "distance_m":None,"expected":expected,
             "actual_rgbd_samples":0,
             "actual_yolo_detection_arrays":0,
             "actual_yolo_person":False,
             "registered_rgbd_from_actual_sensor":False,
             "control_published":False,"goal_sent":False,
             "certified_estop":False,"source_sha":source_sha,
             "registration_sdf_sha256":registration_sha,
             "sensor_source":"same_running_gazebo_rgbd_registered_sdf",
             "detection_source":"original_yolo_ros_DetectionArray_live"}
    rclpy.init()
    node=Node("axia_d08_public_live_d05_range_no_goal",
      parameter_overrides=[Parameter("use_sim_time",value=True)],
      automatically_declare_parameters_from_overrides=True)
    created=time.monotonic()
    def rgb_cb(m):
        rgb.append((time.monotonic(),m))
        verdict["actual_rgbd_samples"]+=1
    def depth_cb(m):
        depth.append((time.monotonic(),m))
    def det_cb(m):
        detections.append((time.monotonic(),m))
        verdict["actual_yolo_detection_arrays"]+=1
        for d in m.detections:
            classes[str(d.class_name).lower()]+=1
    subs=[
        node.create_subscription(Image,RGB_TOPIC,rgb_cb,qos_profile_sensor_data),
        node.create_subscription(Image,DEPTH_TOPIC,depth_cb,qos_profile_sensor_data),
        node.create_subscription(DetectionArray,DETECTIONS_TOPIC,
                                 det_cb,qos_profile_sensor_data),
    ]
    attempted=set()
    actual_no_person=0
    try:
        end=time.monotonic()+timeout_s
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.12)
            now=time.monotonic()
            if now-created<min_settle_s or not(rgb and depth and detections):
                continue
            for det_at,dm in reversed(detections):
                if det_at<created+min_settle_s:
                    continue
                dts=stamp(dm)
                if dts<=0:
                    reasons["DETECTION_STAMP_MISSING"]+=1
                    continue
                if dts in attempted:
                    continue
                attempted.add(dts)
                valid_person_bboxes=[
                    bbox_from_real_detection(d,640,480) for d in dm.detections]
                valid_person_bboxes=[x for x in valid_person_bboxes if x is not None]
                if not valid_person_bboxes:
                    # A real no-person DetectionArray counts as UNKNOWN only
                    # when generated from the same actual registered RGBD
                    # sensor and with fresh host monotonic arrival times.
                    registered=any(
                        rr.header.frame_id==dd.header.frame_id==dm.header.frame_id
                        and rr.header.frame_id=="axia_d08_rgbd_optical"
                        and rr.width==dd.width==640
                        and rr.height==dd.height==480
                        and dd.encoding=="32FC1"
                        and abs(stamp(rr)-stamp(dd))<=50_000_000
                        and abs(stamp(rr)-dts)<=50_000_000
                        and 0<=now-rr_at<=.5
                        and 0<=now-dd_at<=.5
                        for rr_at,rr in rgb for dd_at,dd in depth)
                    if registered and 0<=now-det_at<=.5:
                        actual_no_person+=1
                        verdict["registered_rgbd_from_actual_sensor"]=True
                        verdict["last_detection_stamp_ns"]=dts
                    else:
                        reasons["UNKNOWN_RGBD_OR_DETECTION_NOT_FRESH_REGISTERED"]+=1
                    continue
                if expected=="unknown":
                    # If a person remains in the physical camera, do not
                    # turn it into CLEAR or pretend it was absent.
                    reasons["ACTUAL_PERSON_STILL_VISIBLE"]+=1
                    continue
                best=max(valid_person_bboxes,key=lambda x:x["confidence"])
                verdict["actual_yolo_person"]=True
                observed=False
                for dr_at,dp in reversed(depth):
                    if abs(stamp(dp)-dts)>50_000_000:continue
                    for rgb_at,rp in reversed(rgb):
                        if abs(stamp(rp)-dts)>50_000_000:continue
                        measure=assess_public_person_range(
                            rp,dp,dts,dm.header.frame_id,best,
                            {"rgb":rgb_at,"depth":dr_at,"detection":det_at},
                            now,registration_sha)
                        observed=True
                        if measure["status"]=="VALID":
                            verdict.update(measure)
                            verdict["registered_rgbd_from_actual_sensor"]=True
                            verdict["actual_yolo_person"]=True
                            verdict["bbox"]=best
                            verdict["detection_score"]=best["confidence"]
                            break
                        reasons[measure["reason"]]+=1
                    if verdict["status"]=="VALID":break
                if not observed:
                    reasons["NO_REAL_RGB_DEPTH_YOLO_STAMP_TRIAD"]+=1
                if verdict["status"]=="VALID":break
            if verdict["status"]=="VALID":break
            if (expected=="unknown" and actual_no_person>=2
                and verdict["actual_rgbd_samples"]>=3
                and verdict["actual_yolo_detection_arrays"]>=2):
                verdict["reason"]="NO_PERSON_CLASS_IN_ACTUAL_YOLO"
                verdict["actual_yolo_person"]=False
                verdict["registered_rgbd_from_actual_sensor"]=True
                break
        # Ground the UNKNOWN and blocked cases with last actual ROS
        # source stamps plus host receive ages; a reason string alone is not
        # a triad timing proof.
        stamp_now=time.monotonic()
        if rgb:
            verdict["last_rgb_stamp_ns"]=stamp(rgb[-1][1])
            verdict["last_rgb_receive_age_s"]=round(stamp_now-rgb[-1][0],6)
        if depth:
            verdict["last_depth_stamp_ns"]=stamp(depth[-1][1])
            verdict["last_depth_receive_age_s"]=round(stamp_now-depth[-1][0],6)
        if detections:
            verdict["last_detection_stamp_ns"]=stamp(detections[-1][1])
            verdict["last_detection_receive_age_s"]=round(stamp_now-detections[-1][0],6)
        verdict["debug_reasons"]=dict(reasons)
        verdict["observed_classes"]=dict(classes)
        verdict["rgb_count"]=verdict["actual_rgbd_samples"]
        verdict["depth_count"]=len(depth)
        verdict["detection_array_count"]=verdict["actual_yolo_detection_arrays"]
        if expected=="unknown" and verdict["reason"]=="NOT_OBSERVED":
            if verdict["actual_yolo_detection_arrays"]<2:
                verdict["reason"]="YOLO_DETECTION_STREAM_MISSING"
            elif verdict["actual_rgbd_samples"]<3 or len(depth)<3:
                verdict["reason"]="LIVE_RGBD_STREAM_MISSING"
            else:
                verdict["reason"]="PERSON_LOST_AFTER_REAL_PROXY_MOVE" if (
                    actual_no_person>=2) else "NO_FRESH_VALID_TRIAD_OR_PERSON"
        if expected=="valid" and verdict["status"]!="VALID":
            verdict["reason"]=(
                "LIVE_D05_FIRST_BOUNDARY_"+(
                  reasons.most_common(1)[0][0] if reasons else
                  "PERSON_OR_RGBD_DETECTION_MISSING"))
        try:
            stage_contract(verdict,expected)
            verdict["acceptance"]="D08_PUBLIC_PERSON_RANGE_"+expected.upper()+"_L2_PASS"
            rc=0
        except ValueError as exc:
            verdict["acceptance"]="HOLD"
            verdict["first_boundary"]=str(exc)
            rc=2
        out.write_text(json.dumps(verdict,indent=2,sort_keys=True)+"\n")
        print("D08_LIVE_D05_ACTUAL_"+expected.upper()+"_"+(
          "PASS" if rc==0 else "HOLD")+" "+
          json.dumps({k:verdict.get(k) for k in (
            "distance_m","reason","actual_rgbd_samples",
            "actual_yolo_detection_arrays","detection_score",
            "first_boundary")},sort_keys=True),flush=True)
        return rc
    finally:
        node.destroy_node()
        rclpy.shutdown()


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--registration-sha",required=True)
    p.add_argument("--expected",choices=("valid","unknown"),required=True)
    p.add_argument("--timeout-s",type=float,default=55.)
    p.add_argument("--source-sha",default="")
    a=p.parse_args()
    raise SystemExit(run(a.out,registration_sha=a.registration_sha,
                         expected=a.expected,timeout_s=a.timeout_s,
                         source_sha=a.source_sha))

if __name__=="__main__":
    main()
