#!/usr/bin/env python3
"""D08 minimum live RGB-D/YOLO read-only D05 three-stage classroom session.

The same physical human Proxy has Gazebo-native pose changes only. Uses the
already running official Nav2 world and C++ yolo_ros; never publishes velocity,
Navigation Goals, synthetic scan, fake images, or Instructor solutions.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from d08_live_person_range import run as measure_live

STAGES=(
    ("farther",(-1.20,-.5,.24),"valid"),
    ("stop",(-1.63,-.5,.24),"valid"),
    ("unknown",(-1.9791189342778877,.17129139623634398,.24),"unknown"),
)
RESTORE=(-.58,-.5,.24)


def grade_actual_person_stages(rows):
    if [x.get("stage") for x in rows] != ["farther","stop","unknown"]:
        raise ValueError("D08_LIVE_TWO_VALID_ONE_UNKNOWN_STAGES_MISSING")
    a,b,u=rows
    if any(x.get("native_ack") is not True for x in rows):
        raise ValueError("D08_REAL_HUMAN_NATIVE_POSE_ACK_MISSING")
    if not (a.get("roi_status")=="VALID" and b.get("roi_status")=="VALID"
            and u.get("roi_status")=="UNKNOWN"):
        raise ValueError("D08_TWO_REAL_VALID_AND_UNKNOWN_NOT_OBSERVED")
    if any(x.get("registration_confirmed") is not True for x in rows):
        raise ValueError("D08_RGBD_REGISTRATION_PROOF_MISSING")
    v1,v2=a.get("distance_m"),b.get("distance_m")
    if not (type(v1) in (float,int) and type(v2) in (float,int)):
        raise ValueError("D08_TWO_ACTUAL_PERSON_DISTANCES_NOT_DISTINCT")
    # Physical person is closer during Stop; an inverted ROI trend must
    # never pass merely because its absolute difference is large.
    if v1<=v2:
        raise ValueError("D08_PERSON_DISTANCE_DIRECTION_INCONSISTENT")
    if v1-v2<.12:
        raise ValueError("D08_TWO_ACTUAL_PERSON_DISTANCES_NOT_DISTINCT")
    if u.get("reason")!="NO_PERSON_CLASS_IN_ACTUAL_YOLO":
        raise ValueError("D08_UNKNOWN_NOT_ACTUAL_NO_PERSON")
    return {"status":"D08_REAL_LIVE_PERSON_RANGE_2VALID_UNKNOWN_L2_PASS_NO_GOAL",
            "valid_distance_far_m":v1,"valid_distance_stop_m":v2,
            "valid_distance_delta_m":round(v1-v2,5),
            "unknown_reason":u["reason"],
            "robot_goal_sent":False,"cmd_vel_published":False}


def run_session(out:Path, env:dict, source_sha:str, robot_sdf:Path, scan_probe):
    out=Path(out)
    if out.exists() or out.is_symlink():
        raise ValueError("D08_REAL_RANGE_OUTPUT_EXISTS")
    out.mkdir(parents=True)
    sdf=Path(robot_sdf)
    if not sdf.is_file() or sdf.is_symlink():
        raise RuntimeError("D08_LIVE_REGISTERED_WAFFLE_SDF_MISSING")
    root=ET.parse(sdf).getroot()
    sensors=root.findall(".//sensor[@name='axia_d08_registered_rgbd']")
    if (len(sensors)!=1 or sensors[0].get("type")!="rgbd_camera" or
        sensors[0].findtext("./gz_frame_id")!="axia_d08_rgbd_optical" or
        sensors[0].findtext("./camera/image/width")!="640" or
        sensors[0].findtext("./camera/image/height")!="480"):
        raise RuntimeError("D08_LIVE_ONE_REGISTERED_GAZEBO_RGBD_SDF_NOT_PROVEN")
    robot_hash=hashlib.sha256(sdf.read_bytes()).hexdigest()
    v={"status":"HOLD","goal_sent":False,"cmd_vel_published":False,
       "source_sha":source_sha,"robot_sdf_sha256":robot_hash,
       "registration":"SAME_SINGLE_RGBD_SENSOR_OPTICAL_640X480",
       "world":"same_actual_nav2_gazebo_world",
       "ros_domain_id":env.get("ROS_DOMAIN_ID"),
       "gz_partition":env.get("GZ_PARTITION"),
       "stages":[]}
    moved=False

    def pose(stage,xyz):
        # Native Gazebo service, only ONE pre-existing human model. No robot.
        request=('name: "axia_p2_g07_obstacle", '
          'position: {x: %.9f, y: %.9f, z: %.4f}, orientation: {w: 1}'%
          xyz)
        cp=subprocess.run(
          ["gz","service","-s","/world/default/set_pose",
           "--reqtype","gz.msgs.Pose","--reptype","gz.msgs.Boolean",
           "--timeout","5000","--req",request],
          env=env,text=True,capture_output=True,timeout=13,check=False)
        (out/(stage+"_native_ack.txt")).write_text(cp.stdout+cp.stderr)
        if cp.returncode!=0 or "data: true" not in cp.stdout:
            raise RuntimeError("D08_PERSON_"+stage.upper()+"_GAZEBO_NATIVE_ACK_MISSING")
        return True

    try:
        for stage,world_xyz,expected in STAGES:
            moved=True
            ack=pose(stage,world_xyz)
            scan=None
            if stage!="unknown":
                scan=scan_probe(timeout_s=35)
                (out/(stage+"_scan.json")).write_text(
                    json.dumps(scan,indent=2,sort_keys=True)+"\n")
                # Keep FIRST source-stamp-matched receive violation even
                # though no D05 stage is appended before this fail-closed gate.
                first_scan=scan.get("first_rx_gap_over_500ms")
                if isinstance(first_scan,dict):
                    v.setdefault("first_scan_timing_boundary",
                        {**first_scan,"stage":stage,
                         "source":"D05_ACTUAL_ROS_SCAN_RECEIVER"})
                    print("D08_LIVE_D05_FIRST_SCAN_RX_GAP "+
                          json.dumps(v["first_scan_timing_boundary"],
                                     sort_keys=True),flush=True)
                if (scan.get("scan_count",0)<20 or
                    scan.get("wall_gap_max_sec",999)>=.5 or
                    scan.get("no_synthetic_scan") is not True):
                    raise RuntimeError("D08_PERSON_"+stage.upper()+
                                       "_ACTUAL_SCAN_CADENCE_NOT_VERIFIED")
                front=scan["front_m"]
                band=(.70,.90) if stage=="farther" else (.14,.4)
                if not band[0] <= front < band[1]:
                    raise RuntimeError("D08_PERSON_"+stage.upper()+
                                       "_NATIVE_SCAN_FRONT_GEOMETRY_MISMATCH")
            resultfile=out/(stage+"_live_d05.json")
            rc=measure_live(resultfile,registration_sha=robot_hash,
                            expected=expected,source_sha=source_sha,
                            timeout_s=55.,min_settle_s=1.)
            measured=json.loads(resultfile.read_text())
            v["stages"].append({
                "stage":stage,"native_ack":ack,
                "actual_world_xyz":list(world_xyz),
                "scan_front_m":scan["front_m"] if scan else None,
                "roi_status":measured["status"],
                "distance_m":measured.get("distance_m"),
                "reason":measured.get("reason"),
                "actual_roi_bbox_height_px":(
                    measured.get("actual_roi_source") or {}).get("bbox_height_px"),
                "actual_roi_frame_sha256":(
                    measured.get("actual_roi_source") or {}).get("actual_rgb_frame_sha256"),
                "registration_confirmed":measured.get(
                    "registered_rgbd_from_actual_sensor") is True,
                "actual_yolo_detection_arrays":measured.get(
                    "actual_yolo_detection_arrays",0),
                "source_stamps_ns":{
                    "rgb":measured.get("last_rgb_stamp_ns"),
                    "depth":measured.get("last_depth_stamp_ns"),
                    "detection":measured.get("last_detection_stamp_ns")},
                "input_age_s":{
                    "rgb":measured.get("last_rgb_receive_age_s"),
                    "depth":measured.get("last_depth_receive_age_s"),
                    "detection":measured.get("last_detection_receive_age_s")}})
            if rc!=0:
                raise RuntimeError("D08_LIVE_D05_"+stage.upper()+"_FIRST_BOUNDARY:"+
                                   str(measured.get("first_boundary",
                                       measured.get("reason"))))
        v.update(grade_actual_person_stages(v["stages"]))
        print("D08_LIVE_D05_TWO_VALID_ONE_UNKNOWN_L2_PASS "+
              json.dumps({"distance_far":v["valid_distance_far_m"],
                "distance_stop":v["valid_distance_stop_m"],
                "delta":v["valid_distance_delta_m"],
                "unknown":v["unknown_reason"]}),flush=True)
    except Exception as exc:
        v["first_boundary"]=type(exc).__name__+":"+str(exc)[:300]
        print("D08_LIVE_D05_TWO_VALID_ONE_UNKNOWN_L2_HOLD "+
              v["first_boundary"],flush=True)
    finally:
        if moved:
            try:
                pose("final_restore",RESTORE)
                v["actual_human_restored_far"]=True
            except Exception as exc:
                v["actual_human_restored_far"]=False
                v["restore_first_boundary"]=str(exc)[:220]
                v["status"]="HOLD"
        (out/"verdict.json").write_text(json.dumps(v,indent=2,sort_keys=True)+"\n")
        hashes=[]
        for evidence in sorted(out.rglob("*")):
            if evidence.is_file() and evidence.name!="SHA256SUMS":
                hashes.append(hashlib.sha256(evidence.read_bytes()).hexdigest()+
                              "  "+evidence.relative_to(out).as_posix())
        (out/"SHA256SUMS").write_text("\n".join(hashes)+"\n")
    return 0 if v["status"]=="D08_REAL_LIVE_PERSON_RANGE_2VALID_UNKNOWN_L2_PASS_NO_GOAL" else 2
