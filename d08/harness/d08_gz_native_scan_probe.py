#!/usr/bin/env python3
"""Bounded, read-only Gazebo Harmonic native /scan RX witness.

Standalone process: its Python GIL / event loop is separate from rclpy.
Native transport subscriber *receive* timing is NOT Gazebo source publish
or DDS/ros_gz_bridge send timing. Never publish messages or control instructions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import threading
import time


def run(topic: str, output: Path, max_events: int = 1024) -> int:
    from gz.msgs10.laserscan_pb2 import LaserScan
    from gz.transport13 import Node

    if topic != "/scan":
        raise ValueError("D08_GZ_NATIVE_SCAN_TOPIC_MUST_MATCH_BRIDGE")
    if not 100 <= max_events <= 4096:
        raise ValueError("D08_GZ_NATIVE_TRACE_NOT_BOUNDED")

    output = Path(output)
    if output.exists():
        raise ValueError("D08_GZ_NATIVE_TRACE_OUTPUT_EXISTS")
    output.parent.mkdir(parents=True, exist_ok=True)
    stop = threading.Event()
    lock = threading.Lock()
    counter = {"accepted": 0, "dropped": 0}

    def terminate(_sig, _frame):
        stop.set()

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    node = Node()
    with output.open("x", encoding="utf-8", buffering=1) as dst:
        def on_scan(msg: LaserScan):
            at = time.monotonic()
            try:
                stamp = msg.header.stamp
                source_stamp_ns = int(stamp.sec) * 1_000_000_000 + int(stamp.nsec)
            except (AttributeError, TypeError, ValueError):
                return
            if source_stamp_ns <= 0:
                return
            with lock:
                if counter["accepted"] >= max_events:
                    counter["dropped"] += 1
                    return
                dst.write(json.dumps({
                    "host_monotonic_sec": round(at, 6),
                    "source_stamp_ns": source_stamp_ns,
                }, separators=(",", ":")) + "\n")
                dst.flush()
                counter["accepted"] += 1

        if not node.subscribe(LaserScan, topic, on_scan):
            print("D08_NATIVE_GZ_SCAN_SUBSCRIBE_BLOCKED", flush=True)
            return 2
        print("D08_NATIVE_GZ_SCAN_RECEIVER_READY topic=/scan", flush=True)
        try:
            while not stop.is_set():
                stop.wait(.05)
        finally:
            print("D08_NATIVE_GZ_SCAN_RECEIVER_STOP "
                  + json.dumps(counter, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="/scan")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-events", type=int, default=1024)
    args = parser.parse_args()
    raise SystemExit(run(args.topic, args.out, args.max_events))
