#!/usr/bin/env python3
"""G-D04-1Pi: official ROBOTIS Jazzy Waffle Pi RGB read-only Gazebo probe.

Use official installed turtlebot3_waffle_pi/model.sdf unchanged.
Only image and CameraInfo bridges; no Nav2, goals, faults, /cmd_vel publisher.
A PASS here does NOT prove yolo_ros, AXIA P1, or a person is recognized.
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


EXPECTED_IMAGE_TOPIC = "/camera/image_raw"
EXPECTED_INFO_TOPIC = "/camera/camera_info"
DOMAIN_ID = 40   # Preserve AXIA P1 safe-domain policy: avoid Linux ephemeral UDP.


def official_camera_contract(model_path: Path) -> dict:
    root = ET.parse(model_path).getroot()
    cameras = root.findall(".//sensor[@type='camera']")
    if len(cameras) != 1:
        raise ValueError(f"Expected one official Waffle Pi RGB camera, got {len(cameras)}")
    camera = cameras[0]
    get = lambda selector: camera.findtext(selector, default="")
    contract = {
        "sensor": camera.get("name"),
        "type": camera.get("type"),
        "topic": get("topic"),
        "info_topic": get("camera/camera_info_topic"),
        "frame_id": get("gz_frame_id"),
        "width": int(get("camera/image/width")),
        "height": int(get("camera/image/height")),
        "format": get("camera/image/format"),
        "update_rate": float(get("update_rate")),
    }
    if contract["topic"] != "camera/image_raw" or contract["info_topic"] != "camera/camera_info":
        raise ValueError("Official camera topics differ from pinned D04 ROS contract")
    if contract["width"] != 640 or contract["height"] != 480 or contract["format"] != "R8G8B8":
        raise ValueError("Official camera image contract changed; inspect before continuing")
    return contract


def valid_rgb(image: dict | None) -> bool:
    return bool(
        image
        and image["width"] == 640 and image["height"] == 480
        and image["encoding"].lower() in ("rgb8", "bgr8")
        and image["payload_size"] >= 640 * 480 * 3
        and image["stamp_ns"] > 0
        and image["frame_id"]
    )


def valid_camera_info(info: dict | None) -> bool:
    return bool(info and info["width"] == 640 and info["height"] == 480
                and info["stamp_ns"] > 0 and info["frame_id"])


def simple_world() -> str:
    # A local dependency-free world: no external Gazebo Fuel models to fetch.
    # The robot itself is the *official, unmodified* ROBOTIS model:// reference.
    return """<?xml version="1.0"?>
<sdf version="1.8"><world name="default">
<plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
<plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
  <render_engine>ogre2</render_engine>
