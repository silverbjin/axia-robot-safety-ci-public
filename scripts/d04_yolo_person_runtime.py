#!/usr/bin/env python3
"""G-D04-2: actual Gazebo Waffle Pi RGB -> yolo_ros ONNX -> person bbox/score.

Reuses G-D04-1Pi preflight runner; no P1, Goal, fault, controller, or /cmd_vel.
Fails if any actual person, image, or annotated debug image is missing.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

from d04_bbox_motion_gate import motion_evidence

from d04_waffle_pi_rgb_preflight import (
    DOMAIN_ID, EXPECTED_IMAGE_TOPIC, EXPECTED_INFO_TOPIC,
    _start, _stop_all, official_camera_contract, simple_world,
    sync_ros_discovery_environment, valid_rgb
)

PINNED_YOLO_SHA = "94d2dd500cb26027ee9c019f4d3a02029ac615cc"
PINNED_ONNX_SHA256 = "4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf"
GZ_ACTOR_SOURCE = "https://fuel.gazebosim.org/1.0/Mingfei/models/actor/tip/files/meshes/walk.dae"


def world_with_human(actor_mesh: Path) -> str:
    """Static-position, non-colliding real Gazebo actor; not a synthetic bbox."""
    world = simple_world()
    actor = f"""
<plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
<actor name="human_actor">
  <skin><filename>{actor_mesh.resolve()}</filename><scale>1.0</scale></skin>
  <animation name="walk"><filename>{actor_mesh.resolve()}</filename>
    <interpolate_x>true</interpolate_x></animation>
  <script><loop>true</loop><delay_start>0</delay_start><auto_start>true</auto_start>
    <trajectory id="0" type="walk">
      <waypoint><time>0</time><pose>2.8 0 1.0 0 0 3.14159</pose></waypoint>
      <waypoint><time>20</time><pose>2.8 0 1.0 0 0 3.14159</pose></waypoint>
    </trajectory>
  </script>
</actor>
"""
    if "</world></sdf>" not in world:
        raise ValueError("Unexpected upstream Waffle Pi world format")
    world = world.replace("</world></sdf>", actor + "</world></sdf>")
    ET.fromstring(world)
    return world


def model_yaml(model_path: Path) -> str:
    """Pinned yolo_ros 5.0.0 pipeline, no 3D, tracking, or motor output."""
    model = str(model_path.resolve())
    if not model.endswith(".onnx"):
        raise ValueError("Only offline ONNX path accepted")
    return f"""/yolo/yolo_node:
  ros__parameters:
    use_sim_time: true
    plugins: ["detection", "debug"]
    cameras: ["cam0"]
    cam0:
      rgb_topic: /camera/image_raw
      image_reliability: 2
    detection:
      plugin: yolo_ros/DetectionPlugin
      cameras: ["cam0"]
      model_path: "{model}"
      model_repo: ""
      model_filename: ""
      model_type: auto
      provider: cpu
      threshold: 0.15
      iou: 0.45
      n_threads: 2
      max_fps: 5
    debug:
      plugin: yolo_ros/DebugPlugin
      cameras: ["cam0"]
