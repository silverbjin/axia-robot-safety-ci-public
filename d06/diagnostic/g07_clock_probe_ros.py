#!/usr/bin/env python3
"""Task01 CI diagnostic subscriber to /clock; no commands, publishers, Goal.

Writes ONLY host CLOCK_MONOTONIC receive ns and ROS simulation clock stamp ns
to a bounded, PRIVATE temporary file in the CI runner. This file is NEVER
an Actions artifact. A separate allowlist projects relative samples around
the first CM observer source-gap pair. Does not prove TF Buffer's own clock.
"""
from __future__ import annotations

import argparse
import json
import signal
import time
from pathlib import Path

MAX_ROWS=50_000


def capture(output, *, duration_sec):
    # ROS imports belong inside runtime-only path; pure L0 has no ROS.
    import rclpy
    from rclpy.signals import SignalHandlerOptions
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
    from rosgraph_msgs.msg import Clock

    requested_stop=[False]
    def request_stop(signum, frame):
        requested_stop[0]=True
    rows=[]
    # Official Jazzy rclpy.init() installs its OWN SIGTERM handler by default.
    # Explicit NO prevents it from replacing our bounded flush handler.
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    signal.signal(signal.SIGTERM,request_stop)
    signal.signal(signal.SIGINT,request_stop)
    node=None
    try:
        node=Node("axia_g07_task01_public_ci_clock_probe")
        qos=QoSProfile(depth=10,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE)
        def observe(msg):
            recv_ns=time.monotonic_ns()
            sec=int(msg.clock.sec)
            nsec=int(msg.clock.nanosec)
            if len(rows)<MAX_ROWS and sec>=0 and 0<=nsec<1_000_000_000:
                rows.append({"mono_ns":recv_ns,
                             "sim_ns":sec*1_000_000_000+nsec})
        node.create_subscription(Clock,"/clock",observe,qos)
        deadline=time.monotonic()+duration_sec
        while (not requested_stop[0] and time.monotonic()<deadline
                and rclpy.ok() and len(rows)<MAX_ROWS):
            rclpy.spin_once(node,timeout_sec=0.15)
    finally:
        # Persist FIRST. Even a late ROS node destroy/context error may not
        # erase the clock evidence of the first CM boundary.
        p=Path(output)
        p.parent.mkdir(parents=True,exist_ok=True)
        tmp=p.with_suffix(".partial")
        with tmp.open("w",encoding="utf-8") as dst:
            for row in rows:
                dst.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
        tmp.replace(p)
        print("AXIA_G07_TASK01_CLOCK_PROBE_CALLBACKS="+str(len(rows)))
        print("AXIA_G07_TASK01_CLOCK_PROBE_DIAGNOSTIC_ONLY_NO_GOAL_NO_RELEASE")
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    parser.add_argument("--max-duration-sec",type=int,default=700)
    args=parser.parse_args(argv)
    if not 1<=args.max_duration_sec<=900:
        parser.error("duration out of bounded range")
    capture(args.out,duration_sec=args.max_duration_sec)


if __name__=="__main__":
    main()
