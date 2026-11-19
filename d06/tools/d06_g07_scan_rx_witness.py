#!/usr/bin/env python3
"""D06 read-only host-monotonic /scan and /safety/scan witness, D08 paired stamps.

Never publishes, sends a Goal, changes ROS params or relaxes Scan300ms.
Native transport probe is reused unchanged from D08 public commit.
"""
import argparse
import json
import math
from pathlib import Path
import signal
import time

TTL = 0.300


def historical_verdict(data):
    raw = data.get("raw", {})
    safe = data.get("safety", {})
    reasons = []
    for label, v in (("SAFETY", safe), ("RAW", raw)):
        gap = v.get("max_host_gap_sec")
        if not isinstance(gap, (int, float)) or not math.isfinite(gap):
            reasons.append(label + "_RECEIPT_UNMEASURED")
        elif gap > TTL:
            reasons.append(label + "_RECEIPT_TTL_300MS_BLOCKED")
    crash = data.get("process_crashes", [])
    if crash:
        reasons.append("NATIVE_CHILD_EXIT_MINUS_11")
    return {
        "first_failure": reasons[0] if reasons else "NO_FAILURE_IN_HISTORICAL_SUMMARY",
        "reasons": reasons, "process_crashes": crash,
        "scan_300ms_pass": not any("TTL_300MS" in r or "UNMEASURED" in r for r in reasons),
        "native_first_boundary_proven": bool(data.get("source_native_scan_receipt_pairs_available"))
          and bool(data.get("source_ros_scan_receipt_pairs_available")),
        "release": "HOLD", "goal_allowed": False, "certified_estop": False,
    }


def first_gap(records, limit=TTL):
    clean = [r for r in records if isinstance(r, dict)
             and isinstance(r.get("host_monotonic_sec"), (float, int))
             and isinstance(r.get("source_stamp_ns"), int)]
    for older, newer in zip(clean, clean[1:]):
        gap = float(newer["host_monotonic_sec"] - older["host_monotonic_sec"])
        if gap > limit and newer["source_stamp_ns"] > older["source_stamp_ns"]:
            return older, newer, gap
    return None


def native_clock_window(left, right, clock):
    """Independent same-host Gazebo /clock receive witness around first native scan gap.

    Its instantaneous RTF describes observed sim progress, NOT Gazebo internal
    sensor publisher or the underlying resource contention root cause.
    Diagnostic .6 threshold never changes any Scan/CM/Guard admission TTL.
    """
    r={"native_clock_progress":"UNMEASURED",
       "native_clock_window_rtf":None,
       "native_clock_max_host_gap_sec":None,
       "native_clock_bracketed":False}
    if not isinstance(clock,(tuple,list)):return r
    pairs=[]
    for x in clock:
        if not isinstance(x,dict):continue
        h=x.get("host_monotonic_sec")
        stamp=x.get("sim_stamp_ns")
        if isinstance(h,(int,float)) and math.isfinite(h) and isinstance(stamp,int) and stamp>0:
            pairs.append((float(h),stamp))
    pairs.sort()
    if len(pairs)<3:return r
    before=min(pairs,key=lambda z:abs(z[0]-left))
    after=min(pairs,key=lambda z:abs(z[0]-right))
    if abs(before[0]-left)>.08 or abs(after[0]-right)>.08 or after[0]<=before[0]:
        return r
    bracket=[z for z in pairs if before[0]<=z[0]<=after[0]]
    if len(bracket)<3:return r
    if any(b[0]<=a[0] or b[1]<=a[1] for a,b in zip(bracket,bracket[1:])):
        return r
    span=after[0]-before[0]
    simspan=(after[1]-before[1])/1e9
    if span<=0 or simspan<=0:return r
    rate=simspan/span
    r.update({
      "native_clock_progress":"SLOW" if rate<.6 else "NORMAL_OR_FAST",
      "native_clock_window_rtf":round(rate,6),
      "native_clock_max_host_gap_sec":round(
          max(b[0]-a[0] for a,b in zip(bracket,bracket[1:])),6),
      "native_clock_bracketed":True,
      "native_clock_window_host_sec":round(span,6),
      "native_clock_sim_progress_sec":round(simspan,6),
      "native_clock_internal_sensor_publish_measured":False,
    })
    return r


