#!/usr/bin/env python3
"""Independent process read-only ROS Scan subscriber for first-gap evidence.

Separates rclpy callback scheduling from the original D08 Observer's Python
interpreter. This witness never publishes or commands a robot; cannot measure
ros_gz_bridge internal send, DDS queueing, or certified safety stop behavior.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import signal
import threading
import time


def run(out:Path,max_samples:int=1024)->int:
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan

    if not 50<=max_samples<=4096:
        raise ValueError("D08_ISOLATED_ROS_TRACE_MUST_BE_BOUNDED")
    out=Path(out)
    if out.exists():
        raise ValueError("D08_ISOLATED_ROS_TRACE_OUTPUT_EXISTS")
    out.parent.mkdir(parents=True,exist_ok=True)
    stop=threading.Event()
    counter={"accepted":0,"dropped":0}
    def terminate(_sig,_frame):
        stop.set()
    signal.signal(signal.SIGINT,terminate)
    signal.signal(signal.SIGTERM,terminate)
    rclpy.init()
    node=rclpy.create_node("axia_d08_isolated_scan_no_goal")
    try:
        with out.open("x",encoding="utf8",buffering=1) as dst:
            def on_scan(msg:LaserScan):
                at=time.monotonic()
                stamp=msg.header.stamp
                ns=int(stamp.sec)*1_000_000_000+int(stamp.nanosec)
                if ns<=0:
                    return
                if counter["accepted"]>=max_samples:
                    counter["dropped"]+=1
                    return
                dst.write(json.dumps({
                    "topic":"scan",
                    "host_monotonic_sec":round(at,6),
                    "source_stamp_ns":ns,
                },separators=(",",":"))+"\n")
                counter["accepted"]+=1
            sub=node.create_subscription(
                LaserScan,"/scan",on_scan,qos_profile_sensor_data)
            print("D08_ISOLATED_ROS_SCAN_PROCESS_READY",flush=True)
            while not stop.is_set():
                rclpy.spin_once(node,timeout_sec=.05)
            print("D08_ISOLATED_ROS_SCAN_PROCESS_STOP "
                  +json.dumps(counter,sort_keys=True),flush=True)
            return 0
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--max-samples",type=int,default=1024)
    args=parser.parse_args()
    raise SystemExit(run(args.out,args.max_samples))
