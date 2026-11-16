#!/usr/bin/env python3
"""Read-only Terminal B observer for D06 official isolated CM ROS L1.

Discovers transient ROS_DOMAIN_ID from the actual official CM process.
Never publishes, sends goals, changes lifecycle, or runs Gazebo.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import time

TOPIC_ROOT = "/axia/d06/test"


def find_d06_cm(proc_root: Path = Path("/proc"), uid: int | None = None):
    """Return (pid, domain, rmw) for exact running D06 CM processes."""
    if uid is None:
        uid = os.getuid()
    hits = []
    for item in proc_root.iterdir():
        if not item.name.isdigit():
            continue
        try:
            if item.stat().st_uid != uid:
                continue
            args = (item / "cmdline").read_bytes().split(b"\0")
            args = [x.decode("utf-8", "replace") for x in args if x]
            if (not args or Path(args[0]).name != "collision_monitor"
                    or "--params-file" not in args
                    or not any(Path(x).name == "collision_monitor_d06.yaml" for x in args)):
                continue
            environment = {}
            for entry in (item / "environ").read_bytes().split(b"\0"):
                if b"=" in entry:
                    k, v = entry.split(b"=", 1)
                    if k in (b"ROS_DOMAIN_ID", b"RMW_IMPLEMENTATION", b"ROS_AUTOMATIC_DISCOVERY_RANGE"):
                        environment[k.decode()] = v.decode("utf-8", "replace")
            domain = environment.get("ROS_DOMAIN_ID", "")
            if not re.fullmatch(r"\d{1,3}", domain) or not 0 <= int(domain) <= 232:
                continue
            if environment.get("ROS_AUTOMATIC_DISCOVERY_RANGE") != "LOCALHOST":
                continue
            hits.append((int(item.name), domain, environment.get("RMW_IMPLEMENTATION", "")))
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            continue
    return hits


def select_unique(hits):
    if len(hits) > 1:
        raise RuntimeError("D06_MONITOR_BLOCKED_MULTIPLE_CM: ambiguous test processes")
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--wait-sec", type=float, default=180.0)
    ap.add_argument("--max-observe-sec", type=float, default=35.0)
    args = ap.parse_args()
    if args.self_check:
        assert TOPIC_ROOT == "/axia/d06/test"
        assert select_unique([]) is None
        print("D06_L1_TERMINAL_B_STATIC_PASS ROS_NOT_RUN")
        return 0
    if not (1 <= args.wait_sec <= 600 and 1 <= args.max_observe_sec <= 120):
        ap.error("invalid waiting or observation time")

    print("D06_L1_TERMINAL_B_WAIT_FOR_OFFICIAL_CM: start Terminal A now", flush=True)
    deadline = time.monotonic() + args.wait_sec
    found = None
    while time.monotonic() < deadline:
        try:
            found = select_unique(find_d06_cm())
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr, flush=True)
            return 2
        if found:
            break
        time.sleep(0.2)
    if found is None:
        print("D06_L1_TERMINAL_B_NOT_OBSERVED: no official D06 CM process; no ROS verification", flush=True)
        return 2
    pid, domain, rmw = found
    os.environ["ROS_DOMAIN_ID"] = domain
    os.environ["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
    if rmw:
        os.environ["RMW_IMPLEMENTATION"] = rmw
    print(f"D06_L1_TERMINAL_B_ATTACHED pid={pid} ROS_DOMAIN_ID={domain} READ_ONLY=true", flush=True)

    # ROS imports deliberately occur only after the correct domain is selected.
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import Twist
    from sensor_msgs.msg import LaserScan
    from nav2_msgs.msg import CollisionMonitorState
    rclpy.init(args=None)
    node = rclpy.create_node("axia_d06_cm_l1_terminal_b_readonly")
    last = {}
    counts = {"scan": 0, "cmd_in": 0, "cmd_out": 0, "state": 0}

    def report(label, value, interval=0.9):
        now = time.monotonic()
        previous = last.get(label)
        if previous is None or previous[0] != value or now - previous[1] >= interval:
            print(f"[D06 {label}] {value}", flush=True)
            last[label] = (value, now)

    def on_input(msg):
        counts["cmd_in"] += 1
        report("cmd_in", f"linear.x={msg.linear.x:.3f} m/s")

    def on_output(msg):
        counts["cmd_out"] += 1
        report("cmd_out", f"linear.x={msg.linear.x:.3f} m/s")

    def on_scan(msg):
        counts["scan"] += 1
        # Educational front-range summary; NOT official CM zone verdict.
        values = [float(r) for i, r in enumerate(msg.ranges)
                  if abs(msg.angle_min + i * msg.angle_increment) < 0.09
                  and msg.range_min <= float(r) <= msg.range_max]
        report("synthetic_scan", f"front_min={min(values):.2f} m" if values else "front_min=UNKNOWN")

    def on_state(msg):
        counts["state"] += 1
        print(f"[D06 CM state EVENT] action_type={msg.action_type} polygon_name={msg.polygon_name}", flush=True)

    subs = [
        node.create_subscription(Twist, f"{TOPIC_ROOT}/cmd_in", on_input, 10),
        node.create_subscription(Twist, f"{TOPIC_ROOT}/cmd_out", on_output, 10),
        node.create_subscription(LaserScan, f"{TOPIC_ROOT}/scan", on_scan, qos_profile_sensor_data),
        node.create_subscription(CollisionMonitorState, f"{TOPIC_ROOT}/collision_monitor_state", on_state, 10),
    ]
    print("D06_L1_TERMINAL_B_TOPICS: cmd_in cmd_out scan collision_monitor_state", flush=True)
    print("D06_L1_TERMINAL_B_ACTIONS: isolated bench sends NO Nav2 goal; lifecycle is service, not action", flush=True)
    try:
        stop = time.monotonic() + args.max_observe_sec
        graph_reported = False
        while time.monotonic() < stop and Path(f"/proc/{pid}").exists():
            rclpy.spin_once(node, timeout_sec=0.2)
            if not graph_reported and sum(counts.values()) > 0:
                actions = node.get_action_names_and_types()
                state_services = [name for name, _ in node.get_service_names_and_types()
                                  if name == "/collision_monitor/get_state"]
                print(f"D06_L1_TERMINAL_B_ACTION_GRAPH={actions} LIFECYCLE_GET_STATE={state_services}", flush=True)
                graph_reported = True
    except KeyboardInterrupt:
        print("D06_L1_TERMINAL_B_USER_STOP (observer only)", flush=True)
    finally:
        print("D06_L1_TERMINAL_B_SAMPLES " + " ".join(f"{k}={v}" for k, v in counts.items()), flush=True)
        node.destroy_node()
        rclpy.shutdown()
        print("D06_L1_TERMINAL_B_OBSERVATION_FINISHED; not an L1 acceptance verdict", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