def classify(native, raw, safety, limit=TTL, native_clock=None):
    """Compare same source stamps on the same host; never claim bridge send proof."""
    r = {
        "schema": "axia.d06.g07.native_ros_first_scan_ttl.v1",
        "candidate": "NO_ROS_TTL_VIOLATION_WITNESSED",
        "cause": "UNDETERMINED", "native_gap_sec": None,
        "raw_gap_sec": None, "safety_gap_sec": None,
        "native_stamp_pair_matched": False,
        "publisher_send_timing_proven": False,
        "bridge_dds_send_measured": False,
        "ttl_sec": limit, "release": "HOLD", "goal_allowed": False,
        "native_clock_progress": "UNMEASURED", "native_clock_window_rtf": None,
        "native_clock_max_host_gap_sec": None, "native_clock_bracketed": False,
    }
    raw_first=first_gap(raw,limit)
    safety_first=first_gap(safety,limit)
    if raw_first:r["raw_gap_sec"]=round(raw_first[2],6)
    if safety_first:r["safety_gap_sec"]=round(safety_first[2],6)
    # Earliest *host* timing violation wins across both subscriptions.
    # Different subscriber startup times mean index 6 vs 11 is NOT chronology.
    selected=[(x[1]["host_monotonic_sec"],kind,x) for kind,x in
              (("safety",safety_first),("raw",raw_first)) if x is not None]
    selected.sort(key=lambda v:v[0])
    _,first_topic,first=selected[0] if selected else (None,None,None)
    if first is None:return r
    before,after,_=first
    r["candidate"]="NATIVE_SOURCE_STAMP_PAIR_UNAVAILABLE"
    r["first_ros_topic"]=first_topic
    r["first_ros_source_stamps_ns"]=[before["source_stamp_ns"],after["source_stamp_ns"]]
    r["first_ros_host_receive_sec"]=[before["host_monotonic_sec"],after["host_monotonic_sec"]]
    matches={}
    for n in native:
        if not isinstance(n,dict):continue
        t=n.get("host_monotonic_sec")
        stamp=n.get("source_stamp_ns")
        if (stamp in (before["source_stamp_ns"],after["source_stamp_ns"])
            and isinstance(t,(int,float)) and math.isfinite(t)):
            matches.setdefault(stamp,float(t))
    if len(matches)!=2:return r
    left,right=(matches[before["source_stamp_ns"]],
                matches[after["source_stamp_ns"]])
    if right<=left:return r
    if left>before["host_monotonic_sec"]+.05 or right>after["host_monotonic_sec"]+.05:
        r["candidate"]="NATIVE_CLOCK_ORDER_NOT_VERIFIED"
        return r
    gap=right-left
    r["native_stamp_pair_matched"]=True
    r["native_gap_sec"]=round(gap,6)
    r["native_to_ros_before_sec"]=round(float(before["host_monotonic_sec"])-left,6)
    r["native_to_ros_after_sec"]=round(float(after["host_monotonic_sec"])-right,6)
    r["candidate"]=("AT_OR_BEFORE_NATIVE_TRANSPORT_RX"
                     if gap>limit else "AFTER_NATIVE_TRANSPORT_RX")
    r.update(native_clock_window(left, right, native_clock))
    return r


def read_jsonl(path, max_lines=4096):
    p=Path(path)
    if not p.is_file():return []
    result=[]
    with p.open(encoding="utf-8") as source:
        for i,line in enumerate(source):
            if i>=max_lines:break
            try:
                obj=json.loads(line)
            except ValueError:
                continue
            if isinstance(obj,dict):result.append(obj)
    return result


