#!/usr/bin/env python3
"""D04 pre-development: read-only OFFICIAL Waffle RGB frame discovery.

No AXIA P1 or person entity is launched. Not a YOLO, P1, or S02 acceptance.
Never publishes /cmd_vel, sends goals, or injects faults.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time


def choose_rgb_topic(topic_listing: str) -> str | None:
    """Prefer a Gazebo camera /image topic, excluding depth/points/info."""
    candidates = []
    for line in topic_listing.splitlines():
        name = line.strip()
        low = name.lower()
        if not name.startswith("/") or not re.search(r"(image|rgb)", low):
            continue
        if any(x in low for x in ("depth", "info", "points", "compressed")):
            continue
        candidates.append(name)
    return sorted(candidates, key=lambda x: (not x.endswith("/image"), len(x), x))[0] if candidates else None


def image_is_valid(width: int, height: int, encoding: str, data_bytes: int) -> bool:
    return width > 0 and height > 0 and data_bytes > 0 and bool(encoding)


def _run(args, *, env, timeout=12):
    return subprocess.run(args, env=env, capture_output=True, text=True,
                          timeout=timeout, check=False)


def _stop(proc, record):
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGINT)
        proc.wait(timeout=22)
    except subprocess.TimeoutExpired:
        record["shutdown_escalated"] = True
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=8)


def _wait_ros_image(topic, *, seconds=40):
    import rclpy
    from sensor_msgs.msg import Image
    from rclpy.qos import qos_profile_sensor_data

    rclpy.init()
    node = rclpy.create_node("d04_rgb_readonly_subscriber")
    frames = []
    def cb(message):
        frames.append({
            "width": message.width, "height": message.height,
            "encoding": message.encoding, "bytes": len(message.data),
            "frame_id": message.header.frame_id,
            "stamp_sec": message.header.stamp.sec,
            "stamp_nanosec": message.header.stamp.nanosec,
        })
    node.create_subscription(Image, topic, cb, qos_profile_sensor_data)
    try:
        until = time.monotonic() + seconds
        while time.monotonic() < until and not frames:
            rclpy.spin_once(node, timeout_sec=0.5)
        return frames[0] if frames else None
    finally:
        node.destroy_node()
        rclpy.shutdown()


def main():
    out = Path("results/d04-readonly-camera")
    out.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["ROS_DOMAIN_ID"] = "174"
    env["GZ_PARTITION"] = "axia_d04_rgb_" + env.get("GITHUB_RUN_ID", "local")
    env["TURTLEBOT3_MODEL"] = "waffle"
    env["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
    record = {
        "gate": "G-D04-1_RGB_SUBGATE",
        "kind": "official_waffle_no_goal_camera_probe",
        "source_commit": env.get("GITHUB_SHA", "NOT_PINNED"),
        "p1_included": False,
        "person_entity_verified": False,
        "yolo_inference_verified": False,
        "goal_sent": False,
        "fault_injected": False,
        "cmd_vel_published_by_probe": False,
        "status": "INCONCLUSIVE",
    }
    launch = None
    bridge = None
    try:
        cmd = [
            "ros2", "launch", "nav2_bringup", "tb3_simulation_launch.py",
            "headless:=True", "use_rviz:=False",
            "use_composition:=False", "use_respawn:=False",
        ]
        record["launch_command"] = cmd
        with (out / "sim_stdout.log").open("w", encoding="utf-8") as stream:
            launch = subprocess.Popen(cmd, env=env, stdout=stream,
                                      stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + 135
            listing = ""
            while time.monotonic() < deadline:
                if launch.poll() is not None:
                    record["blocker"] = "SIM_LAUNCH_EXITED"
                    break
                p = _run(["gz", "topic", "-l"], env=env)
                if p.returncode == 0:
                    listing = p.stdout
                    topic = choose_rgb_topic(listing)
                    if topic:
                        break
                time.sleep(4)
            (out / "gz_topics.txt").write_text(listing, encoding="utf-8")
            topic = choose_rgb_topic(listing)
            record["gazebo_rgb_topic"] = topic
            if topic:
                info = _run(["gz", "topic", "-i", "-t", topic], env=env)
                record["gazebo_topic_info"] = (info.stdout + info.stderr)[:1800]
                with (out / "bridge_stdout.log").open("w", encoding="utf-8") as blog:
                    bridge = subprocess.Popen(
                        ["ros2", "run", "ros_gz_bridge", "parameter_bridge",
                         topic + "@sensor_msgs/msg/Image[gz.msgs.Image"],
                        env=env, stdout=blog, stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                    message = _wait_ros_image(topic, seconds=45)
                    record["ros_image_message"] = message
                    if message and image_is_valid(
                        message["width"], message["height"],
                        message["encoding"], message["bytes"]
                    ):
                        record["status"] = "RGB_FRAME_RECEIVED_NO_HUMAN_OR_YOLO_CLAIM"
                    else:
                        record["blocker"] = "RGB_BRIDGE_OR_RENDER_NO_VALID_FRAME"
            else:
                record.setdefault("blocker", "OFFICIAL_WAFFLE_RGB_TOPIC_NOT_VISIBLE")
    except Exception as exc:
        record["blocker"] = type(exc).__name__ + ":" + str(exc)[:300]
    finally:
        _stop(bridge, record)
        _stop(launch, record)
        record["sim_exit_code"] = launch.returncode if launch else None
        record["bridge_exit_code"] = bridge.returncode if bridge else None
        (out / "verdict.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        files = sorted(f for f in out.iterdir() if f.is_file() and f.name != "SHA256SUMS")
        (out / "SHA256SUMS").write_text("".join(
            hashlib.sha256(f.read_bytes()).hexdigest() + "  " + f.name + "\n"
            for f in files
        ), encoding="utf-8")
        print(json.dumps({k: record.get(k) for k in
                          ("gate", "status", "blocker", "gazebo_rgb_topic",
                           "ros_image_message", "source_commit")}, ensure_ascii=False))
    return 0 if record["status"].startswith("RGB_FRAME_RECEIVED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
