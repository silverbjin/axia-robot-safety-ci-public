#!/usr/bin/env python3
"""Streaming, bounded summary of actual Jazzy ros2:rcl_* userspace LTTng events.

Not a per-LaserScan message join. PID/handle/topic inference requires init
tracepoints; without them report attribution unavailable, never DDS PASS.
"""
from __future__ import annotations
import argparse
import collections
import json
import re
import sys
from pathlib import Path

EVENT = re.compile(r"\bros2:(rcl_publisher_init|rcl_subscription_init|rcl_publish|rcl_take):")
TIME = re.compile(r"\[(?:(?:\d{4}-\d{2}-\d{2})\s+)?(\d\d):(\d\d):(\d\d)\.(\d+)\]")
PID = re.compile(r"\bvpid\s*=\s*(\d+)")
PROC = re.compile(r'\bprocname\s*=\s*"([^"]+)"')
TOPIC = re.compile(r'\btopic_name\s*=\s*"([^"]+)"')
PUB = re.compile(r"\bpublisher_handle\s*=\s*(0x[0-9a-fA-F]+|\d+)")
SUB = re.compile(r"\bsubscription_handle\s*=\s*(0x[0-9a-fA-F]+|\d+)")


def parse_events(lines):
    owners = {"publish": {}, "take": {}}
    event_counts = collections.Counter()
    scan_events = {"publish": collections.defaultdict(list),
                   "take": collections.defaultdict(list)}
    proc_names = {}
    parseable_time_count = 0
    for line in lines:
        match = EVENT.search(line)
        if not match:
            continue
        kind = match.group(1)
        event_counts[kind] += 1
        pid_match = PID.search(line)
        pid = pid_match.group(1) if pid_match else "UNKNOWN_PID"
        p = PROC.search(line)
        if p:
            proc_names[pid] = p.group(1)
        handle_match = PUB.search(line) if "publish" in kind else SUB.search(line)
        handle = handle_match.group(1) if handle_match else None
        if kind in ("rcl_publisher_init", "rcl_subscription_init"):
            tm = TOPIC.search(line)
            if handle and tm:
                owners["publish" if kind == "rcl_publisher_init" else "take"][(pid,handle)] = tm.group(1)
            continue
        tm = TIME.search(line)
        if not tm or handle is None:
            continue
        hours, mins, secs, decimals = tm.groups()
        t = int(hours)*3600 + int(mins)*60 + int(secs) + float("0."+decimals)
        parseable_time_count += 1
        direction = "publish" if kind == "rcl_publish" else "take"
        topic = owners[direction].get((pid,handle))
        if topic in ("scan", "/scan"):
            rows = scan_events[direction][(pid,handle)]
            if not rows:
                rows.extend([t, 0, 0.0, []])
            else:
                gap = t - rows[0]
                if gap < -80000:
                    gap += 86400
                rows[0] = t
                if gap >= 0:
                    rows[2] = max(rows[2],gap)
                    top = rows[3]
                    if gap > .3:
                        top.append(round(gap,6))
                        top.sort(reverse=True)
                        del top[10:]
            rows[1] += 1
    summaries = []
    for direction, entries in scan_events.items():
        for (pid,handle), row in entries.items():
            summaries.append({"direction":direction,"pid":pid,
                              "process":proc_names.get(pid),
                              "topic":"/scan","count":row[1],
                              "max_consecutive_rcl_event_gap_sec":round(row[2],6),
                              "largest_gaps_over_300ms_sec":row[3],
                              "message_identity_correlated":False})
    summaries.sort(key=lambda x:(x["direction"],x["pid"]))
    return {"status":"DIAGNOSTIC_ONLY_CAUSE_UNDETERMINED",
            "trace_event_counts":dict(sorted(event_counts.items())),
            "parseable_time_event_count":parseable_time_count,
            "scan_topic_streams":summaries,
            "scan_bridge_publisher_identity_verified":False,
            "rcl_publish_to_rcl_take_same_message_join_verified":False,
            "publisher_rmw_cadence_measured":False,
            "cm_internal_receiver_ttl_verified":False,
            "owner_wsl2_l3_verified":False,
            "limitations":"rcl init topic handles and rcl events only; not source-stamp message joins or RMW scheduling proofs"}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=parse_events(sys.stdin)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("D08_BRIDGE_RCL_TRACE_EVENTS="+json.dumps(result["trace_event_counts"],sort_keys=True))
    print("D08_BRIDGE_RCL_SCAN_TOPIC_STREAMS="+str(len(result["scan_topic_streams"])))
    print("D08_BRIDGE_RCL_TRACE_ROOT_CAUSE=UNDETERMINED")
if __name__=="__main__":main()
