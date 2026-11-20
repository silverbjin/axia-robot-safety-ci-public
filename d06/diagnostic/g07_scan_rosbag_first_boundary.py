#!/usr/bin/env python3
"""Exact first LaserScan.header pair in independent ROS bag receive timebase.

The Owner's pregoal callback uses Linux host monotonic. rosbag2 received
nanoseconds use the recorder's own system timestamp; compare INTERVALS only.
Sensor header stamps are sim-time, only exact matching pairs are joined.
No native Gazebo publish stamp, DDS transport or bridge bottleneck is proven.
The bag remains private/local; output is numeric allowlisted only. No Goal.
"""
import argparse
import json
import math
from pathlib import Path

def _ns_from_float(value):
    if type(value) not in (float,int) or not math.isfinite(value) or value<0:
        return None
    return round(value*1_000_000_000)

def _safe_msec(value):
    return round(value/1_000_000,6) if type(value) is int and value>=0 else None

def _out(status,**fields):
    return dict(schema="axia.g07.scan_exact_rosbag_receive_first_pair.v1",
                status=status,root_cause="UNDETERMINED",
                root_cause_proven=False,
                gazebo_native_publish_root_proven=False,
                ros_gz_bridge_root_proven=False,
                observer_callback_root_proven=False,
                all_clock_intervals_same_rosbag_receive_timebase=True,
                host_monotonic_minus_rosbag_epoch_subtracted=False,
                independent_bag_scan_gap_ms=None,
                independent_bag_safety_scan_gap_ms=None,
                matched_exact_first_header_pair=False,
                certified_estop=False,goal_sent=False,release="HOLD",**fields)

def classify(first_pair, rows):
    if not isinstance(first_pair,dict) or not isinstance(rows,dict):
        return _out("EXACT_LASERSCAN_BAG_PAIR_UNVERIFIED_HOLD")
    h0=_ns_from_float(first_pair.get("previous_header_sim"))
    h1=_ns_from_float(first_pair.get("current_header_sim"))
    gap=first_pair.get("gap_ms")
    if (h0 is None or h1 is None or h1<=h0
            or type(gap) not in (float,int) or not math.isfinite(gap) or gap<0):
        return _out("EXACT_LASERSCAN_BAG_PAIR_UNVERIFIED_HOLD")

    def pair(topic):
        found={}
        for row in rows.get(topic,[]):
            if not isinstance(row,dict):
                continue
            t=row.get("header_sim_ns")
            rx=row.get("rx_ns")
            if t in (h0,h1) and type(rx) is int and rx>0:
                found.setdefault(t,[]).append(rx)
        if len(found.get(h0,[]))!=1 or len(found.get(h1,[]))!=1:
            return None
        a,b=found[h0][0],found[h1][0]
        return _safe_msec(b-a) if b>a else None
    scan=pair("/scan")
    safety=pair("/safety/scan")
    if scan is None:
        return _out("EXACT_LASERSCAN_BAG_PAIR_UNVERIFIED_HOLD",
                    independent_bag_safety_scan_gap_ms=safety,
                    expected_first_scan_header_gap_ms=_safe_msec(h1-h0))
    if scan>300 and safety is not None and safety>300:
        status="SHARED_SCAN_DELIVERY_GAP_CANDIDATE_HOLD"
    elif scan<=300 and gap>300:
        status="OBSERVER_RX_GAP_NOT_REPRODUCED_IN_BAG_CANDIDATE_HOLD"
    elif scan>300:
        status="BAG_SCAN_RECEIVE_GAP_CANDIDATE_HOLD"
    else:
        status="FIRST_SCAN_BAG_PAIR_WITHIN_BOUND_CAUSE_HOLD"
    clock=rows.get("/clock",[])
    odom=rows.get("/odom",[])
    return _out(status,matched_exact_first_header_pair=True,
                observer_first_scan_gap_ms=round(float(gap),6),
                expected_first_scan_header_gap_ms=_safe_msec(h1-h0),
                independent_bag_scan_gap_ms=scan,
                independent_bag_safety_scan_gap_ms=safety,
                rosbag_clock_record_count=len(clock) if isinstance(clock,list) else None,
                rosbag_odom_record_count=len(odom) if isinstance(odom,list) else None,
                same_header_pair_rosbag_timebase_only=True)

