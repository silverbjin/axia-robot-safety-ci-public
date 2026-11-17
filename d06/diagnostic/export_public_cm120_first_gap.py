"""Task01 public CI allowlisted *timing-only* evidence from sealed ROS data.

Never exports private instructor source, raw ROS messages, sensor coordinates,
frames, callback pointers, private file paths, or unfiltered LTTng/TF logs.
Times are independent offsets from source SYSTEM and observer MONOTONIC
anchors, not proof of their clock-domain equivalence. No Goal/release grant.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from d06.live.g07_cycle05_cm_callback_window import _first_pair
from d06.live.g07_cycle31_cm_topic_callback_identity import resolve_cm_cmdvel_handles
from d06.diagnostic.analyze_first_cm_tf import TF_LINE, TF_SLEEP_LINE

SCHEMA = "axia.g07.cm120.public_first_gap_v1"
SHA = re.compile(r"[0-9a-f]{40}\Z")
RUN = re.compile(r"[0-9]{5,15}\Z")
READY = "AXIA_CM120_TF_DIAG_CM_LIBRARY_LOADED"
MAX_SLEEPS = 64
MAX_TFS = 40


def _clock(anchors):
    if not isinstance(anchors, dict):
        raise ValueError("PUBLIC_CLOCK_ANCHOR_INVALID")
    a, b = anchors.get("start"), anchors.get("end")
    if not isinstance(a, dict) or not isinstance(b, dict):
        raise ValueError("PUBLIC_CLOCK_ANCHOR_MISSING")
    for x in (a, b):
        for k in ("mono_ns", "wall_ns"):
            if type(x.get(k)) is not int or not 0 < x[k] < 10**20:
                raise ValueError("PUBLIC_CLOCK_ANCHOR_FIELD_INVALID")
    if b["mono_ns"] <= a["mono_ns"] or b["wall_ns"] <= a["wall_ns"]:
        raise ValueError("PUBLIC_CLOCK_ANCHOR_ORDER_INVALID")
    drift = (b["wall_ns"]-b["mono_ns"])-(a["wall_ns"]-a["mono_ns"])
    if abs(drift) >= 50_000_000:
        raise ValueError("PUBLIC_CLOCK_ANCHOR_DRIFT_INVALID")
    return a, b


def export_sanitized(observer, trace, tf_lines, anchors, *, run_id, public_sha, clock_rows=None):
    if not isinstance(run_id, str) or not RUN.fullmatch(run_id):
        raise ValueError("PUBLIC_RUN_ID_INVALID")
    if not isinstance(public_sha, str) or not SHA.fullmatch(public_sha):
        raise ValueError("PUBLIC_SHA_INVALID")
    if (not isinstance(observer, list) or not isinstance(trace, list)
            or not isinstance(tf_lines, list) or len(observer) > 100000
            or len(trace) > 150000 or len(tf_lines) > 20000):
        raise ValueError("PUBLIC_INPUT_UNBOUNDED")
    if not all(isinstance(x, str) and len(x) <= 320 for x in tf_lines):
        raise ValueError("PUBLIC_TF_LINE_OVERSIZE")
    start, end = _clock(anchors)
    out = dict(
        schema=SCHEMA, run_id=run_id, public_source_sha=public_sha,
        status="FIRST_RMW_SOURCE_GAP_NOT_REPRODUCED",
        original_source_modified=False, goal_authorized_by_exporter=False,
        source_publication_to_monotonic_alignment_proven=False,
        tf_wait_proven=False, scheduler_wait_proven=False,
        root_cause_proven=False, gate_c_authorized=False,
        cm120_release_pass=False, owner_wsl2_accepted=False,
        certified_estop=False,
        first_gap=None,
        clock_anchor=dict(
            wall_minus_mono_start_ns=start["wall_ns"]-start["mono_ns"],
            wall_minus_mono_end_ns=end["wall_ns"]-end["mono_ns"],
            sender_clock_domain_proven=False),
        tf_calls=dict(count=0, durations_ms=[]),
        tf_sleep=dict(count=0, spans=[], coverage_proven=False))
    pair = _first_pair(observer)
    if pair is None:
        return out
    a, b, source_ms = pair
    if any(type(e.get(k)) is not int for e in (a,b)
           for k in ("rmw_source_ns", "rmw_publication_seq")):
        raise ValueError("PUBLIC_RMW_SOURCE_FIELDS_UNVERIFIED")
    if (not math.isfinite(source_ms) or source_ms<120
            or b["rmw_publication_seq"] != a["rmw_publication_seq"]+1):
        raise ValueError("PUBLIC_RMW_SOURCE_PAIR_INVALID")
    pair_start_ns=round(a["t"]*1e9)
    pair_end_ns=round(b["t"]*1e9)
    def normalized(e, seq):
        recv=e.get("rmw_received_ns")
        return dict(
            seq_relative=seq,
            source_from_wall_start_anchor_ns=e["rmw_source_ns"]-start["wall_ns"],
            observer_from_mono_start_anchor_ns=round(e["t"]*1e9)-start["mono_ns"],
            received_from_wall_start_anchor_ns=(
                recv-start["wall_ns"]
                if type(recv) is int and 0<recv<10**20 else None))
    out["first_gap"] = dict(
        rmw_source_gap_ns=b["rmw_source_ns"]-a["rmw_source_ns"],
        observer_gap_ns=pair_end_ns-pair_start_ns,
        pairs=[normalized(a,0),normalized(b,1)])
    out["status"]="FIRST_RMW_SOURCE_GAP_SELECTED_CAUSE_UNPROVEN"

    # Optional read-only /clock subscriber. Only bounded numeric relative
    # samples may enter the public artifact. Existing raw-free v1 consumers
    # remain byte-identical when clock_rows is omitted. This probe is NOT
    # the official tf2 Buffer's internal clock or source SYSTEM epoch.
    if clock_rows is not None:
        from d06.diagnostic.firstgap_clock_progress import summarize
        out["clock_progress"]=summarize(
            clock_rows,pair_start_ns,pair_end_ns)

    pids={e.get("vpid") for e in trace if isinstance(e,dict)
          and e.get("name")=="ros2:rcl_subscription_init"
          and e.get("procname") in ("collision_monitor","collision_monit")
          and e.get("topic_name")=="/cmd_vel_supervised"
          and type(e.get("vpid")) is int}
    if len(pids)!=1:
        out["status"]="CM_CALLBACK_OWNER_UNVERIFIED_HOLD"
        return out
    pid=next(iter(pids))
    try:
        handles,meta=resolve_cm_cmdvel_handles(trace,cm_pid=pid)
    except (ValueError, KeyError, TypeError):
        out["status"]="CM_CALLBACK_HANDLE_UNVERIFIED_HOLD"
        return out
    if len(handles)!=1 or meta.get("topic_matched_subscriptions")!=1:
        out["status"]="CM_CALLBACK_HANDLE_UNVERIFIED_HOLD"
        return out
    handle=next(iter(handles))
    tids={e.get("vtid") for e in trace if isinstance(e,dict)
          and e.get("vpid")==pid
          and e.get("name") in ("ros2:callback_start","ros2:callback_end")
          and str(e.get("callback"))==handle and type(e.get("vtid")) is int}
    if not tids:
        out["status"]="CM_CALLBACK_THREAD_UNVERIFIED_HOLD"
        return out

    tf_calls, sleeps=[],[]
    mapped=False
    for line in tf_lines:
        if line.strip()==READY:
            mapped=True
            continue
        match=TF_LINE.fullmatch(line.strip())
        if match:
            vals=match.groups()
            p,tid,t0,t1=map(int,vals[:4])
            if t1<t0:
                raise ValueError("PUBLIC_TF_INTERVAL_INVALID")
            if p==pid and tid in tids and t1>=pair_start_ns-200_000_000 and (
                    t0<=pair_end_ns+200_000_000):
                tf_calls.append((p,tid,t0,t1,
                    int(vals[12]) if vals[12] is not None else None,
                    int(vals[4])))
            continue
        match=TF_SLEEP_LINE.fullmatch(line.strip())
        if match:
            p,tid,t0,t1,req,rc=map(int,match.groups())
            if t1<t0 or req<0:
                raise ValueError("PUBLIC_TF_SLEEP_INTERVAL_INVALID")
            if p==pid and tid in tids and t1>=pair_start_ns-200_000_000 and (
                    t0<=pair_end_ns+200_000_000):
                sleeps.append((p,tid,t0,t1,req,rc))
            continue
        raise ValueError("PUBLIC_TF_RAW_LINE_UNEXPECTED")
    if not mapped:
        out["status"]="CM_TF_PRELOAD_NOT_CONFIRMED_HOLD"
        return out
    if len(tf_calls)>MAX_TFS or len(sleeps)>MAX_SLEEPS:
        raise ValueError("PUBLIC_TIMING_SPAN_LIMIT_EXCEEDED")

    # Exact same invocation containment, by original CM PID+TID before
    # projection to a numeric public time-relative artifact. Keep call
    # start/end rather than the previous ambiguous list of durations only.
    # No frame/pose, raw ROS, pointer, PID or TID leaves the sealed runner.
    spans=[]
    per_call=[[] for _ in tf_calls]
    for p,tid,t0,t1,req,rc in sleeps:
        owners=[i for i,(cp,ct,ta,tb,sc,cpu) in enumerate(tf_calls)
                if cp==p and ct==tid and ta<=t0<=t1<=tb]
        if len(owners)!=1:
            out["status"]="TF_SLEEP_SPAN_CALL_LINK_UNVERIFIED_HOLD"
            return out
        per_call[owners[0]].append((t0,t1,req,rc))
        spans.append(dict(
            start_rel_observer_ns=t0-pair_start_ns,
            end_rel_observer_ns=t1-pair_start_ns,
            request_ns=req,rc=rc))
    spans.sort(key=lambda x:x["start_rel_observer_ns"])
    if any(l["end_rel_observer_ns"]>r["start_rel_observer_ns"]
           for l,r in zip(spans,spans[1:])):
        out["status"]="TF_SLEEP_OVERLAP_UNVERIFIED_HOLD"
        return out
    if any(l[3]>r[2] for l,r in
           zip(sorted(tf_calls,key=lambda c:c[2]),
               sorted(tf_calls,key=lambda c:c[2])[1:])):
        out["status"]="TF_CALL_INTERVALS_OVERLAP_HOLD"
        return out

    call_spans=[]
    for (p,tid,t0,t1,declared,cpu),inside in zip(tf_calls,per_call):
        count=len(inside)
        request=sum(x[2] for x in inside)
        sleep_wall=sum(x[1]-x[0] for x in inside)
        valid=(declared is not None and count==declared
               and all(x[3]==0 and x[1]-x[0]>=x[2] for x in inside)
               and sleep_wall<=t1-t0 and cpu>=0 and cpu<=t1-t0)
        call_spans.append(dict(
            start_rel_observer_ns=t0-pair_start_ns,
            end_rel_observer_ns=t1-pair_start_ns,
            thread_cpu_ns=cpu,
            sleep_count_declared=declared,
            sleep_count_observed=count,
            sleep_request_ns=request,
            sleep_wall_ns=sleep_wall,
            coverage_complete=valid))

    out["tf_calls"]=dict(
        count=len(tf_calls),
        durations_ms=[round((t[3]-t[2])/1e6,6) for t in tf_calls],
        spans=call_spans)
    out["tf_sleep"]=dict(
        count=len(spans),spans=spans,
        coverage_proven=(bool(call_spans)
                         and all(c["coverage_complete"] for c in call_spans)))
    return out

def write_allowlisted_json(out,path):
    if not isinstance(out,dict) or out.get("schema")!=SCHEMA:
        raise ValueError("PUBLIC_OUTPUT_SCHEMA_UNVERIFIED")
    contents=json.dumps(out,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n"
    if len(contents.encode("utf-8"))>=32768:
        raise ValueError("PUBLIC_OUTPUT_OVERSIZE")
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(contents,encoding="utf-8")
    return p
