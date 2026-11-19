#!/usr/bin/env python3
"""Bounded official Jazzy rcl/rmw topic-handle trace summarizer (diagnostic only).

ROS rcl_take has only message pointer, not subscription_handle: it cannot
be mapped to /scan. Instead join rcl_subscription_init.rmw_subscription_handle
to rmw_take and rcl_publisher_init.rmw_publisher_handle to rmw_publish.
Nothing here proves matching LaserScan identity or DDS latency root cause.
"""
from __future__ import annotations
import argparse
import collections
import json
import re
import sys
import time
from pathlib import Path

EVENT = re.compile(r"\bros2:(rcl_publisher_init|rcl_subscription_init|rcl_publish|rcl_take|rmw_publish|rmw_take):")
TIME = re.compile(r"\[(?:(?:\d{4}-\d{2}-\d{2})\s+)?(\d\d):(\d\d):(\d\d)\.(\d+)\]")
PID = re.compile(r"\bvpid\s*=\s*(\d+)")
PROC = re.compile(r'\bprocname\s*=\s*"([^"]+)"')
TOPIC = re.compile(r'\btopic_name\s*=\s*"([^"]+)"')
PUB = re.compile(r"\bpublisher_handle\s*=\s*(0x[0-9a-fA-F]+|\d+)")
SUB = re.compile(r"\bsubscription_handle\s*=\s*(0x[0-9a-fA-F]+|\d+)")
RMW_PUB = re.compile(r"\brmw_publisher_handle\s*=\s*(0x[0-9a-fA-F]+|\d+)")
RMW_SUB = re.compile(r"\brmw_subscription_handle\s*=\s*(0x[0-9a-fA-F]+|\d+)")
TAKEN_TRUE = re.compile(r"\btaken\s*=\s*1\b")
SOURCE_TS = re.compile(r"\\b(?:source_timestamp|timestamp)\\s*=\\s*[1-9][0-9]*\\b")
PUB_SOURCE_STAMP = re.compile(r"\\btimestamp\\s*=\\s*(\\d+)")
TAKE_SOURCE_STAMP = re.compile(r"\\bsource_timestamp\\s*=\\s*(\\d+)")
MAX_SCAN_RMW_TRACE_EVENTS = 12000


def _host_monotonic_from_trace_time(t, clock_anchor):
    """Approximate same-host monotonic using local trace time and anchor.

    Window intersection only, NOT an identical-message correlation.
    """
    if clock_anchor is None:
        return None
    sod=clock_anchor.get("local_seconds_of_day")
    if sod is None:
        wall=clock_anchor["wall_ns"]/1e9
        local=time.localtime(wall)
        sod=(local.tm_hour*3600 + local.tm_min*60 +
             local.tm_sec + (wall%1))
    delta=t-float(sod)
    if delta < -43200: delta+=86400
    if delta > 43200: delta-=86400
    return round(clock_anchor["monotonic_ns"]/1e9+delta,6)


