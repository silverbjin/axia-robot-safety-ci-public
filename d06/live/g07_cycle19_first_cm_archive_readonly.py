#!/usr/bin/env python3
"""Read-only first WSL2 CM 150ms breach versus native STOP RPC attribution.

No ROS, Gazebo, Goal, /proc writes, trial reset, or public raw upload.
Only original Owner TAR members are read in memory with SHA256 verification.
RMW system-time source/receive intervals and monotonic callback/STOP RPC
windows are different clock domains; NEVER subtract them from each other.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import tarfile

PRIVATE_SHA="01d45d46b6eb6a05b1bd313d73f1fc3549575545"
ORIGINAL_SHA="c2557e3269c5cb3f56d1842f8d39bcdc5d6ab0055180911fc492a5bc84a1f672"
NAME="p2-l3-owner-A9IwJNZJ"
CM_TTL=0.15
LIMIT_BYTES=20*1024*1024

def _number(v):
    return type(v) in (int,float) and math.isfinite(v) and v>=0

def _hash(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def _member(tar,name,limit=LIMIT_BYTES):
    members=[m for m in tar.getmembers() if m.name==f"{NAME}/{name}"]
    if len(members)!=1 or not members[0].isfile() or not 0<members[0].size<=limit:
        raise ValueError("ORIGINAL_MEMBER_MISSING_DUPLICATE_OR_TOO_LARGE")
    f=tar.extractfile(members[0])
    if f is None:
        raise ValueError("ORIGINAL_MEMBER_NOT_FILE")
    data=f.read(limit+1)
    if len(data)>limit:
        raise ValueError("ORIGINAL_MEMBER_READ_LIMIT")
    return data

def _load(archive,expected_sha):
    if (archive.is_symlink() or not archive.is_file() or
        archive.name not in (NAME+".tar.gz",ORIGINAL_SHA) or
        expected_sha!=ORIGINAL_SHA or _hash(archive)!=expected_sha):
        raise ValueError("ORIGINAL_ARCHIVE_HASH_OR_NAME_MISMATCH")
    try:
        with tarfile.open(archive,"r:gz") as t:
            source=_member(t,"source.sha",128).decode("ascii").strip()
            if source!=PRIVATE_SHA:
                raise ValueError("ORIGINAL_OWNER_SOURCE_SHA_MISMATCH")
            live=json.loads(_member(t,"G07/live/ci_moving_goal_result.json").decode("utf-8"))
            events=_member(t,"G07/live/actual_ros_events.jsonl").decode("utf-8").splitlines()
    except (tarfile.TarError,OSError,UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError("ORIGINAL_ARCHIVE_UNREADABLE_"+type(exc).__name__) from exc
    if not isinstance(live,dict):
        raise ValueError("ORIGINAL_LIVE_RESULT_NOT_OBJECT")
    if len(events)>250000:
        raise ValueError("ORIGINAL_EVENTS_COUNT_UNBOUNDED")
    e=[]
    for line in events:
        try:
            j=json.loads(line)
        except (ValueError,UnicodeError):
            raise ValueError("ORIGINAL_EVENT_JSON_INVALID")
        if not isinstance(j,dict):
            raise ValueError("ORIGINAL_EVENT_TYPE_INVALID")
        e.append(j)
    return live,e

def analyze_original(live,events):
    hold={"schema":"axia.g07.owner_first_cm_rpc_attribution_v1",
          "status":"ORIGINAL_FIRST_GAP_NOT_REPRODUCED",
          "owner_l3_accepted":False,"certified_estop":False,
          "owner_goal_authorized":False,"no_ros_no_goal":True,
          "cm_internal_callback_cause_proven":False,
          "host_clock_step_excluded":False}
    if not isinstance(live,dict) or not isinstance(events,list):
        return {**hold,"status":"ORIGINAL_RESULT_UNVERIFIED"}
    latch=live.get("first_guard_latch")
    if not isinstance(latch,dict) or latch.get("reason")!="UPSTREAM_STALE_AFTER_MOTION":
        return {**hold,"status":"ORIGINAL_GUARD_FIRST_LATCH_UNVERIFIED"}
    cmage=latch.get("cm_age_sec")
    tick=latch.get("tick_monotonic")
    if not (_number(cmage) and cmage>CM_TTL and _number(tick)):
        return {**hold,"status":"ORIGINAL_GUARD_TTL_NOT_ESTABLISHED"}
    start=next((x.get("t") for x in events
                if x.get("kind")=="owner_goal_published" and _number(x.get("t"))),None)
    if start is None:
        return {**hold,"status":"ORIGINAL_GOAL_START_NOT_ESTABLISHED",
                "first_guard_cm_age_ms":round(cmage*1000,6)}
    streams={"pre_guard":[],"supervised":[]}
    for e in events:
        kind=e.get("kind")
        if kind not in streams:
            continue
        callback=e.get("t")
        src=e.get("rmw_source_ns")
        recv=e.get("rmw_received_ns")
        seq=e.get("rmw_publication_seq")
        if not (_number(callback) and callback>=start and type(src) is int
                and type(recv) is int and type(seq) is int and src>0 and recv>=src):
            continue
        streams[kind].append({"t":callback,"src":src,"recv":recv,"seq":seq})
    cm=streams["pre_guard"]
    up=streams["supervised"]
    if len(cm)<2:
        return {**hold,"status":"ORIGINAL_CM_RMW_SOURCE_MISSING",
                "first_guard_cm_age_ms":round(cmage*1000,6)}
    # Do not misclassify a host SYSTEM clock step as a publisher stall.
    for stream in (cm,up):
        if any(b["src"]<=a["src"] or b["seq"]<=a["seq"]
               for a,b in zip(stream,stream[1:])):
            return {**hold,"status":"RMW_SOURCE_SEQUENCE_OR_CLOCK_DISCONTINUITY"}
    first=next(((a,b) for a,b in zip(cm,cm[1:])
                if (b["src"]-a["src"])/1e9>=CM_TTL),None)
    if first is None:
        return {**hold,"status":"ORIGINAL_FIRST_150MS_CM_GAP_NOT_IN_EVENTS",
                "first_guard_cm_age_ms":round(cmage*1000,6)}
    a,b=first
    inside=[x for x in up if a["src"]<x["src"]<b["src"]]
    source_gap=(b["src"]-a["src"])/1e6
    receive_gap=(b["recv"]-a["recv"])/1e6
    observer_gap=(b["t"]-a["t"])*1000
    if any(x<0 for x in (source_gap,receive_gap,observer_gap)):
        return {**hold,"status":"RMW_DOMAIN_INVALID"}
    covers=[a["src"]]+[x["src"] for x in inside]+[b["src"]]
    upmax=max((r-l)/1e6 for l,r in zip(covers,covers[1:]))
    # All following overlap comparisons use monotonic timestamps ONLY.
    rpc=live.get("stop_native_rpc_monotonic_window")
    rpc_overlap=None
    rpc_duration_ms=None
    if (isinstance(rpc,dict) and _number(rpc.get("started_at"))
        and _number(rpc.get("ended_at"))
        and rpc["started_at"]<=rpc["ended_at"]):
        rpc_duration_ms=round((rpc["ended_at"]-rpc["started_at"])*1000,6)
        rpc_overlap=(max(a["t"],rpc["started_at"])<
                     min(b["t"],rpc["ended_at"]))
    first_guard_inside=(a["t"]<=tick<=b["t"])
    wait=live.get("cm_scheduler_native_stop_window")
    sample=live.get("cm_native_rpc_thread_state")
    return {**hold,
        "status":"OWNER_FIRST_CM_GAP_CONFIRMED_CAUSE_PENDING",
        "first_guard_cm_age_ms":round(cmage*1000,6),
        "first_guard_hard_ttl_ms":150,
        "first_cm_rmw_source_gap_ms":round(source_gap,6),
        "first_cm_rmw_receive_gap_ms":round(receive_gap,6),
        "first_cm_observer_callback_gap_ms":round(observer_gap,6),
        "upstream_publications_inside_gap":len(inside),
        "upstream_max_gap_inside_ms":round(upmax,6),
        "first_guard_tick_inside_same_monotonic_cm_gap":first_guard_inside,
        "native_stop_rpc_duration_ms":rpc_duration_ms,
        "native_stop_rpc_overlaps_first_cm_gap_candidate":rpc_overlap,
        "cm_scheduler_native_stop_window_available":isinstance(wait,dict)
            and wait.get("available") is True,
        "cm_scheduler_native_stop_window_attribution":
            wait.get("attribution") if isinstance(wait,dict) else None,
        "cm_rpc_thread_sampler_available":isinstance(sample,dict)
            and sample.get("available") is True,
        "evidence_scope":"ONE_ORIGINAL_OWNER_GOAL_RETAINED_RAW_READONLY",
        "raw_events_exported":False,
        "causal_attribution":"UNDETERMINED_CM_PROCESSING_VS_TF_VS_SCHEDULER",
    }

def inspect(archive:Path, expected_sha=ORIGINAL_SHA):
    live,events=_load(archive,expected_sha)
    return analyze_original(live,events)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",required=True,type=Path)
    p.add_argument("--expected-sha256",default=ORIGINAL_SHA)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    try:
        result=inspect(args.archive,args.expected_sha256)
        if args.output.is_symlink() or args.output.exists():
            raise ValueError("OUTPUT_ALREADY_EXISTS_OR_SYMLINK")
        with args.output.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=True,indent=2,sort_keys=True)
            f.write("\n")
        args.output.chmod(0o600)
    except (OSError,ValueError,tarfile.TarError) as exc:
        print("AXIA_G07_FIRST_CM_OWNER_ORIGINAL_UNAVAILABLE_OR_INVALID "+
              type(exc).__name__+":"+str(exc),file=sys.stderr)
        print("AXIA_MVP_DEMO_ACCEPTED=HOLD",flush=True)
        return 3
    print("AXIA_G07_FIRST_CM_ORIGINAL_READONLY "+
          json.dumps(result,sort_keys=True),flush=True)
    print("AXIA_G07_FIRST_CM_SANITIZED_RESULT="+str(args.output))
    print("AXIA_G07_NO_ROS_NO_GOAL_OWNER_L3_NOT_ACCEPTED")
    print("AXIA_MVP_DEMO_ACCEPTED=HOLD")
    return 0 if result["status"]=="OWNER_FIRST_CM_GAP_CONFIRMED_CAUSE_PENDING" else 3

if __name__=="__main__":
    raise SystemExit(main())
