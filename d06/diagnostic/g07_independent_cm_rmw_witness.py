#!/usr/bin/env python3
"""G07 read-only independent ROS CM FastDDS receive witness (CI diagnostics).

Reuses D08 PR #202's bounded, callback-I/O-free isolated ROS pattern.
Independent rclpy process/DDS participant, same host monotonic clock.
No output Twist, no motion/safety changes, no raw message/GID custody.
Never implies certified E-stop or formal safety release.
"""
from collections import deque
import argparse
import json
import math
from pathlib import Path
import signal
import threading
import time


class BoundedCmEvidence:
    def __init__(self,max_samples=12000):
        if type(max_samples) is not int or not 1 <= max_samples <= 20000:
            raise ValueError("CM_WITNESS_BOUNDED_SAMPLE_COUNT_REQUIRED")
        self.rows=deque(maxlen=max_samples)
        self.dropped=0

    def add(self,row):
        if len(self.rows)==self.rows.maxlen:
            self.dropped+=1
        self.rows.append(row)


def normalize_witness_metadata(info):
    """Retain source/received fields even when sequence is unsupported.

    Some Jazzy rclpy MessageInfo adapters omit publication_sequence_number.
    Missing that *one* member must not destroy two valid timestamps; it
    does block exact same-publication matching and hence any safety PASS.
    """
    def one(name):
        try:
            # Jazzy 2-argument subscription MessageInfo is a dict in
            # the actual original Observer. Keep object fallback for unit
            # adapters; never coerce missing fields into valid measurements.
            value=(info.get(name) if isinstance(info,dict)
                   else getattr(info,name))
            if type(value) is bool:
                return -1
            v=int(value)
            return v if v>=0 else -1
        except (AttributeError,TypeError,ValueError,OverflowError):
            return -1
    return (one("source_timestamp"),one("received_timestamp"),
            one("publication_sequence_number"))


def _independent_monotonic_continuity_hold(result,original,independent,start,end):
    """Host monotonic independent callback continuity only, NOT exact DDS pair.

    A complete independent witness over the original host interval is
    weaker than exact pub-seq pairing but demonstrates source availability
    at this *topic* on this host while the original subscriber missed its
    120ms callback interval. Never infer DDS, Executor or scheduler root.
    """
    if any(_valid(row) for row in independent):
        # Fully specified metadata but a different sequence/source stamp:
        # original strict exact-pair policy rejects it.
        return result
    times=sorted(row["t"] for row in independent
                 if isinstance(row,dict) and row.get("kind")=="pre_guard"
                 and type(row.get("t")) in (float,int)
                 and math.isfinite(row["t"]))
    before=[t for t in times if t<=start]
    after=[t for t in times if t>=end]
    if not before or not after:
        return result
    left,right=before[-1],after[0]
    if start-left>.12 or right-end>.12:
        return result
    span=[t for t in times if left<=t<=right]
    inside=[t for t in span if start<t<end]
    if len(inside)<5 or len(span)<7:
        return result
    maxgap=max((b-a for a,b in zip(span,span[1:])),default=float("inf"))
    if maxgap<=0 or maxgap>.12 or end-start<=.12:
        return result
    return {**result,
            "status":"INDEPENDENT_CM_CALLBACKS_CONTINUED_EXACT_PAIR_UNVERIFIED_HOLD",
            "original_host_callback_gap_ms":round((end-start)*1000,6),
            "independent_host_callback_count_inside_gap":len(inside),
            "independent_max_callback_interval_ms":round(maxgap*1000,6),
            "independent_host_coverage_start_delta_ms":round((start-left)*1000,6),
            "independent_host_coverage_end_delta_ms":round((right-end)*1000,6),
            "same_publication_exact_pair_proven":False,
            "metadata_publication_sequence_available":False,
            "original_executor_root_proven":False,
            "transport_root_proven":False,
            "root_cause_proven":False,"release":"HOLD"}


def _valid(row):
    return (isinstance(row,dict) and row.get("kind")=="pre_guard" and
            type(row.get("t")) in (int,float) and math.isfinite(row["t"]) and
            type(row.get("rmw_source_ns")) is int and row["rmw_source_ns"]>0 and
            type(row.get("rmw_received_ns")) is int and
            row["rmw_received_ns"]>=row["rmw_source_ns"] and
            type(row.get("rmw_publication_seq")) is int and
            row["rmw_publication_seq"]>=0)


