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

def _bag_max_rx_gap_ms(rows, topic):
    """Only adjacent receive intervals from one rosbag recorder's clock."""
    samples=rows.get(topic,[]) if isinstance(rows,dict) else []
    if not isinstance(samples,list) or len(samples)<2:
        return None
    stamps=[row.get("rx_ns") for row in samples if isinstance(row,dict)
            and type(row.get("rx_ns")) is int and row["rx_ns"]>0]
    if len(stamps)<2 or len(stamps)!=len(samples):
        return None
    gaps=[b-a for a,b in zip(stamps,stamps[1:])]
    if any(g<=0 for g in gaps):
        return None
    return _safe_msec(max(gaps))


def _out(status,**fields):
    result=dict(schema="axia.g07.scan_exact_rosbag_receive_first_pair.v1",
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
                certified_estop=False,goal_sent=False,release="HOLD")
    result.update(fields)
    return result

def _classify_scan(first_pair, rows, *, pregoal_report=None):
    if not isinstance(rows,dict):
        return _out("EXACT_LASERSCAN_BAG_PAIR_UNVERIFIED_HOLD")
    clock_max=_bag_max_rx_gap_ms(rows,"/clock")
    odom_max=_bag_max_rx_gap_ms(rows,"/odom")
    if not isinstance(first_pair,dict):
        reported=(pregoal_report if isinstance(pregoal_report,dict) else {})
        first=reported.get("first_delivery_violation")
        channel=first.get("channel") if isinstance(first,dict) else None
        if channel in ("clock","odom") and (clock_max is not None or odom_max is not None):
            return _out("CLOCK_ODOM_ROSBAG_INTERVALS_NO_EXACT_SCAN_PAIR_HOLD",
                        independent_bag_clock_max_gap_ms=clock_max,
                        independent_bag_odom_max_gap_ms=odom_max,
                        observer_first_delivery_channel=channel,
                        observer_clock_max_wall_gap_ms=reported.get("clock_max_wall_gap_ms"),
                        observer_odom_max_wall_gap_ms=reported.get("odom_max_wall_gap_ms"),
                        same_first_rosbag_record_pair_proven=False)
        return _out("PREG0AL_FIRST_SCAN_PAIR_NOT_AVAILABLE_HOLD")
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
                independent_bag_clock_max_gap_ms=clock_max,
                independent_bag_odom_max_gap_ms=odom_max,
                observer_first_scan_gap_ms=round(float(gap),6),
                expected_first_scan_header_gap_ms=_safe_msec(h1-h0),
                independent_bag_scan_gap_ms=scan,
                independent_bag_safety_scan_gap_ms=safety,
                rosbag_clock_record_count=len(clock) if isinstance(clock,list) else None,
                rosbag_odom_record_count=len(odom) if isinstance(odom,list) else None,
                same_header_pair_rosbag_timebase_only=True)

