#!/usr/bin/env python3
"""Read-only Gazebo Transport /scan + /clock causal witness, same host clock.

Separate Python process from the ROS Observer; native transport SUBSCRIBER
callback timestamps do not measure Gazebo internal publisher or bridge send.
Bounded JSONL evidence; does not publish or control the robot.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import threading
import time


def run(topic: str, output: Path, max_events: int = 1024,
        clock_output: Path | None = None, max_clock_events: int = 2048) -> int:
    from gz.msgs10.laserscan_pb2 import LaserScan
    from gz.msgs10.clock_pb2 import Clock
    from gz.transport13 import Node

    if topic != "/scan":
        raise ValueError("D08_GZ_NATIVE_SCAN_TOPIC_MUST_MATCH_BRIDGE")
    if not 100 <= max_events <= 4096 or not 100 <= max_clock_events <= 4096:
        raise ValueError("D08_GZ_NATIVE_TRACE_NOT_BOUNDED")
    output=Path(output)
    if output.exists():
        raise ValueError("D08_GZ_NATIVE_TRACE_OUTPUT_EXISTS")
    output.parent.mkdir(parents=True,exist_ok=True)
    if clock_output is not None:
        clock_output=Path(clock_output)
        if clock_output.exists() or clock_output==output:
            raise ValueError("D08_GZ_NATIVE_CLOCK_TRACE_OUTPUT_EXISTS")
    stop=threading.Event()
    lock=threading.Lock()
    counts={"scan":0,"clock":0,"scan_dropped":0,"clock_dropped":0}
    last_clock_at=[float("-inf")]

    def terminate(_sig,_frame):
        stop.set()

    signal.signal(signal.SIGTERM,terminate)
    signal.signal(signal.SIGINT,terminate)
    node=Node()
    with output.open("x",encoding="utf-8",buffering=1) as dst:
        clock_dst=(clock_output.open("x",encoding="utf-8",buffering=1)
                   if clock_output is not None else None)
        try:
            def on_scan(msg:LaserScan):
                at=time.monotonic()
                try:
                    stamp=msg.header.stamp
                    stamp_ns=int(stamp.sec)*1_000_000_000+int(stamp.nsec)
                except (AttributeError,ValueError,TypeError):
                    return
                if stamp_ns<=0:
                    return
                with lock:
                    if counts["scan"]>=max_events:
                        counts["scan_dropped"]+=1
                        return
                    dst.write(json.dumps({
                        "host_monotonic_sec":round(at,6),
                        "source_stamp_ns":stamp_ns,
                    },separators=(",",":"))+"\n")
                    counts["scan"]+=1

            def on_clock(msg:Clock):
                at=time.monotonic()
                try:
                    stamp=msg.sim
                    stamp_ns=int(stamp.sec)*1_000_000_000+int(stamp.nsec)
                except (AttributeError,ValueError,TypeError):
                    return
                if stamp_ns<=0 or clock_dst is None:
                    return
                with lock:
                    # 25Hz bounded witness preserves host callback gaps;
                    # this is diagnostic sampling, NOT a Clock safety TTL.
                    if at-last_clock_at[0]<.04:
                        return
                    last_clock_at[0]=at
                    if counts["clock"]>=max_clock_events:
                        counts["clock_dropped"]+=1
                        return
                    clock_dst.write(json.dumps({
                        "host_monotonic_sec":round(at,6),
                        "sim_stamp_ns":stamp_ns,
                    },separators=(",",":"))+"\n")
                    counts["clock"]+=1

            if not node.subscribe(LaserScan,topic,on_scan):
                print("D08_NATIVE_GZ_SCAN_SUBSCRIBE_BLOCKED",flush=True)
                return 2
            if clock_dst is not None and not node.subscribe(Clock,"/clock",on_clock):
                print("D08_NATIVE_GZ_CLOCK_SUBSCRIBE_BLOCKED",flush=True)
                return 2
            print("D08_NATIVE_GZ_SCAN_CLOCK_RECEIVER_READY topic=/scan clock=/clock",
                  flush=True)
            try:
                while not stop.is_set():
                    stop.wait(.05)
            finally:
                print("D08_NATIVE_GZ_SCAN_CLOCK_RECEIVER_STOP "
                      +json.dumps(counts,sort_keys=True),flush=True)
            return 0
        finally:
            if clock_dst is not None:
                clock_dst.close()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--topic",default="/scan")
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--clock-out",type=Path)
    parser.add_argument("--max-events",type=int,default=1024)
    parser.add_argument("--max-clock-events",type=int,default=2048)
    args=parser.parse_args()
    raise SystemExit(run(args.topic,args.out,args.max_events,
                         args.clock_out,args.max_clock_events))