def observe(path,max_events=4096,max_seconds=180):
    """Read-only ROS observer; no implicit approval if it fails."""
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan
    if path.exists():raise ValueError("D06_G07_RX_OUTPUT_EXISTS")
    path.parent.mkdir(parents=True,exist_ok=True)
    stop=[False]
    def done(_sig,_frame):stop[0]=True
    signal.signal(signal.SIGTERM,done)
    signal.signal(signal.SIGINT,done)
    rclpy.init()
    node=rclpy.create_node("d06_g07_rx_readonly_witness")
    counts={"raw":0,"safety":0}
    with path.open("x",encoding="utf-8",buffering=1) as dest:
        subs=[]
        def callback(msg,topic):
            host=time.monotonic()
            stamp=msg.header.stamp
            stamp_ns=int(stamp.sec)*1_000_000_000+int(stamp.nanosec)
            if stamp_ns<=0 or counts[topic]>=max_events:return
            dest.write(json.dumps({"topic":topic,
                "host_monotonic_sec":round(host,6),
                "source_stamp_ns":stamp_ns},separators=(",",":"))+"\n")
            counts[topic]+=1
        for topic,name in (("/scan","raw"),("/safety/scan","safety")):
            subs.append(node.create_subscription(LaserScan,topic,
              lambda msg,n=name: callback(msg,n),qos_profile_sensor_data))
        deadline=time.monotonic()+max_seconds
        try:
            print("D06_G07_ROS_RX_WITNESS_READY_NO_GOAL",flush=True)
            while not stop[0] and time.monotonic()<deadline:
                rclpy.spin_once(node,timeout_sec=.10)
        except (KeyboardInterrupt, ExternalShutdownException):
            # ROS 2 shutdown signal handler has already ended the context.
            # The completed read-only evidence is preserved, not a system PASS.
            print("D06_G07_ROS_RX_EXTERNAL_SHUTDOWN_HANDLED_NO_GOAL",flush=True)
        finally:
            for sub in subs:node.destroy_subscription(sub)
            node.destroy_node()
            rclpy.try_shutdown()
    print("D06_G07_ROS_RX_WITNESS_STOP "+json.dumps(counts,sort_keys=True),flush=True)
    return 0 if all(v>0 for v in counts.values()) else 3


def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--capture",action="store_true")
    g.add_argument("--analyze",action="store_true")
    g.add_argument("--self-check",action="store_true")
    p.add_argument("--ros-jsonl",type=Path)
    p.add_argument("--native-jsonl",type=Path)
    p.add_argument("--native-clock-jsonl",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_check:
        print("D06_G07_FIRST_SCAN_TTL_HOLD NO_ROS_NO_GAZEBO_NO_GOAL")
        return 0
    if not a.ros_jsonl or not a.output:
        p.error("--ros-jsonl and --output required")
    if a.capture:
        return observe(a.ros_jsonl)
    scans=read_jsonl(a.ros_jsonl,8192)
    native=read_jsonl(a.native_jsonl,4096) if a.native_jsonl else []
    raw=[x for x in scans if x.get("topic")=="raw"]
    safe=[x for x in scans if x.get("topic")=="safety"]
    # Analyze complete same-session trace. Captures startup too;
    # never equate this first gap with the Student probe first gap.
    native_clock=read_jsonl(a.native_clock_jsonl,4096) if a.native_clock_jsonl else []
    report=classify(native,raw,safe,native_clock=native_clock)
    report["native_clock_count"]=len(native_clock)
    report["observer_raw_count"]=len(raw)
    report["observer_safety_count"]=len(safe)
    report["native_count"]=len(native)
    report["original_student_first_gap_same_pair_proven"]=False
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("D06_G07_FIRST_SCAN_TTL_HOLD candidate="+report["candidate"]+
          " native_clock="+report["native_clock_progress"]+
          " local_rtf="+str(report["native_clock_window_rtf"])+
          " release=HOLD no_goal=true",flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