def _with_first_clock_odom(result, rows, pregoal):
    """Match the FIRST Clock/Odom callback pair to this rosbag's same stamps.

    Never infer the gap from bag session maxima, nor compare absolute
    system/monotonic clocks. Exact duplicate or missing pair is HOLD.
    These observations classify delivery and do not assert a DDS root cause.
    """
    result["matched_exact_first_clock_pair"]=False
    result["matched_exact_first_odom_pair"]=False
    result["independent_first_clock_rx_gap_ms"]=None
    result["independent_first_odom_rx_gap_ms"]=None
    result["observer_first_clock_gap_ms"]=None
    result["observer_first_odom_gap_ms"]=None
    result["clock_odom_exact_first_class"]="FIRST_CLOCK_ODOM_PAIR_NOT_APPLICABLE_HOLD"
    if not isinstance(pregoal,dict) or not isinstance(rows,dict):
        return result
    first=pregoal.get("first_delivery_violation")
    topic=first.get("channel") if isinstance(first,dict) else None
    if topic not in ("clock","odom"):
        return result
    result["clock_odom_exact_first_class"]=(
        "FIRST_"+topic.upper()+"_EXACT_BAG_PAIR_UNVERIFIED_HOLD")
    gap=first.get("gap_ms")
    if type(gap) not in (int,float) or not math.isfinite(gap) or gap<=0:
        return result
    result["observer_first_"+topic+"_gap_ms"]=round(float(gap),6)
    h0=_ns_from_float(first.get("previous_header_sim"))
    h1=_ns_from_float(first.get("current_header_sim"))
    if h0 is None or h1 is None or h1<=h0:
        return result
    simgap=first.get("header_sim_gap_ms")
    if (type(simgap) not in (int,float) or not math.isfinite(simgap)
            or simgap<=0 or abs(simgap-(h1-h0)/1_000_000)>.02):
        return result
    matches={}
    for row in rows.get("/"+topic,[]):
        if not isinstance(row,dict):
            continue
        if row.get("header_sim_ns") in (h0,h1):
            matches.setdefault(row["header_sim_ns"],[]).append(row.get("rx_ns"))
    if len(matches.get(h0,[]))!=1 or len(matches.get(h1,[]))!=1:
        return result
    a,b=matches[h0][0],matches[h1][0]
    if type(a) is not int or type(b) is not int or a<=0 or b<=a:
        return result
    result["matched_exact_first_"+topic+"_pair"]=True
    bag_gap=_safe_msec(b-a)
    result["independent_first_"+topic+"_rx_gap_ms"]=bag_gap
    if gap>300 and bag_gap<=300:
        status="FIRST_"+topic.upper()+"_OBSERVER_GAP_NOT_REPRODUCED_IN_BAG_CANDIDATE_HOLD"
    elif bag_gap>300:
        status="FIRST_"+topic.upper()+"_BAG_AND_OBSERVER_GAP_CANDIDATE_HOLD"
    else:
        status="FIRST_"+topic.upper()+"_DELIVERY_EXACT_BAG_PAIR_WITHIN_BOUND_HOLD"
    result["clock_odom_exact_first_class"]=status
    return result


def classify(first_pair, rows, *, pregoal_report=None):
    scan=_classify_scan(first_pair,rows,pregoal_report=pregoal_report)
    return _with_first_clock_odom(scan,rows,pregoal_report)


def _load_bag_numeric(bag_root, first, *, first_delivery=None):
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
    matched_topic=(
        "/"+first_delivery["channel"]
        if isinstance(first_delivery,dict)
           and first_delivery.get("channel") in ("clock","odom")
           and _ns_from_float(first_delivery.get("previous_header_sim")) is not None
           and _ns_from_float(first_delivery.get("current_header_sim")) is not None
        else None)
    decode_types={"/scan","/safety/scan"}
    if matched_topic is not None:
        decode_types.add(matched_topic)
    msgtypes={topic:get_message(types[topic]) for topic in wanted
              if topic in types and topic in decode_types}
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
                row={"rx_ns":int(rx_ns)}
                # Decode ONLY the first violating sensor's exact message
                # stamps for offline pair matching; never during Goal.
                if topic==matched_topic and topic in msgtypes:
                    msg=deserialize_message(payload,msgtypes[topic])
                    stamp=(msg.clock if topic=="/clock" else msg.header.stamp)
                    row["header_sim_ns"]=(
                        int(stamp.sec)*1_000_000_000+int(stamp.nanosec))
                out[topic].append(row)
            continue
        if topic not in msgtypes:
            continue
        h0=_ns_from_float(first.get("previous_header_sim"))
        h1=_ns_from_float(first.get("current_header_sim"))
        if h0 is None or h1 is None:
            continue  # Clock/Odom-only first violation: do not decode RGB/LaserScan.
        msg=deserialize_message(payload,msgtypes[topic])
        stamp=int(msg.header.stamp.sec)*1_000_000_000+int(msg.header.stamp.nanosec)
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
        first_delivery=report.get("first_delivery_violation")
        if not isinstance(first,dict) and not isinstance(first_delivery,dict):
            result=_out("PREG0AL_FIRST_SCAN_PAIR_NOT_AVAILABLE_HOLD")
        else:
            rows,count,storage=_load_bag_numeric(
                a.bag_root,first if isinstance(first,dict) else {},
                first_delivery=first_delivery)
            result=classify(first,rows,pregoal_report=report)
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