def parse_events(lines, clock_anchor=None):
    rcl_owner = {"publish": {}, "take": {}}
    rmw_owner = {"publish": {}, "take": {}}
    counts = collections.Counter()
    streams = {"publish": {}, "take": {}}
    processes = {}
    parsed = 0
    rmw_scan_events = []
    rmw_scan_event_overflow = False
    for line in lines:
        match = EVENT.search(line)
        if not match:
            continue
        kind = match.group(1)
        counts[kind] += 1
        m_pid = PID.search(line)
        pid = m_pid.group(1) if m_pid else "UNKNOWN_PID"
        m_proc = PROC.search(line)
        if m_proc:
            processes[pid] = m_proc.group(1)
        if kind in ("rcl_publisher_init", "rcl_subscription_init"):
            direction = "publish" if kind == "rcl_publisher_init" else "take"
            m_topic = TOPIC.search(line)
            m_rcl = (PUB if direction == "publish" else SUB).search(line)
            m_rmw = (RMW_PUB if direction == "publish" else RMW_SUB).search(line)
            if m_topic and m_rcl:
                rcl_owner[direction][(pid,m_rcl.group(1))] = m_topic.group(1)
            if m_topic and m_rmw:
                rmw_owner[direction][(pid,m_rmw.group(1))] = m_topic.group(1)
            continue

        if kind == "rcl_take":
            # Official rcl_take provides only a message pointer.
            # Never assign these events to an arbitrary /scan subscription.
            continue
        if kind == "rmw_take" and not TAKEN_TRUE.search(line):
            continue

        direction = "publish" if kind in ("rcl_publish","rmw_publish") else "take"
        m_handle = (RMW_PUB if kind == "rmw_publish" else
                    RMW_SUB if kind == "rmw_take" else PUB).search(line)
        m_time = TIME.search(line)
        if not m_handle or not m_time:
            continue
        topic_owner = rmw_owner if kind.startswith("rmw_") else rcl_owner
        if topic_owner[direction].get((pid,m_handle.group(1))) not in ("scan","/scan"):
            continue
        hh,mm,ss,us = m_time.groups()
        t = int(hh)*3600+int(mm)*60+int(ss)+float("0."+us)
        parsed += 1
        if kind in ("rmw_publish", "rmw_take"):
            stamp_match = (PUB_SOURCE_STAMP if kind == "rmw_publish"
                           else TAKE_SOURCE_STAMP).search(line)
            stamp = int(stamp_match.group(1)) if stamp_match else 0
            if stamp > 0:
                if len(rmw_scan_events) < MAX_SCAN_RMW_TRACE_EVENTS:
                    rmw_scan_events.append((direction,pid,m_handle.group(1),stamp,t))
                else:
                    rmw_scan_event_overflow = True
        key = (pid,m_handle.group(1),kind)
        row = streams[direction].setdefault(key,{"last":None,"count":0,"max":0.0,
                                                 "max_window":None,"large":[],"source_ts":0})
        if row["last"] is not None:
            gap = t - row["last"]
            if gap < -80000:
                gap += 86400
            if gap >= 0:
                if gap > row["max"]:
                    row["max"] = gap
                    row["max_window"] = {
                        "gap_sec":round(gap,6),
                        "start_trace_time_of_day_sec":round(row["last"],6),
                        "end_trace_time_of_day_sec":round(t,6),
                        "start_host_monotonic_sec":_host_monotonic_from_trace_time(row["last"],clock_anchor),
                        "end_host_monotonic_sec":_host_monotonic_from_trace_time(t,clock_anchor),
                        "matched_same_laserscan_header_stamp":False}
                if gap > .3:
                    row["large"].append(round(gap,6))
                    row["large"].sort(reverse=True)
                    del row["large"][10:]
        row["last"] = t
        row["count"] += 1
        if kind.startswith("rmw_") and SOURCE_TS.search(line):
            row["source_ts"] += 1

    result_streams = []
    for direction,entries in streams.items():
        for (pid,handle,kind),row in entries.items():
            gap = round(row["max"],6)
            result_streams.append({
                "direction":direction,"pid":pid,"process":processes.get(pid),
                "event_type":kind,"topic":"/scan","count":row["count"],
                "max_consecutive_rcl_event_gap_sec":gap,
                "max_consecutive_trace_event_gap_sec":gap,
                "nonzero_source_timestamp_events":row["source_ts"],
                "max_gap_window":row["max_window"],
                "largest_gaps_over_300ms_sec":row["large"],
                "message_identity_correlated":False})
    result_streams.sort(key=lambda v:(v["direction"],v["pid"],v["event_type"]))
    # Publisher/take source timestamps come from RMW tracing, NOT a
    # LaserScan.header.stamp comparison. Repeated/missing timestamps must
    # never be treated as a unique causal message identity.
    publishes = collections.defaultdict(list)
    takes = collections.defaultdict(list)
    for direction,pid,handle,stamp,at in rmw_scan_events:
        if direction == "publish":
            publishes[stamp].append((pid,handle,at))
        else:
            takes[(pid,handle,stamp)].append(at)
    duplicate_pub = sum(len(v)-1 for v in publishes.values() if len(v)>1)
    matched = []
    unmatched = 0
    ambiguous = 0
    for (pid,handle,stamp),vals in takes.items():
        candidates=publishes.get(stamp,())
        if len(candidates)!=1 or len(vals)!=1:
            if len(candidates)>1 or len(vals)>1: ambiguous += 1
            else: unmatched += 1
            continue
        sent=candidates[0][2]
        latency=vals[0]-sent
        if latency < 0 or latency > 10:
            unmatched += 1
            continue
        matched.append((round(latency,6),pid,stamp,round(sent,6),round(vals[0],6)))
    worst=max(matched,key=lambda x:x[0]) if matched else None
    joined={
        "state":("SOURCE_TIMESTAMP_JOIN_ONLY"
                 if len(matched)>=2 and not rmw_scan_event_overflow
                 else "UNDETERMINED"),
        "matched_unique_pairs":len(matched),
        "max_publish_to_take_sec":worst[0] if worst else None,
        "max_pair":({"receiver_pid":worst[1], "source_timestamp":worst[2],
                     "publish_time_of_day_sec":worst[3], "take_time_of_day_sec":worst[4]}
                    if worst else None),
        "duplicate_publisher_source_timestamps":duplicate_pub,
        "ambiguous_subscription_timestamp_groups":ambiguous,
        "unmatched_subscription_timestamp_groups":unmatched,
        "bounded_capture_complete":not rmw_scan_event_overflow,
        "identical_laserscan_header_stamp_verified":False,
        "cm_internal_safety_ttl_verified":False,
        "scope":"single-host RMW source_timestamp correspondence, not DDS-only or safety cause"}
    return {
        "rmw_scan_source_stamp_join":joined,
        "status":"DIAGNOSTIC_ONLY_CAUSE_UNDETERMINED",
        "trace_event_counts":dict(sorted(counts.items())),
        "parseable_time_event_count":parsed,
        "scan_topic_streams":result_streams,
        "rmw_scan_publish_event_gap_measured":any(s["event_type"]=="rmw_publish" for s in result_streams),
        "rmw_scan_take_event_gap_measured":any(s["event_type"]=="rmw_take" for s in result_streams),
        "scan_bridge_publisher_identity_verified":False,
        "rcl_publish_to_rcl_take_same_message_join_verified":False,
        "publisher_rmw_cadence_measured":False,
        "cm_internal_receiver_ttl_verified":False,
        "owner_wsl2_l3_verified":False,
        "limitations":"RMW event intervals are per topic but NOT identical LaserScan source-message joins or DDS scheduling proof"}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--clock-anchor",type=Path)
    args=ap.parse_args()
    anchor=json.loads(args.clock_anchor.read_text()) if args.clock_anchor else None
    result=parse_events(sys.stdin,clock_anchor=anchor)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("D08_BRIDGE_RCL_TRACE_EVENTS="+json.dumps(result["trace_event_counts"],sort_keys=True))
    print("D08_BRIDGE_RCL_SCAN_TOPIC_STREAMS="+str(len(result["scan_topic_streams"])))
    print("D08_BRIDGE_RCL_TRACE_ROOT_CAUSE=UNDETERMINED")
if __name__=="__main__":main()