</plugin>
<light name="key_light" type="directional"><pose>0 0 5 0 0 0</pose>
<diffuse>0.85 0.85 0.85 1</diffuse><specular>0.15 0.15 0.15 1</specular>
<attenuation><range>20</range><constant>1</constant><linear>0</linear><quadratic>0</quadratic></attenuation>
<direction>-0.3 0.1 -1</direction></light>
<model name="ground"><static>true</static><link name="floor">
<collision name="floor_c"><geometry><plane><normal>0 0 1</normal><size>20 20</size></plane></geometry></collision>
<visual name="floor_v"><geometry><plane><normal>0 0 1</normal><size>20 20</size></plane></geometry></visual>
</link></model>
<include><uri>model://turtlebot3_waffle_pi</uri><name>turtlebot3_waffle_pi</name>
<pose>0 0 0.05 0 0 0</pose></include>
</world></sdf>
"""


def _read_ros_frames(image_topic: str, info_topic: str, timeout_s: float) -> tuple[dict | None, dict | None]:
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image, CameraInfo
    rclpy.init(args=None)
    node = rclpy.create_node("axia_d04_pi_camera_readonly")
    images: list[dict] = []
    infos: list[dict] = []

    def image_cb(msg):
        if images:
            return
        images.append({
            "width": msg.width, "height": msg.height,
            "encoding": msg.encoding, "frame_id": msg.header.frame_id,
            "stamp_ns": msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec,
            "payload_size": len(msg.data),
            "payload_sha256": hashlib.sha256(msg.data).hexdigest(),
        })

    def info_cb(msg):
        if infos:
            return
        infos.append({
            "width": msg.width, "height": msg.height,
            "frame_id": msg.header.frame_id,
            "stamp_ns": msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec,
            "focal_x": float(msg.k[0]), "focal_y": float(msg.k[4]),
        })

    node.create_subscription(Image, image_topic, image_cb, qos_profile_sensor_data)
    node.create_subscription(CameraInfo, info_topic, info_cb, qos_profile_sensor_data)
    try:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline and not (images and infos):
            rclpy.spin_once(node, timeout_sec=0.5)
        return (images[0] if images else None, infos[0] if infos else None)
    finally:
        node.destroy_node()
        rclpy.shutdown()


def _start(label: str, argv: list[str], env: dict, out: Path, processes: list):
    logfile = (out / f"{label}.log").open("w", encoding="utf-8")
    try:
        proc = subprocess.Popen(argv, stdout=logfile, stderr=subprocess.STDOUT,
                                env=env, start_new_session=True)
    finally:
        logfile.close()
    processes.append((label, proc))
    return proc


def _stop_all(processes: list, evidence: dict):
    for label, proc in reversed(processes):
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGINT)
            try:
                proc.wait(timeout=18)
            except subprocess.TimeoutExpired:
                evidence.setdefault("shutdown_escalated", []).append(label)
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=8)
        evidence.setdefault("process_exit", {})[label] = proc.returncode


def _probe():
    out = Path("results/d04-waffle-pi-rgb")
    out.mkdir(parents=True, exist_ok=True)
    verdict = {
        "gate": "G-D04-1Pi",
        "status": "BLOCKED_OR_INCONCLUSIVE",
        "source_head_sha": os.environ.get("AXIA_TESTED_HEAD_SHA", "UNVERIFIED"),
        "official_model": "turtlebot3_waffle_pi",
        "human_added": False, "yolo_executed": False, "p1_executed": False,
        "goal_sent": False, "fault_injected": False,
        "command_published": False, "p1_acceptance": False,
    }
    processes = []
    env = os.environ.copy()
    env["ROS_DOMAIN_ID"] = str(DOMAIN_ID)
    env["GZ_PARTITION"] = "axia_d04_pi_" + os.environ.get("GITHUB_RUN_ID", "manual")
    env["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
    env["TURTLEBOT3_MODEL"] = "waffle_pi"
    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    env.pop("EGL_PLATFORM", None)
    env["GALLIUM_DRIVER"] = "llvmpipe"

    try:
        import ament_index_python.packages
        share = Path(ament_index_python.packages.get_package_share_directory("turtlebot3_gazebo"))
        model = share / "models/turtlebot3_waffle_pi/model.sdf"
        if not model.is_file():
            raise FileNotFoundError(model)
        verdict["package_share"] = str(share)
        verdict["model_sha256"] = hashlib.sha256(model.read_bytes()).hexdigest()
        verdict["source_camera"] = official_camera_contract(model)
        env["GZ_SIM_RESOURCE_PATH"] = str(share / "models") + ":" + env.get("GZ_SIM_RESOURCE_PATH", "")
        world = out / "waffle_pi_rgb_probe.sdf"
        world.write_text(simple_world(), encoding="utf-8")
        verdict["world_sha256"] = hashlib.sha256(world.read_bytes()).hexdigest()
        sim = _start("gazebo_server",
                     ["xvfb-run", "-a", "-s", "-screen 0 1280x720x24",
                      "gz", "sim", "-r", "-s", "-v3", str(world.resolve())],
                     env, out, processes)
        image_bridge = _start("image_bridge",
                              ["ros2", "run", "ros_gz_image", "image_bridge", EXPECTED_IMAGE_TOPIC],
                              env, out, processes)
        info_bridge = _start("info_bridge",
                             ["ros2", "run", "ros_gz_bridge", "parameter_bridge",
                              EXPECTED_INFO_TOPIC + "@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo"],
                             env, out, processes)
        # A short startup guard distinguishes a prematurely dead renderer from a late topic.
        time.sleep(7)
        if sim.poll() is not None:
            verdict["blocker"] = "GAZEBO_SERVER_EXITED_BEFORE_RGB_FRAME"
        elif image_bridge.poll() is not None:
            verdict["blocker"] = "IMAGE_BRIDGE_EXITED_BEFORE_RGB_FRAME"
        elif info_bridge.poll() is not None:
            verdict["blocker"] = "CAMERA_INFO_BRIDGE_EXITED_BEFORE_FRAME"
        else:
            rgb, info = _read_ros_frames(EXPECTED_IMAGE_TOPIC, EXPECTED_INFO_TOPIC, timeout_s=100)
            verdict["ros_image"] = rgb
            verdict["ros_camera_info"] = info
            if valid_rgb(rgb) and valid_camera_info(info):
                verdict["status"] = "PASS_RGB_FRAME_AND_CAMERA_INFO"
            else:
                verdict["blocker"] = ("NO_RGB_FRAME" if rgb is None else
                                      "INVALID_RGB_FRAME" if not valid_rgb(rgb) else
                                      "NO_VALID_CAMERA_INFO")
        # Distinguish an advertised Gazebo transport topic from actual sensor data.
        raw_info = subprocess.run(["gz", "topic", "-i", "-t", EXPECTED_IMAGE_TOPIC],
                                   env=env, capture_output=True, text=True,
                                   timeout=10, check=False)
        (out / "gz_image_topic_info.txt").write_text(raw_info.stdout + "\n" + raw_info.stderr,
                                                      encoding="utf-8")
        verdict["gz_image_topic_info_exit"] = raw_info.returncode
        listing = subprocess.run(["gz", "topic", "-l"], env=env,
                                  capture_output=True, text=True, timeout=12, check=False)
        (out / "gz_topics.txt").write_text(listing.stdout + "\n" + listing.stderr, encoding="utf-8")
        verdict["gazebo_topics"] = [line.strip() for line in listing.stdout.splitlines()
                                     if "camera" in line.lower() or "image" in line.lower()]
        verdict["gz_topic_list_exit"] = listing.returncode
    except Exception as exc:
        verdict["blocker"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    finally:
        _stop_all(processes, verdict)
        (out / "verdict.json").write_text(json.dumps(verdict, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
        files = sorted(f for f in out.iterdir() if f.is_file() and f.name != "SHA256SUMS")
        (out / "SHA256SUMS").write_text("".join(
            hashlib.sha256(f.read_bytes()).hexdigest() + "  " + f.name + "\n"
            for f in files), encoding="utf-8")
        print(json.dumps({k: verdict.get(k) for k in
              ("gate","status","blocker","source_camera","ros_image",
               "ros_camera_info","gazebo_topics","source_head_sha")},ensure_ascii=False))
    return 0 if verdict["status"] == "PASS_RGB_FRAME_AND_CAMERA_INFO" else 2


if __name__ == "__main__":
    raise SystemExit(_probe())