def _load_bag_numeric(bag_root, first):
    """Read existing rosbag2 sequentially, serialize no message content."""
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    path=Path(bag_root)
    if not path.is_dir():
        raise FileNotFoundError("ROSBAG_DIRECTORY_MISSING")
    storage_id=("sqlite3" if any(path.glob("*.db3")) else
                "mcap" if any(path.glob("*.mcap")) else "sqlite3")
    reader=rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(path),storage_id=storage_id),
                rosbag2_py.ConverterOptions(input_serialization_format="cdr",
                                            output_serialization_format="cdr"))
    types={t.name:t.type for t in reader.get_all_topics_and_types()}
    wanted={"/scan","/safety/scan","/clock","/odom"}
    if "/scan" not in types:
        raise RuntimeError("ROSBAG_SCAN_TOPIC_MISSING")
    # A bounded numeric-only buffer; on overrun we stop with HOLD, never PASS.
    out={k:[] for k in wanted}
    msgtypes={topic:get_message(types[topic]) for topic in wanted if topic in types
              and topic in ("/scan","/safety/scan")}
    maxread=1_000_000
    seen=0
    while reader.has_next():
        seen+=1
        if seen>maxread:
            raise RuntimeError("ROSBAG_BOUNDED_SAMPLE_CAP_REACHED")
        topic,payload,rx_ns=reader.read_next()
        if topic not in wanted:
            continue
        if topic in ("/clock","/odom"):
            if len(out[topic])<100000:
                out[topic].append({"rx_ns":int(rx_ns)})
            continue
        if topic not in msgtypes:
            continue
        msg=deserialize_message(payload,msgtypes[topic])
        stamp=int(msg.header.stamp.sec)*1_000_000_000+int(msg.header.stamp.nanosec)
        h0=_ns_from_float(first.get("previous_header_sim"))
        h1=_ns_from_float(first.get("current_header_sim"))
        if stamp in (h0,h1):
            out[topic].append({"rx_ns":int(rx_ns),"header_sim_ns":stamp})
    return out,seen,storage_id

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--bag-root",type=Path,required=True)
    p.add_argument("--first-report",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(argv)
    report={}
    try:
        if a.first_report.is_file() and a.first_report.stat().st_size<65536:
            report=json.loads(a.first_report.read_text())
        first=report.get("first_scan_timing_boundary")
        if not isinstance(first,dict):
            result=_out("PREG0AL_FIRST_SCAN_PAIR_NOT_AVAILABLE_HOLD")
        else:
            rows,count,storage=_load_bag_numeric(a.bag_root,first)
            result=classify(first,rows)
            result["bag_rows_inspected"]=count
            result["bag_storage_id"]=storage
    except (OSError,ValueError,RuntimeError,ImportError) as exc:
        result=_out("EXACT_LASERSCAN_BAG_READ_UNVERIFIED_HOLD",
                    diagnostic_error_type=type(exc).__name__)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    s=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n"
    if len(s.encode())>16384:
        result=_out("EXACT_LASERSCAN_BAG_OUTPUT_TOO_LARGE_HOLD")
        s=json.dumps(result,sort_keys=True,indent=2)+"\n"
    a.output.write_text(s)
    print("AXIA_G07_FIRST_SCAN_ROSBAG_EXACT_PAIR "+json.dumps(result,sort_keys=True),flush=True)
    return 0 # Read-only diagnostic MUST NOT grant field safety.

if __name__=="__main__":
    raise SystemExit(main())
