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


class IsolatedScanEvidence:
    """Bounded source-stamped samples; callback writes only first readiness row."""
    def __init__(self, max_samples):
        self.max_samples=max_samples
        self.rows=[]
        self.dropped=0

    def add(self, host_at, source_stamp_ns):
        if source_stamp_ns<=0:
            return False
        if len(self.rows)>=self.max_samples:
            self.dropped+=1
            return False
        self.rows.append({
            "topic":"scan",
            "host_monotonic_sec":round(host_at,6),
            "source_stamp_ns":int(source_stamp_ns),
        })
        return len(self.rows)==1

    def write_remaining(self, dst, start=0, stop=None):
        for row in self.rows[start:stop]:
            dst.write(json.dumps(row,separators=(",",":"))+"\n")


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
    evidence=IsolatedScanEvidence(max_samples)
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
                # Callback must never perform per-frame JSON/disk I/O.
                # One actual first sample is flushed for the existing startup
                # readiness probe; remaining exact timestamps stay in memory.
                if evidence.add(at,ns):
                    evidence.write_remaining(dst,start=0,stop=1)
            sub=node.create_subscription(
                LaserScan,"/scan",on_scan,qos_profile_sensor_data)
            print("D08_ISOLATED_ROS_SCAN_PROCESS_READY",flush=True)
            while not stop.is_set():
                rclpy.spin_once(node,timeout_sec=.05)
            evidence.write_remaining(dst,start=1)
            counter={"accepted":len(evidence.rows),"dropped":evidence.dropped}
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
