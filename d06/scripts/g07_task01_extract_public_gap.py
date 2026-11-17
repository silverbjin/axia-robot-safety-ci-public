#!/usr/bin/env python3
"""Sealed-runner-only adapter: raw private ROS/TF/LTTng -> public allowlist JSON.

The *only* files allowed to leave the runner are first_gap_sanitized.json and
SHA256SUMS.txt. Never upload raw ROS, private source, TF log or LTTng data.
This script never starts or authorizes an actual Goal. Even a good artifact
is diagnostics only, not an accepted CM120 or certified E-Stop.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from d06.diagnostic.export_public_cm120_first_gap import (
    SCHEMA, export_sanitized, write_allowlisted_json,
)
from d06.diagnostic.s0_cm_diag_readiness import select_exact_cm_callbacks

EVENTS = {
    "ros2:rcl_subscription_init",
    "ros2:rclcpp_subscription_init",
    "ros2:rclcpp_subscription_callback_added",
    "ros2:callback_start",
    "ros2:callback_end",
}


def exact_trace_rows(trace_dir):
    import bt2  # system Python in pinned ROS2 Jazzy container
    def rows():
        for msg in bt2.TraceCollectionMessageIterator(str(trace_dir)):
            if not isinstance(msg, bt2._EventMessageConst):
                continue
            event=msg.event
            if event.name not in EVENTS:
                continue
            r={"name":event.name}
            c=event.common_context_field
            p=event.payload_field
            for key in ("vpid", "vtid"):
                if c is not None and key in c:
                    r[key]=int(c[key])
            if c is not None and "procname" in c:
                r["procname"]=str(c["procname"])
            for key in ("subscription_handle","subscription","callback","topic_name"):
                if p is not None and key in p:
                    r[key]=str(p[key])
            snap=msg.default_clock_snapshot
            if snap is not None:
                r["timestamp_ns"]=snap.ns_from_origin
            yield r
    result=select_exact_cm_callbacks(rows())
    if result.get("status")!="EXACT_CM_CALLBACK_FILTER_READY":
        raise ValueError("EXACT_CM_CALLBACK_FILTER_NOT_READY")
    return result["rows"]


def _narrow_first_observer_window_tf(observer, tf_lines):
    """Only the first source-gap-selected OBSERVER interval +/-200ms.

    Original TF raw remains local. Discard unrelated same-session polls
    before the native exporter applies its 20k line cap. This is NOT
    source SYSTEM -> MONOTONIC sender alignment or causal proof.
    """
    from d06.live.g07_cycle05_cm_callback_window import _first_pair
    from d06.diagnostic.analyze_first_cm_tf import (
        TF_LINE, TF_SLEEP_LINE, TF_CLOCK_LINE, TF_AVAIL_LINE)
    from d06.diagnostic.export_public_cm120_first_gap import READY
    if not isinstance(tf_lines, list) or len(tf_lines) > 100000:
        raise ValueError("PUBLIC_TF_RAW_LINE_LIMIT")
    pair = _first_pair(observer)
    # No actual source breach: never select a TF callback by proximity.
    selected=[]
    if pair is None:
        return selected
    a,b,_=pair
    begin=round(a["t"]*1e9)-200_000_000
    end=round(b["t"]*1e9)+200_000_000
    for row in tf_lines:
        if not isinstance(row,str) or len(row)>320:
            raise ValueError("PUBLIC_TF_LINE_OVERSIZE")
        line=row.strip()
        if line==READY:
            selected.append(line)
            continue
        m=TF_LINE.fullmatch(line)
        if m:
            start,stop=(int(m.group(3)),int(m.group(4)))
        else:
            m=TF_SLEEP_LINE.fullmatch(line)
            if m:
                start,stop=(int(m.group(3)),int(m.group(4)))
            else:
                m=TF_CLOCK_LINE.fullmatch(line)
                if m:
                    start=stop=int(m.group(3))
                else:
                    m=TF_AVAIL_LINE.fullmatch(line)
                    if m:
                        start,stop=(int(m.group(3)),int(m.group(6)))
                    else:
                        raise ValueError("PUBLIC_TF_RAW_LINE_UNEXPECTED")
        if start<=end and stop>=begin:
            selected.append(line)
            if len(selected)>20000:
                raise ValueError("PUBLIC_FIRST_GAP_TF_WINDOW_STILL_UNBOUNDED")
    return selected


def _fallback(status, run_id, public_sha):
    # Fixed strings and fixed SHA validated by caller; no raw exceptions leak.
    return {
        "schema":SCHEMA, "status":status,
        "run_id":run_id,"public_source_sha":public_sha,
        "root_cause_proven":False,"gate_c_authorized":False,
        "cm120_release_pass":False,"owner_wsl2_accepted":False,
        "source_publication_to_monotonic_alignment_proven":False,
        "original_source_modified":False,
        "certified_estop":False,
    }


def extract(*, events, trace_dir, tf_file, anchors_dir,
            out, run_id, public_sha, clock_file=None):
    if not (isinstance(run_id,str) and run_id.isdigit() and
            5<=len(run_id)<=15 and isinstance(public_sha,str) and
            len(public_sha)==40 and all(c in "0123456789abcdef" for c in public_sha)):
        raise ValueError("INVALID_PUBLIC_RUN_OR_SOURCE_SHA")
    # A failed raw CTF join must not erase the independent first RMW
    # publisher-source INTERVAL observed by Jazzy MessageInfo. Preserve
    # ONLY two durations; no PID, raw topic, pose or SYSTEM absolute epoch.
    observer=None
    failure_stage="RAW_INPUT_METADATA"
    try:
        event_path=Path(events)
        trace_path=Path(trace_dir)
        tf_path=Path(tf_file)
        anchor_path=Path(anchors_dir)
        if not (event_path.is_file() and tf_path.is_file() and trace_path.is_dir()
                and (anchor_path/"start_anchor.json").is_file()
                and (anchor_path/"end_anchor.json").is_file()):
            data=_fallback("RAW_EVIDENCE_NOT_CREATED_HOLD",run_id,public_sha)
        else:
            if event_path.stat().st_size > 12_000_000 or tf_path.stat().st_size > 3_000_000:
                raise ValueError("PRIVATE_INPUT_OVERSIZE")
            failure_stage="OBSERVER_RMW_JSONL_PARSE"
            observer=[json.loads(x) for x in event_path.read_text().splitlines()]
            failure_stage="NATIVE_TF_DIAGNOSTIC_ROWS"
            tf_lines=tf_path.read_text().splitlines()
            failure_stage="NARROW_FIRST_OBSERVER_TF_WINDOW"
            tf_lines=_narrow_first_observer_window_tf(observer,tf_lines)
            anchors={
                "start":json.loads((anchor_path/"start_anchor.json").read_text()),
                "end":json.loads((anchor_path/"end_anchor.json").read_text()),
            }
            failure_stage="NATIVE_LTTNG_CALLBACK_ROWS"
            trace=exact_trace_rows(trace_path)
            # Raw /clock MONOTONIC receive and ROS SIM clock stamps remain
            # in sealed runner only. Missing/incomplete probe => HOLD, not
            # a fabricated negative scheduler/TF-causality result.
            clock_rows=None
            if clock_file is not None:
                cp=Path(clock_file)
                if cp.is_file() and cp.stat().st_size<=2_500_000:
                    clock_rows=[json.loads(v) for v in
                                cp.read_text().splitlines()]
                else:
                    clock_rows=[]
            failure_stage="EXACT_SOURCE_TF_ALLOWLIST_JOIN"
            data=export_sanitized(observer,trace,tf_lines,anchors,
                    run_id=run_id,public_sha=public_sha,
                    clock_rows=clock_rows)
    except (OSError,ValueError,KeyError,TypeError,ImportError,RuntimeError):
        data=_fallback("PUBLIC_EVIDENCE_EXTRACTION_UNVERIFIED_HOLD",
                       run_id,public_sha)
        data["failure_stage"]=failure_stage  # fixed internal enum, no exception text
        # In contrast with TF/Callback causality, this *independent* RMW
        # source interval needs only MessageInfo sequence and receive rows.
        # The original publisher clock domain remains UNVERIFIED.
        try:
            from d06.live.g07_cycle05_cm_callback_window import _first_pair
            pair=_first_pair(observer)
            if pair is not None:
                a,b,_=pair
                source=b["rmw_source_ns"]-a["rmw_source_ns"]
                received=round((b["t"]-a["t"])*1_000_000_000)
                if (type(source) is int and 120_000_000<=source<1_000_000_000
                        and type(received) is int
                        and 0<received<1_000_000_000):
                    data["first_gap"]={
                        "rmw_source_gap_ns":source,
                        "observer_gap_ns":received}
                    data["first_gap_provenance"]=(
                        "OBSERVER_RMW_ONLY_EXACT_CM_CALLBACK_UNVERIFIED")
        except (ValueError,KeyError,TypeError,IndexError,OverflowError):
            pass
    p=write_allowlisted_json(data,out)
    return data["status"],p


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--events",required=True)
    ap.add_argument("--trace-dir",required=True)
    ap.add_argument("--tf-file",required=True)
    ap.add_argument("--anchors-dir",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--public-sha",required=True)
    ap.add_argument("--clock-file",default=None)
    v=ap.parse_args()
    status,p=extract(events=v.events, trace_dir=v.trace_dir,
        tf_file=v.tf_file, anchors_dir=v.anchors_dir, out=v.out,
        run_id=v.run_id,public_sha=v.public_sha,
        clock_file=v.clock_file)
    # No exception contents, filenames, private source paths or raw ROS text.
    print("AXIA_G07_TASK01_PUBLIC_TIMING_EVIDENCE_STATUS="+status)
    print("AXIA_G07_TASK01_PUBLIC_TIMING_EVIDENCE_BYTES="+str(p.stat().st_size))
    print("AXIA_G07_TASK01_PUBLIC_EVIDENCE_NOT_RELEASE_NOT_ESTOP")


if __name__=="__main__":
    main()
