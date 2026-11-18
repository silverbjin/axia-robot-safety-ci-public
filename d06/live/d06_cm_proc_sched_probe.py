#!/usr/bin/env python3
"""D06 real G07 CI: monitor official CM /proc scheduler timing READ-ONLY.

Pure Linux process sampling. Does not invoke ROS, issue Goal, set priorities,
signal safety processes, change timeouts, or export private raw evidence.
Read-only per-process schedstat is optional; unavailable => INCONCLUSIVE.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import signal
import time


def read_schedstat(path: Path):
    try:
        if path.is_symlink():
            return None
        values = path.read_text(encoding="ascii").split()
        if len(values) != 3:
            return None
        parsed = tuple(int(x) for x in values)
        if any(x < 0 for x in parsed):
            return None
        return parsed
    except (OSError, ValueError, UnicodeError):
        return None


def _enabled(proc: Path) -> bool:
    try:
        return (proc/"sys/kernel/sched_schedstats").read_text().strip() == "1"
    except OSError:
        return False


def _find_cm(proc: Path, partition: str, domain: str):
    # Match EXACT official executable and isolated CI session environment.
    # Never target unrelated ROS processes or any user's Owner WSL2 session.
    for folder in proc.iterdir():
        if not folder.name.isdigit():
            continue
        try:
            if (folder/"exe").resolve().name not in (
                    "collision_monitor", "collision_monitor_node"):
                continue
            env=(folder/"environ").read_bytes().split(b"\0")
            if (("GZ_PARTITION="+partition).encode() not in env
                    or ("ROS_DOMAIN_ID="+domain).encode() not in env):
                continue
            return folder/"schedstat"
        except (OSError, ValueError):
            continue
    return None


def _num(x):
    return type(x) in (int,float) and math.isfinite(x)


def analyze_gap(events, samples, *, schedstat_enabled: bool):
    """First actual CM publisher gap, and scheduler counter change nearby.

    A runqueue wait counter is an attribution CANDIDATE, never callback proof.
    Missing kernel stats or missing witness samples remain explicitly unknown.
    """
    output = {
        "schema":"axia.d06.g07_first_cm_rmw_schedstat_v1",
        "status":"NO_ACTUAL_GOAL_OR_CM_RMW_PROOF",
        "first_cm_source_gap_ms":None,
        "upstream_publications_inside_gap":0,
        "scheduler_status":"SCHEDSTAT_UNAVAILABLE" if not schedstat_enabled
                           else "SCHEDSTAT_WINDOW_MISSING",
        "scheduler_wait_growth_ms":None,
        "scheduler_cpu_runtime_growth_ms":None,
        "scheduler_wait_overlaps_gap_candidate":False,
        "cm_callback_processing_delay_proven":False,
        "safety_pass":False,
        "owner_l3_accepted":False,
        "certified_estop":False,
    }
    if not isinstance(events,list) or not isinstance(samples,list):
        return output
    goals=[row["t"] for row in events
           if isinstance(row,dict) and row.get("kind")=="owner_goal_published"
           and _num(row.get("t"))]
    if len(goals)!=1:
        return output
    cm=sorted((e for e in events if isinstance(e,dict)
               and e.get("kind")=="pre_guard"
               and _num(e.get("t")) and e["t"]>=goals[0]
               and type(e.get("rmw_source_ns")) is int
               and type(e.get("rmw_publication_seq")) is int),
              key=lambda e:e["t"])
    first=None
    for a,b in zip(cm,cm[1:]):
        gap=(b["rmw_source_ns"]-a["rmw_source_ns"])/1e9
        if b["rmw_publication_seq"]-a["rmw_publication_seq"] != 1:
            continue
        if gap > .15 and 0 < b["t"]-a["t"] < 2:
            first=(a,b,gap)
            break
    if first is None:
        return output
    a,b,gap=first
    output["status"]="HOLD_CM_RMW_PUBLISH_GAP_OVER_150MS"
    output["first_cm_source_gap_ms"]=round(gap*1000,6)
    output["upstream_publications_inside_gap"]=sum(
        1 for row in events
        if isinstance(row,dict) and row.get("kind")=="supervised"
        and type(row.get("rmw_source_ns")) is int
        and a["rmw_source_ns"]<row["rmw_source_ns"]<b["rmw_source_ns"]
    )
    if not schedstat_enabled:
        return output
    valid=[s for s in samples if isinstance(s,dict)
           and all(_num(s.get(k)) for k in ("t","runtime_ns","wait_ns","timeslices"))]
    before=[s for s in valid if 0 <= a["t"]-s["t"] <= .065]
    after=[s for s in valid if 0 <= s["t"]-b["t"] <= .065]
    if not before or not after:
        return output
    x=max(before,key=lambda s:s["t"])
    y=min(after,key=lambda s:s["t"])
    waited=y["wait_ns"]-x["wait_ns"]
    cpu=y["runtime_ns"]-x["runtime_ns"]
    if waited<0 or cpu<0:
        return output
    output["scheduler_status"]="SCHEDSTAT_WINDOW_MEASURED"
    output["scheduler_wait_growth_ms"]=round(waited/1e6,3)
    output["scheduler_cpu_runtime_growth_ms"]=round(cpu/1e6,3)
    output["scheduler_wait_overlaps_gap_candidate"]=waited/1e9 >= .5*gap
    return output


_STOP = False
def _stop(_signo, _frame):
    global _STOP
    _STOP = True


def sample(proc: Path, output: Path, *, partition: str, domain: str,
           duration: float, interval: float):
    """Lower-impact 25ms read-only sampling, limited to CI's exact CM PID."""
    global _STOP
    _STOP = False
    signal.signal(signal.SIGTERM,_stop)
    signal.signal(signal.SIGINT,_stop)
    started=time.monotonic()
    next_lookup=started
    statpath=None
    enabled=_enabled(proc)
    found=False
    count=0
    output.parent.mkdir(parents=True,exist_ok=True)
    # File is private to the GitHub Actions job; never upload.
    with output.open("x",encoding="utf-8",buffering=64*1024) as stream:
        stream.write(json.dumps({"kind":"meta","schedstat_enabled":enabled})+"\n")
        while not _STOP and time.monotonic()-started<duration:
            now=time.monotonic()
            if statpath is None and now>=next_lookup:
                statpath=_find_cm(proc,partition,domain)
                next_lookup=now+.5
            if statpath is not None:
                snap=read_schedstat(statpath)
                if snap is None:
                    statpath=None
                else:
                    found=True
                    stream.write(json.dumps({
                        "t":now,"runtime_ns":snap[0],"wait_ns":snap[1],
                        "timeslices":snap[2]},sort_keys=True)+"\n")
                    count+=1
            time.sleep(interval)
    print("D06_CM_SCHEDSTAT_SAMPLER_EXIT "
          + json.dumps({"process_found":found,"samples":count,
                        "schedstat_enabled":enabled},sort_keys=True))
    return 0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("sample")
    s.add_argument("--output",type=Path,required=True)
    s.add_argument("--proc",type=Path,default=Path("/proc"))
    s.add_argument("--partition",default="axia_p2_ci_moving_83")
    s.add_argument("--domain",default="83")
    s.add_argument("--duration",type=float,default=180.)
    s.add_argument("--interval",type=float,default=.025)
    a=sub.add_parser("analyze")
    a.add_argument("--events",type=Path,required=True)
    a.add_argument("--samples",type=Path,required=True)
    args=p.parse_args()
    if args.cmd=="sample":
        if not (0<args.duration<=900 and .015<=args.interval<=.1):
            return 3
        return sample(args.proc,args.output,partition=args.partition,
                      domain=args.domain,duration=args.duration,
                      interval=args.interval)
    try:
        if args.samples.is_symlink() or args.events.is_symlink():
            raise ValueError("symlink")
        events=[json.loads(line) for line in
                args.events.read_text(encoding="utf-8").splitlines() if line.strip()]
        rows=[json.loads(line) for line in
              args.samples.read_text(encoding="utf-8").splitlines() if line.strip()]
        meta=next((r for r in rows if r.get("kind")=="meta"),{})
        result=analyze_gap(events,[r for r in rows if r.get("kind")!="meta"],
                           schedstat_enabled=meta.get("schedstat_enabled") is True)
    except (OSError,ValueError,TypeError,KeyError):
        result=analyze_gap([],[],schedstat_enabled=False)
    print("D06_G07_CM_SCHED_FIRST_RMW_GAP "
          +json.dumps(result,sort_keys=True))
    # Diagnostic is not an acceptance gate; original real L2 oracle is.
    return 0


if __name__=="__main__":
    raise SystemExit(main())