def compare_same_cm_pair(original,independent,start,end):
    """One exact same publisher pair only, never cross process stream maxima.

    Both processes' absolute host-monotonic event times share one host.
    Source and reception *intervals* are comparable within their own RMW
    timebase, not against host monotonic absolute epochs.
    """
    result=dict(schema="axia.g07.independent_cm_first_rmw_pair.v1",
                status="INDEPENDENT_CM_EXACT_PAIR_NOT_VERIFIED_HOLD",
                original_receive_gap_ms=None,
                independent_receive_gap_ms=None,
                original_source_gap_ms=None,
                independent_source_gap_ms=None,
                matched_publication_seq_gap=None,
                root_cause="UNDETERMINED",root_cause_proven=False,
                transport_root_proven=False,
                original_executor_root_proven=False,
                safety_ttl_changed=False,certified_estop=False,release="HOLD")
    if (not isinstance(original,list) or not isinstance(independent,list)
            or type(start) not in (int,float) or type(end) not in (int,float)
            or not math.isfinite(start) or not math.isfinite(end) or end<=start):
        return result
    target=[]
    for t in (start,end):
        rows=[row for row in original if _valid(row) and
              abs(row["t"]-t)<.0000005]
        if len(rows)!=1:return result
        target.append(rows[0])
    a,b=target
    if b["rmw_publication_seq"]-a["rmw_publication_seq"]!=1:return result
    # Match exactly the SAME publisher's consecutive DDS samples.
    wanted={(p["rmw_publication_seq"],p["rmw_source_ns"]):p for p in target}
    pair=[]
    for p in target:
        candidates=[row for row in independent if _valid(row) and
            (row["rmw_publication_seq"],row["rmw_source_ns"])==
            (p["rmw_publication_seq"],p["rmw_source_ns"])]
        if len(candidates)!=1:
            return _independent_monotonic_continuity_hold(
                result,original,independent,start,end)
        pair.append(candidates[0])
    c,d=pair
    orig_src=b["rmw_source_ns"]-a["rmw_source_ns"]
    ind_src=d["rmw_source_ns"]-c["rmw_source_ns"]
    orig_rx=b["rmw_received_ns"]-a["rmw_received_ns"]
    ind_rx=d["rmw_received_ns"]-c["rmw_received_ns"]
    if min(orig_src,ind_src,orig_rx,ind_rx)<=0:
        return {**result,"status":"INDEPENDENT_CM_TIMEBASE_REGRESSION_HOLD"}
    if orig_src!=ind_src:return result
    result.update(original_receive_gap_ms=round(orig_rx/1e6,6),
                  independent_receive_gap_ms=round(ind_rx/1e6,6),
                  original_source_gap_ms=round(orig_src/1e6,6),
                  independent_source_gap_ms=round(ind_src/1e6,6),
                  matched_publication_seq_gap=1)
    if orig_rx>=120_000_000 and ind_rx<120_000_000:
        result["status"]="ORIGINAL_PROCESS_RECEIPT_GAP_CANDIDATE"
    elif orig_rx>=120_000_000 and ind_rx>=120_000_000:
        result["status"]="TWO_PROCESS_RECEIPT_GAP_CANDIDATE"
    elif orig_rx<120_000_000 and ind_rx>=120_000_000:
        result["status"]="INDEPENDENT_PROCESS_RECEIPT_GAP_CANDIDATE"
    else:
        result["status"]="TWO_PROCESS_CM_RECEIPT_WITHIN_120_CANDIDATE"
    return result


def run(out, max_samples=12000):
    """Read one *existing* /cmd_vel_pre_guard topic, no outgoing messages."""
    from geometry_msgs.msg import Twist
    import rclpy
    from rclpy.executors import ShutdownException, ExternalShutdownException
    out=Path(out)
    if out.exists():raise ValueError("CM_WITNESS_OUTPUT_EXISTS")
    out.parent.mkdir(parents=True,exist_ok=True)
    evidence=BoundedCmEvidence(max_samples)
    stop=threading.Event()
    def handle(_sig,_frame): stop.set()
    signal.signal(signal.SIGINT,handle)
    signal.signal(signal.SIGTERM,handle)
    rclpy.init()
    node=rclpy.create_node("axia_g07_independent_cm_rmw_observation_only",
                           start_parameter_services=False)
    def on_cm(_message,info):
        at=time.monotonic()
        src,rx,seq=normalize_witness_metadata(info)
        evidence.add(dict(kind="pre_guard",t=round(at,9),
                          rmw_source_ns=src,rmw_received_ns=rx,
                          rmw_publication_seq=seq))
    sub=node.create_subscription(Twist,"/cmd_vel_pre_guard",on_cm,10)
    print("AXIA_G07_INDEPENDENT_CM_RMW_PROCESS_READY",flush=True)
    try:
        try:
            while not stop.is_set() and rclpy.ok():
                rclpy.spin_once(node,timeout_sec=.05)
        except (ShutdownException,ExternalShutdownException):
            if rclpy.ok() and not stop.is_set():raise
    finally:
        # No JSON/disk I/O in any DDS callback. Preserve bounded evidence
        # even if rclpy installed a SIGTERM handler and shut its context.
        with out.open("x",encoding="utf8") as fd:
            for row in evidence.rows:
                fd.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
        print("AXIA_G07_INDEPENDENT_CM_RMW_CAPTURE_DONE "+
              json.dumps({"accepted":len(evidence.rows),"dropped":evidence.dropped},
                         sort_keys=True),flush=True)
        node.destroy_node()
        if rclpy.ok():rclpy.shutdown()
    return 0


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--max-samples",type=int,default=12000)
    args=p.parse_args()
    raise SystemExit(run(args.out,args.max_samples))