"""


def valid_person(box: dict, width: int = 640, height: int = 480) -> bool:
    """Strictly require a real yolo_msgs person with finite score/bbox."""
    import math
    return bool(
        box.get("class_name", "").lower() == "person"
        and box.get("class_id") == 0
        and isinstance(box.get("score"), float)
        and math.isfinite(box["score"])
        and 0.0 < box["score"] <= 1.0
        and 0.0 < box.get("size_x", 0) <= width
        and 0.0 < box.get("size_y", 0) <= height
        and 0.0 <= box.get("center_x", -1) <= width
        and 0.0 <= box.get("center_y", -1) <= height
        and box.get("stamp_ns", 0) > 0
    )


def _watch_detections_and_images(out: Path, duration_s: int = 95, *, require_motion: bool = False) -> dict:
    """Actual ROS 2 subscriptions, never publishes data or synthetic detections."""
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image
    from yolo_msgs.msg import DetectionArray

    rclpy.init(args=None)
    node = rclpy.create_node("axia_d04_person_readonly_verifier")
    seen = {"camera_frames": 0, "detection_frames": 0, "debug_frames": 0,
            "person": None, "first_image": None,
            "non_person_detections": 0, "debug_saved": False,
            "person_samples": []}
    saved = {"camera": False, "debug": False}

    def image_cb(msg, which):
        seen["camera_frames" if which == "camera" else "debug_frames"] += 1
        if which == "camera" and seen["first_image"] is None:
            seen["first_image"] = {
                "width": msg.width, "height": msg.height,
                "encoding": msg.encoding, "stamp_ns": msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec,
                "payload_size": len(msg.data), "frame_id": msg.header.frame_id,
                "payload_sha256": hashlib.sha256(msg.data).hexdigest()}
        if saved[which] or msg.width != 640 or msg.height != 480:
            return
        if msg.encoding.lower() not in ("rgb8", "bgr8") or len(msg.data) < 640*480*3:
            return
        try:
            import cv2
            import numpy as np
            a = np.frombuffer(msg.data, np.uint8).reshape((msg.height, msg.step))[:, :msg.width*3].reshape((msg.height,msg.width,3))
            if msg.encoding.lower() == "rgb8":
                a = cv2.cvtColor(a, cv2.COLOR_RGB2BGR)
            saved[which] = bool(cv2.imwrite(str(out / (which + "_frame.png")), a))
            if which == "debug":
                seen["debug_saved"] = saved[which]
        except Exception as exc:
            seen[which + "_save_error"] = str(exc)[:160]

    def detection_cb(msg):
        seen["detection_frames"] += 1
        stamp = msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec
        for d in msg.detections:
            b = {
                "class_id": int(d.class_id), "class_name": str(d.class_name),
                "score": float(d.score), "stamp_ns": stamp,
                "center_x": float(d.bbox.center.position.x),
                "center_y": float(d.bbox.center.position.y),
                "size_x": float(d.bbox.size.x), "size_y": float(d.bbox.size.y)}
            if valid_person(b):
                if len(seen["person_samples"]) < 250:
                    seen["person_samples"].append(b)
                if seen["person"] is None or b["score"] > seen["person"]["score"]:
                    seen["person"] = b
            elif b["class_name"] != "person":
                seen["non_person_detections"] += 1

    node.create_subscription(Image, EXPECTED_IMAGE_TOPIC, lambda m: image_cb(m,"camera"), qos_profile_sensor_data)
    node.create_subscription(Image, "/yolo/cam0/debug_image",lambda m: image_cb(m,"debug"), qos_profile_sensor_data)
    node.create_subscription(DetectionArray, "/yolo/cam0/detections", detection_cb, qos_profile_sensor_data)

    try:
        deadline = time.monotonic() + duration_s
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.5)
            basic_ready = (seen["person"] is not None and
                           seen["debug_frames"] >= 1 and
                           seen["camera_frames"] >= 1)
            if basic_ready and (not require_motion or
                                motion_evidence(seen["person_samples"])["passed"]):
                break
    finally:
        node.destroy_node()
        rclpy.shutdown()
    seen["motion_evidence"] = motion_evidence(seen["person_samples"])
    (out/"person_samples.json").write_text(
        json.dumps({"samples":seen["person_samples"],
                    "motion_evidence":seen["motion_evidence"]},
                   ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return seen


def main() -> int:
    out = Path("results/d04-yolo-person")
    out.mkdir(parents=True, exist_ok=True)
    verdict = {
        "gate": "G-D04-2", "status": "BLOCKED_OR_INCONCLUSIVE",
        "source_head_sha": os.environ.get("AXIA_TESTED_HEAD_SHA", "UNPINNED"),
        "yolo_source_sha": PINNED_YOLO_SHA,
        "actor_source": GZ_ACTOR_SOURCE,
        "model_license": "AGPL-3.0 (ephemeral evaluation only; not distributed)",
        "p1_executed": False, "goal_sent": False,
        "fault_injected": False, "cmd_vel_published": False,
        "certified_estop_tested": False
    }
    processes = []
    env = os.environ.copy()
    env["ROS_DOMAIN_ID"] = str(DOMAIN_ID)
    env["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
    env["GZ_PARTITION"] = "axia_yolo_person_" + env.get("GITHUB_RUN_ID","manual")
    env["GZ_SIM_RESOURCE_PATH"] = str(Path(os.environ["TURTLEBOT3_GAZEBO_SHARE"])/"models")
    env["TURTLEBOT3_MODEL"] = "waffle_pi"
    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    env["GALLIUM_DRIVER"] = "llvmpipe"
    env.pop("EGL_PLATFORM",None)
    sync_ros_discovery_environment(env)
    try:
        asset = Path(os.environ["AXIA_ACTOR_DAE"])
        model = Path(os.environ["AXIA_ONNX_PATH"])
        if not asset.is_file() or not model.is_file():
            raise FileNotFoundError("Actor DAE or licensed ephemeral ONNX not present")
        model_hash = hashlib.sha256(model.read_bytes()).hexdigest()
        verdict["model_sha256"] = model_hash
        if model_hash != PINNED_ONNX_SHA256:
            raise ValueError("Unpinned model SHA256; refusing evaluation")
        verdict["actor_sha256"] = hashlib.sha256(asset.read_bytes()).hexdigest()
        share = Path(os.environ["TURTLEBOT3_GAZEBO_SHARE"])
        verdict["official_camera"] = official_camera_contract(share/"models/turtlebot3_waffle_pi/model.sdf")
        world = out/"waffle_pi_person.sdf"
        world.write_text(world_with_human(asset),encoding="utf-8")
        params = out/"yolo_rgb_only.yaml"
        params.write_text(model_yaml(model),encoding="utf-8")
        verdict["world_sha256"] = hashlib.sha256(world.read_bytes()).hexdigest()
        _start("gazebo_server",["xvfb-run","-a","-s","-screen 0 1280x720x24",
             "gz","sim","-r","-s","-v3",str(world.resolve())],env,out,processes)
        _start("image_bridge",["ros2","run","ros_gz_image","image_bridge",EXPECTED_IMAGE_TOPIC],env,out,processes)
        _start("clock_bridge",["ros2","run","ros_gz_bridge","parameter_bridge",
                "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],env,out,processes)
        _start("yolo",["ros2","launch","yolo_bringup","yolo.launch.py",
                        "params_file:="+str(params.resolve())],env,out,processes)
        verdict["ros_evidence"] = _watch_detections_and_images(out, duration_s=95)
        rgb = verdict["ros_evidence"]["first_image"]
        person = verdict["ros_evidence"]["person"]
        debug = verdict["ros_evidence"]["debug_saved"]
        if rgb is None:
            verdict["blocker"]="NO_ACTUAL_GAZEBO_RGB"
        elif not valid_rgb(rgb):
            verdict["blocker"]="INVALID_RGB"
        elif not person:
            verdict["blocker"]="NO_REAL_PERSON_DETECTION"
        elif not debug:
            verdict["blocker"]="NO_ACTUAL_DEBUG_BOUNDING_BOX_IMAGE"
        else:
            verdict["status"]="PASS_REAL_GAZEBO_PERSON_BBOX_CONFIDENCE"
        listing = subprocess.run(["gz","topic","-l"],env=env,capture_output=True,text=True,timeout=12,check=False)
        (out/"gazebo_topics.txt").write_text(listing.stdout+"\n"+listing.stderr,encoding="utf-8")
        verdict["actor_present_in_world"] = "human_actor" in world.read_text()
    except Exception as exc:
        verdict["blocker"]=f"{type(exc).__name__}:{str(exc)[:350]}"
    finally:
        _stop_all(processes,verdict)
        (out/"verdict.json").write_text(json.dumps(verdict,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        files=sorted(x for x in out.iterdir() if x.is_file() and x.name!="SHA256SUMS")
        (out/"SHA256SUMS").write_text("".join(hashlib.sha256(x.read_bytes()).hexdigest()+"  "+x.name+"\n" for x in files),encoding="utf-8")
        print(json.dumps({k:verdict.get(k) for k in ("gate","status","blocker","ros_evidence","source_head_sha")},ensure_ascii=False))
    return 0 if verdict["status"]=="PASS_REAL_GAZEBO_PERSON_BBOX_CONFIDENCE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
