#!/usr/bin/env python3
"""ROS read-only observation of REAL G07. Publishes RViz markers only.

The ring overlay is not Nav2 CollisionMonitorState/physical safety evidence.
The unchanged private G07 Owner runner exclusively attests safety and Goal.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import time

STOP_M, SLOW_M, OBS_AGE_S = 0.40, 0.75, 0.50

def front_distance(scan):
    """Front range teaching annotation, NOT official CM polygon+min_points."""
    a = [
        float(v) for i, v in enumerate(scan.ranges)
        if abs(float(scan.angle_min) + i * float(scan.angle_increment)) <= 0.18
        and math.isfinite(v) and scan.range_min <= v <= scan.range_max
    ]
    return min(a) if a else None

def annotated_zone(front_m, age_s):
    if (front_m is None or age_s is None or not math.isfinite(age_s)
            or age_s < 0 or age_s > OBS_AGE_S
            or not math.isfinite(front_m) or front_m <= 0):
        return "UNKNOWN"
    if front_m <= STOP_M:
        return "STOP"
    if front_m <= SLOW_M:
        return "SLOWDOWN"
    return "CLEAR"

def run(out: Path):
    # ROS is imported ONLY at runtime. CI L0 imports pure helpers without ROS.
    import rclpy
    from rclpy.node import Node
    from rclpy.parameter import Parameter
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan
    from nav_msgs.msg import Odometry
    from geometry_msgs.msg import Twist, Point
    from visualization_msgs.msg import MarkerArray, Marker

    out.mkdir(parents=True, exist_ok=True)
    rclpy.init()
    node = Node("axia_d06_gazebo_readonly_monitor", parameter_overrides=[
        Parameter("use_sim_time", Parameter.Type.BOOL, True)])
    state = {"front": None, "last_scan": None, "scan_count": 0,
             "odom_vx": None, "supervised_vx": None,
             "cm_vx": None, "final_vx": None, "cm_action_event": None}
    first_scan_gap = None

    def scan_cb(msg):
        nonlocal first_scan_gap
        now = time.monotonic()
        previous = state["last_scan"]
        if previous is not None and now - previous > 0.30 and first_scan_gap is None:
            first_scan_gap = {"gap_sec": round(now - previous, 5),
                              "after_scan_count": state["scan_count"]}
        state["front"] = front_distance(msg)
        state["last_scan"] = now
        state["scan_count"] += 1

    node.create_subscription(LaserScan, "/scan", scan_cb, qos_profile_sensor_data)
    node.create_subscription(Odometry, "/odom",
        lambda msg: state.__setitem__("odom_vx", float(msg.twist.twist.linear.x)),
        qos_profile_sensor_data)
    for key, topic in (
        ("supervised_vx", "/cmd_vel_supervised"),
        ("cm_vx", "/cmd_vel_pre_guard"),
        ("final_vx", "/cmd_vel"),
    ):
        node.create_subscription(Twist, topic,
            lambda msg, k=key: state.__setitem__(k, float(msg.linear.x)),
            qos_profile_sensor_data)
    # CollisionMonitorState may be a state TRANSITION event, not periodic.
    try:
        from nav2_msgs.msg import CollisionMonitorState
        node.create_subscription(CollisionMonitorState, "/collision_monitor_state",
          lambda msg: state.__setitem__("cm_action_event", int(msg.action_type)), 10)
    except (ImportError, AttributeError):
        pass

    # The ONLY publisher; it is display data, not a robot command.
    pub = node.create_publisher(MarkerArray, "/axia/d06/rviz/bubble", 5)

    def ring(r, id_, color):
        m = Marker()
        m.header.frame_id = "base_footprint"
        m.header.stamp = node.get_clock().now().to_msg()
        m.ns = "D06_EDUCATIONAL_RING_NOT_OFFICIAL_CM"
        m.id, m.type, m.action = id_, Marker.LINE_STRIP, Marker.ADD
        m.pose.orientation.w = 1.0
        m.scale.x = 0.025
        m.color.r, m.color.g, m.color.b, m.color.a = color
        for i in range(73):
            ang = 2 * math.pi * i / 72
            m.points.append(Point(x=r*math.cos(ang), y=r*math.sin(ang), z=0.06))
        m.lifetime.sec = 2
        return m

    def label(zone):
        m = Marker()
        m.header.frame_id = "base_footprint"
        m.header.stamp = node.get_clock().now().to_msg()
        m.ns = "D06_EDU_LABEL_NOT_CM_VERDICT"
        m.id, m.type, m.action = 3, Marker.TEXT_VIEW_FACING, Marker.ADD
        m.pose.orientation.w = 1.0
        m.pose.position.z = 0.65
        m.scale.z = 0.13
        m.color.r = m.color.g = m.color.b = m.color.a = 1.0
        m.text = f"D06 /scan annotation: {zone} (NOT CM verdict)"
        m.lifetime.sec = 2
        return m

    latest = None
    next_emit = 0.0
    print("D06_READONLY_MONITOR_STARTED EVIDENCE_ONLY_NOT_CM_VERDICT", flush=True)
    with (out / "readonly_samples.jsonl").open("x", encoding="utf-8", buffering=1) as log:
        try:
            while rclpy.ok():
                rclpy.spin_once(node, timeout_sec=0.10)
                now = time.monotonic()
                if now < next_emit:
                    continue
                next_emit = now + 1.00  # <=1 Hz read-only visualization; safety TTL unchanged
                age = None if state["last_scan"] is None else now - state["last_scan"]
                zone = annotated_zone(state["front"], age)
                pub.publish(MarkerArray(markers=[
                    ring(SLOW_M, 1, (0.95, 0.7, 0.2, 0.8)),
                    ring(STOP_M, 2, (0.95, 0.22, 0.15, 0.95)), label(zone)]))
                entry = {
                    "t_monotonic": round(now, 5),
                    "actual_scan_messages": state["scan_count"],
                    "front_m": state["front"],
                    "scan_age_s": round(age, 4) if age is not None else None,
                    "annotated_zone_NOT_CM_VERDICT": zone,
                    "cm_action_last_event": state["cm_action_event"],
                    "supervised_vx_mps": state["supervised_vx"],
                    "cm_vx_mps": state["cm_vx"],
                    "final_vx_mps": state["final_vx"],
                    "odom_vx_mps": state["odom_vx"],
                    "first_readonly_scan_gap_over_0p3_s": first_scan_gap,
                    "gazebo_attested_by_this_node": False,
                    "safety_cm_attested_by_this_node": False,
                    "certified_estop": False,
                }
                log.write(json.dumps(entry, ensure_ascii=False, allow_nan=False) + "\n")
                if zone != latest:
                    latest = zone
                    print("D06_EDU_OBSERVATION_ZONE " + json.dumps({
                        "zone": zone, "front_m": state["front"],
                        "cm_vx": state["cm_vx"], "odom_vx": state["odom_vx"],
                        "evidence_only": True}, ensure_ascii=False), flush=True)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()
    print("D06_READONLY_MONITOR_STOPPED", flush=True)
    return 0

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    raise SystemExit(run(args.out))
