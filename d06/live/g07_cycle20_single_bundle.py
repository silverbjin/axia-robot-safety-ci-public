#!/usr/bin/env python3
"""AXIA G07 Cycle20 ONE sanitized Owner evidence archive (NO ROS/NO Goal).

Read original SHA256-verified G11 TAR, retain only whitelisted numeric timing,
first Guard safety transition and bounded scheduler aggregates. A single tar.gz
is the ONLY output. Do not include ROS bags, private source, user path, ID,
Goal UUID, full ROS message payloads or raw logs.

RMW source/receive clocks are HOST SYSTEM time. Callback and STOP RPC are
MONOTONIC. Compare gaps within each domain, never subtract absolute clocks.
Context/environment probes describe CURRENT host, not historical scheduler.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import secrets
import sys
import tarfile

if __package__ in (None,""):
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from d06.live import g07_cycle19_first_cm_archive_readonly as previous

KIND=("pre_guard","supervised","scan","odom","clock","guard","source","supervisor")
FILES=("00_manifest.json","01_first_boundary.json","02_event_window.json",
       "03_cm_scheduler.json","04_environment.json","SHA256SUMS")
MAX_EVENTS_PER_KIND=16
MAX_MEMBER_BYTES=200000
FIRST_TTL=0.150

def _num(v):
    return type(v) in (int,float) and math.isfinite(v) and v>=0

def _json(payload):
    return (json.dumps(payload,sort_keys=True,indent=2,ensure_ascii=True,
                       allow_nan=False)+"\n").encode("ascii")

def _only_numbers(obj, names):
    obj=obj if type(obj) is dict else {}
    return {key:obj.get(key) if _num(obj.get(key)) else None for key in names}

def _first_gap(events,live):
    start=next((e.get("t") for e in events
                if e.get("kind")=="owner_goal_published" and _num(e.get("t"))),None)
    if start is None:
        raise ValueError("OWNER_GOAL_MARKER_NOT_VERIFIED")
    rows=[]
    for e in events:
        if e.get("kind")!="pre_guard":
            continue
        if not _num(e.get("t")) or e["t"]<start:
            continue
        if (type(e.get("rmw_source_ns")) is not int or
            type(e.get("rmw_received_ns")) is not int or
            type(e.get("rmw_publication_seq")) is not int):
            continue
        if (e["rmw_source_ns"]<=0 or
            e["rmw_received_ns"]<e["rmw_source_ns"]):
            continue
        rows.append(e)
    if len(rows)<2 or any(
        b["rmw_source_ns"]<=a["rmw_source_ns"] or
        b["rmw_publication_seq"]<=a["rmw_publication_seq"]
        for a,b in zip(rows,rows[1:])):
        raise ValueError("OWNER_CM_SOURCE_OR_CLOCK_DISCONTINUITY")
    for a,b in zip(rows,rows[1:]):
        if (b["rmw_source_ns"]-a["rmw_source_ns"])/1e9>=FIRST_TTL:
            return a,b
    raise ValueError("OWNER_FIRST_CM_HARD_GAP_NOT_IN_ORIGINAL")

def _environment():
    # The CURRENT WSL2 host state is context only; not a sample from the
    # past moving Goal. Do not include hostname, user, env var values, MAC.
    version=None
    p=Path("/etc/os-release")
    try:
        if p.is_file():
            pairs={}
            for line in p.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.startswith("#"):
                    k,v=line.split("=",1)
                    if k in ("ID","VERSION_ID"):
                        pairs[k]=v.strip('"')
            version=pairs
    except (OSError,UnicodeError):
        pass
    try:
        cpus=len(os.sched_getaffinity(0))
    except (AttributeError,OSError):
        cpus=None
    def textfile(path,max_chars=100):
        try:
            t=Path(path).read_text(encoding="ascii").strip()
            return t if len(t)<=max_chars and all(ch.isprintable() for ch in t) else None
        except (OSError,UnicodeError):
            return None
    pressure=textfile("/proc/pressure/cpu",240)
    # Avoid exporting full /proc strings. Extract only avg10 numeric value.
    pressure10=None
    if pressure:
        import re
        m=re.search(r"^some\s+avg10=(\d+(?:\.\d+)?)",pressure,re.M)
        if m:
            pressure10=float(m.group(1))
    cgroup_cpu=textfile("/sys/fs/cgroup/cpu.max",80)
    if cgroup_cpu is not None and not all(
        part=="max" or part.isdecimal() for part in cgroup_cpu.split()):
        cgroup_cpu=None
    return {
        "schema":"axia.g07.owner_current_environment_context_v1",
        "historic_goal_environment_proven":False,
        "capture_mode":"CURRENT_HOST_READONLY_NOT_HISTORIC",
        "os_release":version,
        "kernel_wsl_family":"WSL" if "microsoft" in platform.release().lower()
                            else "NON_WSL_OR_UNVERIFIED",
        "allowed_cpu_count_current":cpus,
        "cgroup_cpu_max_current":cgroup_cpu,
        "cpu_pressure_avg10_current":pressure10,
        "wslg_display_present_now":bool(os.getenv("DISPLAY")),
        "wslg_wayland_present_now":bool(os.getenv("WAYLAND_DISPLAY")),
        "ros2_initialized_by_this_tool":False,
        "gazebo_initialized_by_this_tool":False,
        "owner_goal_sent_by_this_tool":False,
    }

def _window(events,a,b):
    left=a["t"]; right=b["t"]; lo=left-.25; hi=right+.25
    source_base=a["rmw_source_ns"]
    out={}
    for kind in KIND:
        matching=[e for e in events if e.get("kind")==kind
                  and _num(e.get("t")) and lo<=e["t"]<=hi]
        middle=(left+right)/2
        matching=sorted(sorted(matching,key=lambda e:abs(e["t"]-middle))
                        [:MAX_EVENTS_PER_KIND],key=lambda e:e["t"])
        seq0=next((e.get("rmw_publication_seq") for e in matching
                   if type(e.get("rmw_publication_seq")) is int),None)
        out[kind]=[]
        for e in matching:
            def offset(key):
                v=e.get(key)
                return round((v-source_base)/1e6,6) if type(v) is int and v>=0 else None
            seq=e.get("rmw_publication_seq")
            out[kind].append({
                "callback_offset_ms":round((e["t"]-left)*1000,6),
                "rmw_source_offset_ms":offset("rmw_source_ns"),
                "rmw_receive_offset_ms":offset("rmw_received_ns"),
                "publication_sequence_relative":(seq-seq0 if
                    type(seq) is int and type(seq0) is int else None),
            })
    return {
        "schema":"axia.g07.owner_first_cm_bounded_window_v1",
        "time_origin":"FIRST_CM_CALLBACK_AND_SOURCE_NORMALIZED",
        "rmw_source_and_receive_share_host_system_domain":True,
        "callback_and_rpc_share_monotonic_domain":True,
        "different_clock_domains_absolute_subtraction_forbidden":True,
        "time_window_ms":{"before_first_callback":250,"after_second_callback":250},
        "max_records_per_kind":MAX_EVENTS_PER_KIND,
        "events_by_kind":out,
        "no_ros_messages_exported":True,
        "raw_absolute_timestamps_exported":False,
    }

def _first_boundary(live,events,a,b,existing):
    latch=live.get("first_guard_latch") if type(live)==dict else None
    age=latch.get("cm_age_sec") if type(latch)==dict else None
    tick=latch.get("tick_monotonic") if type(latch)==dict else None
    if (type(latch) is not dict or latch.get("reason")!="UPSTREAM_STALE_AFTER_MOTION"
        or not _num(age) or age<=FIRST_TTL or not _num(tick)):
        raise ValueError("FIRST_GUARD_INTERNAL_CM_TTL_NOT_PROVEN")
    src_gap=(b["rmw_source_ns"]-a["rmw_source_ns"])/1e6
    recv_gap=(b["rmw_received_ns"]-a["rmw_received_ns"])/1e6
    cb_gap=(b["t"]-a["t"])*1000
    if any(x<0 for x in (recv_gap,cb_gap)):
        raise ValueError("FIRST_CM_RECEIVE_OR_CALLBACK_CLOCK_UNVERIFIED")
    inside=[e for e in events if e.get("kind")=="supervised"
            and type(e.get("rmw_source_ns")) is int
            and a["rmw_source_ns"]<e["rmw_source_ns"]<b["rmw_source_ns"]]
    inside.sort(key=lambda e:e["rmw_source_ns"])
    anchors=[a["rmw_source_ns"]]+[e["rmw_source_ns"] for e in inside]+[b["rmw_source_ns"]]
    coverage=max((r-l)/1e6 for l,r in zip(anchors,anchors[1:]))
    rpc=live.get("stop_native_rpc_monotonic_window")
    relation="NATIVE_STOP_RPC_MONOTONIC_UNAVAILABLE"
    overlap=None; rpc_ms=None; distance=None
    if (type(rpc) is dict and _num(rpc.get("started_at"))
        and _num(rpc.get("ended_at"))
        and rpc["started_at"]<=rpc["ended_at"]):
        start=rpc["started_at"];end=rpc["ended_at"]
        rpc_ms=round((end-start)*1000,6)
        overlap=max(a["t"],start)<min(b["t"],end)
        if overlap:
            relation="FIRST_GAP_OVERLAPS_RPC_CANDIDATE"
            distance=0.0
        elif b["t"]<=start:
            relation="FIRST_GAP_BEFORE_RPC"
            distance=round((start-b["t"])*1000,6)
        else:
            relation="FIRST_GAP_AFTER_RPC"
            distance=round((a["t"]-end)*1000,6)
    return {
        "schema":"axia.g07.owner_first_cm_breach_summary_v1",
        "status":"OWNER_FIRST_GUARD_TTL_BREACH_CAUSE_PENDING",
        "guard_first_transition":"UPSTREAM_STALE_AFTER_MOTION",
        "first_guard_cm_age_ms":round(age*1000,6),
        "first_guard_cm_hard_ttl_ms":150,
        "first_guard_tick_inside_cm_callback_interval":a["t"]<=tick<=b["t"],
        "first_cm_rmw_source_gap_ms":round(src_gap,6),
        "first_cm_rmw_receive_gap_ms":round(recv_gap,6),
        "first_cm_observer_callback_gap_ms":round(cb_gap,6),
        "receive_gap_minus_source_gap_ms":round(recv_gap-src_gap,6),
        "callback_gap_minus_source_gap_ms":round(cb_gap-src_gap,6),
        "cm_publication_sequence_gap":b["rmw_publication_seq"]-a["rmw_publication_seq"],
        "upstream_publications_inside_gap":len(inside),
        "upstream_max_coverage_gap_ms":round(coverage,6),
        "native_stop_rpc_duration_ms":rpc_ms,
        "native_stop_rpc_overlaps_first_cm_gap":overlap,
        "native_stop_rpc_temporal_relation":relation,
        "native_stop_rpc_nearest_gap_distance_ms":distance,
        # Existing summary explicitly leaves this unresolved.
        "host_clock_step_excluded":False,
        "cm_internal_cause_proven":False,
        "source_gap_cause":"UNDETERMINED_CM_TF_CALLBACK_SCHEDULING_OR_RMW",
        "previous_cycle19_first_gap_confirmed":
            existing.get("status")=="OWNER_FIRST_CM_GAP_CONFIRMED_CAUSE_PENDING",
        "owner_release_allowed":False,
    }

def _scheduler(live):
    a=live.get("cm_scheduler_native_stop_window")
    b=live.get("cm_native_rpc_thread_state")
    a=a if type(a)==dict else {}
    b=b if type(b)==dict else {}
    def goodlabel(value,allowed):
        return value if type(value) is str and value in allowed else "UNVERIFIED"
    classes=b.get("wait_classes")
    classes=classes if type(classes)==dict else {}
    kinds=("futex","epoll","sleep","other")
    return {
        "schema":"axia.g07.owner_historic_cm_scheduler_aggregate_v1",
        "native_stop_window":{
            "available":a.get("available") is True,
            "run_sec":a.get("run_sec") if _num(a.get("run_sec")) else None,
            "wait_sec":a.get("wait_sec") if _num(a.get("wait_sec")) else None,
            "thread_count":a.get("thread_count") if type(a.get("thread_count")) is int
                                                 and 0<=a["thread_count"]<=512 else None,
            "attribution":goodlabel(a.get("attribution"),{
                "CM_SCHEDSTAT_UNAVAILABLE",
                "CM_SCHEDULER_WAIT_CANDIDATE",
                "CM_EXECUTION_BUSY_CANDIDATE",
                "CM_SCHEDULER_VS_EXECUTION_UNDETERMINED"}),
        },
        "rpc_sampler":{
            "available":b.get("available") is True,
            **_only_numbers(b,("samples","valid_samples","runnable_samples",
                               "all_sleeping_samples","thread_count_max")),
            "wait_classes":{k:(classes.get(k) if type(classes.get(k)) is int
                             and 0<=classes[k]<=100000 else None) for k in kinds},
        },
        "native_rpc_sample_not_evidence_of_first_gap_when_disjoint":True,
        "historical_scheduler_internal_cause_proven":False,
        "no_thread_identifiers_or_raw_proc_exported":True,
    }

def _validate_existing(root,expected_sha):
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("BUNDLE_OUTDIR_UNTRUSTED")
    if type(expected_sha) is not str or len(expected_sha)!=64:
        raise ValueError("ORIGINAL_SHA_NOT_VERIFIED")

def create_bundle(archive:Path, out_dir:Path, *,expected_sha=previous.ORIGINAL_SHA) -> Path:
    archive=Path(archive);out_dir=Path(out_dir)
    _validate_existing(out_dir,expected_sha)
    live,events=previous._load(archive,expected_sha)
    prior=previous.analyze_original(live,events)
    if prior.get("status")!="OWNER_FIRST_CM_GAP_CONFIRMED_CAUSE_PENDING":
        raise ValueError("OWNER_FIRST_CM_GAP_NOT_GROUNDED")
    a,b=_first_gap(events,live)
    first=_first_boundary(live,events,a,b,prior)
    win=_window(events,a,b)
    sched=_scheduler(live)
    environment=_environment()
    manifest={
        "schema":"axia.g07.single_owner_sanitized_evidence_v1",
        "status":"FIRST_GUARD_CM_TTL_BREACH_CAUSE_PENDING",
        "created_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "original_archive_sha256":expected_sha,
        "private_source_sha":previous.PRIVATE_SHA,
        "original_archive_verified":True,
        "diagnostic_mode":"READONLY_NO_ROS_NO_GOAL",
        "no_ros_no_goal":True,
        "owner_l3_accepted":False,"certified_estop":False,
        "owner_release_allowed":False,"private_original_included":False,
        "original_bag_or_source_included":False,
        "time_domains_separately_compared":True,
        "host_clock_step_excluded":False,
        "native_rpc_is_first_cm_gap_cause_proven":False,
        "field_runtime_fix_verified":False,
    }
    data={
        "00_manifest.json":_json(manifest),
        "01_first_boundary.json":_json(first),
        "02_event_window.json":_json(win),
        "03_cm_scheduler.json":_json(sched),
        "04_environment.json":_json(environment),
    }
    assert all(len(x)<MAX_MEMBER_BYTES for x in data.values())
    checks="".join(hashlib.sha256(data[name]).hexdigest()+"  "+name+"\n"
                   for name in sorted(data))
    data["SHA256SUMS"]=checks.encode("ascii")
    if not out_dir.exists():
        out_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
    out_dir.chmod(0o700)
    name=("g07-cycle20-owner-evidence-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
          +"-"+secrets.token_hex(4)+".tar.gz")
    path=out_dir/name
    try:
        with path.open("xb") as out:
            os.fchmod(out.fileno(),0o600)
            with tarfile.open(fileobj=out,mode="w:gz") as tar:
                for key in FILES:
                    bts=data[key]
                    info=tarfile.TarInfo(key)
                    info.mode=0o600
                    info.mtime=0
                    info.size=len(bts)
                    tar.addfile(info,io.BytesIO(bts))
        read_bundle_manifest(path)
    except Exception:
        if path.exists() and not path.is_symlink():
            path.unlink()
        raise
    return path

def read_bundle_manifest(path:Path):
    with tarfile.open(path,"r:gz") as t:
        members=t.getmembers()
        if len(members)!=len(FILES) or set(m.name for m in members)!=set(FILES):
            raise ValueError("BUNDLE_MEMBER_SET_INVALID")
        if any(not m.isfile() or m.size>MAX_MEMBER_BYTES for m in members):
            raise ValueError("BUNDLE_MEMBER_KIND_OR_SIZE_INVALID")
        raw={}
        for m in members:
            f=t.extractfile(m)
            if f is None: raise ValueError("BUNDLE_MEMBER_UNREADABLE")
            raw[m.name]=f.read(MAX_MEMBER_BYTES+1)
        lines=raw["SHA256SUMS"].decode("ascii").splitlines()
        parsed={}
        for line in lines:
            bits=line.split(maxsplit=1)
            if len(bits)!=2 or bits[1] in parsed:
                raise ValueError("BUNDLE_SHA256SUMS_FORMAT_BAD")
            parsed[bits[1]]=bits[0]
        if set(parsed)!=set(FILES)-{"SHA256SUMS"} or any(
            hashlib.sha256(raw[k]).hexdigest()!=parsed[k] for k in parsed):
            raise ValueError("BUNDLE_MEMBER_SHA256_MISMATCH")
        manifest=json.loads(raw["00_manifest.json"])
        if (manifest.get("schema")!="axia.g07.single_owner_sanitized_evidence_v1"
            or manifest.get("owner_release_allowed") is not False
            or manifest.get("private_original_included") is not False):
            raise ValueError("BUNDLE_MANIFEST_FAIL_CLOSED")
        return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",required=True,type=Path)
    p.add_argument("--expected-sha256",default=previous.ORIGINAL_SHA)
    p.add_argument("--out-dir",required=True,type=Path)
    args=p.parse_args()
    try:
        bundle=create_bundle(args.archive,args.out_dir,
                             expected_sha=args.expected_sha256)
    except (OSError,ValueError,tarfile.TarError,AssertionError) as e:
        print("AXIA_G07_CYCLE20_BUNDLE_BLOCKED "+type(e).__name__+":"+str(e),
              file=sys.stderr)
        print("AXIA_MVP_DEMO_ACCEPTED=HOLD")
        return 3
    print("AXIA_G07_CYCLE20_ONE_SANITIZED_BUNDLE_SHA256="+
          hashlib.sha256(bundle.read_bytes()).hexdigest())
    print("AXIA_G07_CYCLE20_UPLOAD_ONLY_THIS_ARCHIVE="+str(bundle))
    print("AXIA_G07_CYCLE20_READONLY_NO_ROS_NO_GOAL_NO_RAW_ORIGINAL")
    print("AXIA_MVP_DEMO_ACCEPTED=HOLD")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
