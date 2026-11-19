#!/usr/bin/env python3
"""CV2U3T4v: read-only, low-overhead WSL2 CPU scheduler + Scan correlation.

Never modifies ROS, CM, Guard, Gazebo or the owner's acceptance thresholds.
No ROS subscription is added; the original Owner rosbag supplies scan/clock.
Only stdlib. Hypervisor preemption is UNCONFIRMED from guest stats alone.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import statistics
import struct
import sys
import tempfile
import time


def read_text(path):
    try:
        return Path(path).read_text(errors="replace")
    except (OSError, UnicodeError):
        return ""


def guest_system():
    cpu = read_text("/proc/stat").splitlines()
    words = cpu[0].split() if cpu else []
    psi_cpu = read_text("/proc/pressure/cpu")
    psi_mem = read_text("/proc/pressure/memory")
    def total(s):
        m = re.search(r"some\s+[^\n]*?total=(\d+)", s)
        return int(m.group(1)) if m else None
    return {
        "steal_jiffies": int(words[8]) if len(words)>8 else None,
        "proc_stat_total_jiffies": sum(int(n) for n in words[1:11]) if len(words)>8 else None,
        "cpu_pressure_some_us": total(psi_cpu),
        "memory_pressure_some_us": total(psi_mem),
    }


def target_roles():
    """Names/PIDs only; no command lines or private paths in evidence."""
    found={}
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            cmd=(item/"cmdline").read_bytes().replace(b"\0",b" ").decode(errors="ignore")
            comm=read_text(item/"comm").strip()
        except OSError:
            continue
        role=None
        if re.search(r"\bgz\s+sim\b",cmd) and " -s " in (" "+cmd+" "):
            role="gazebo_server"
        elif "ros_gz_bridge" in cmd or comm=="parameter_bridge":
            role="ros_gz_bridge"
        elif "collision_monitor" in cmd:
            role="collision_monitor"
        elif "p2_base_guard" in cmd:
            role="base_guard"
        elif "safety_supervisor" in cmd:
            role="safety_supervisor"
        elif comm in ("controller_server","bt_navigator","amcl","map_server","lifecycle_manager"):
            role=comm
        if role and sum(1 for x in found.values() if x==role)<3:
            found[int(item.name)]=role
    return found


def process_sched(pids):
    out=[]
    for pid,role in pids.items():
        # This is thread-group LEADER schedstat only. Multi-thread Gazebo
        # physics/renderer worker wait may not be visible here.
        words=read_text(f"/proc/{pid}/schedstat").split()
        if len(words)<3:
            continue
        try:
            run,wait,slices=(int(v) for v in words[:3])
        except ValueError:
            continue
        if run==0 and wait==0 and slices==0:
            continue
        out.append({"pid":pid,"role":role,"sched_run_ns":run,
                    "sched_wait_ns":wait,"timeslices":slices})
    return out


def monitor(output, stop, interval_ms):
    if not 20<=interval_ms<=100:
        raise ValueError("interval must be 20..100ms")
    out=Path(output)
    out.parent.mkdir(parents=True,exist_ok=True)
    stop=Path(stop)
    period=interval_ms/1000.0
    prior=time.monotonic_ns()
    known={}
    last_refresh=0
    index=0
    with out.open("w",encoding="utf8",buffering=1) as f:
        while not stop.exists():
            now=time.monotonic_ns()
            epoch=time.time_ns()
            delta=(now-prior)/1_000_000
            prior=now
            row={"mono_ns":now,"realtime_ns":epoch,"gap_ms":round(delta,4),
                 "overshoot_ms":round(max(0,delta-interval_ms),4)}
            if hasattr(time,"CLOCK_BOOTTIME"):
                row["boottime_ns"]=time.clock_gettime_ns(time.CLOCK_BOOTTIME)
            if now-last_refresh>=1_000_000_000:
                known=target_roles()
                last_refresh=now
            if index%5==0:
                row.update(guest_system())
                row["proc_sched"]=process_sched(known)
            f.write(json.dumps(row,separators=(",",":"))+"\n")
            index+=1
            time.sleep(period)
    print("AXIA_G07_WSL2_GUEST_SCHED_MONITOR_STOPPED samples="+str(index),flush=True)


def jsonlines(path):
    rows=[]
    if not path or not Path(path).is_file():
        return rows
    with Path(path).open(errors="replace") as f:
        for line in f:
            try:
                obj=json.loads(line)
                if isinstance(obj,dict):
                    rows.append(obj)
            except (ValueError,TypeError):
                continue
    return rows


def first_violation(result):
    item=result.get("first_timing_violation",{})
    if not isinstance(item,dict):
        return None
    at=item.get("first_violation_at")
    if type(at) not in (float,int) or not math.isfinite(at):
        return None
    return item


def scan_result(owner_console):
    text=read_text(owner_console)
    m=re.search(r"AXIA_G07_TASK04_LOCAL_EVIDENCE=([^\s]+)",text)
    if not m:
        return None,None,None
    root=Path(m.group(1))
    candidates=list(root.glob("native/**/ci_moving_goal_result.json"))
    for path in candidates:
        try:
            result=json.loads(path.read_text())
            return root,result,first_violation(result)
        except (OSError,ValueError):
            pass
    return root,None,None


def local_bag_clock(root,violation,anchor_rows):
    """Read-only CDR: /scan header stamp vs receipt, /clock sim progress.

    Only near first violation; WSL2 realtime clock jumps can invalidate
    epoch alignment, hence diagnostics are NOT a safety gate.
    """
    if not root or not violation or not anchor_rows:
        return {"status":"NOT_AVAILABLE"}
    at=violation["first_violation_at"]
    nearest=min(anchor_rows,key=lambda r:abs(r["mono_ns"]/1e9-at))
    offset_sec=abs(nearest["mono_ns"]/1e9-at)
    if offset_sec>2:
        return {"status":"EVENT_OUTSIDE_GUEST_TRACE","nearest_mono_delta_sec":offset_sec}
    event_wall_ns=int(nearest["realtime_ns"] + (at-nearest["mono_ns"]/1e9)*1e9)
    files=list(root.glob("native/**/*.db3"))
    if not files:
        return {"status":"ORIGINAL_SQLITE_NOT_FOUND"}
    def stamp(b):
        if len(b)<12 or b[0:2] not in (b"\x00\x01",b"\x01\x00"):
            return None
        prefix="<" if b[0:2]==b"\x00\x01" else ">"
        sec,nsec=struct.unpack_from(prefix+"iI",b,4)
        return sec+nsec/1e9 if nsec<1_000_000_000 else None
    try:
        db=sqlite3.connect(f"file:{files[0]}?mode=ro",uri=True,timeout=3)
        try:
            topics={name:idx for idx,name in db.execute("SELECT id,name FROM topics")}
            samples={}
            for topic in ("/scan","/safety/scan","/clock"):
                if topic not in topics:
                    continue
                low=event_wall_ns-2_000_000_000
                high=event_wall_ns+2_000_000_000
                samples[topic]=[(t,stamp(b)) for t,b in db.execute(
                    "SELECT timestamp,data FROM messages WHERE topic_id=? "
                    "AND timestamp BETWEEN ? AND ? ORDER BY timestamp",
                    (topics[topic],low,high))]
        finally:
            db.close()
    except (sqlite3.Error,OSError):
        return {"status":"SQLITE_READ_FAILURE"}
    report={"status":"OBSERVED_NOT_PROOF_OF_HYPERVISOR_PREEMPTION"}
    for topic in ("/scan","/safety/scan"):
        rows=samples.get(topic,[])
        candidates=[]
        for (t,a),(nt,b) in zip(rows,rows[1:]):
            if a is not None and b is not None:
                candidates.append((1000*(nt-t)/1e9,1000*(b-a),t,nt))
        if candidates:
            wall_ms,sim_ms,t,nt=max(candidates,key=lambda x:x[0])
            report[topic]={"max_wall_gap_ms":round(wall_ms,3),
                          "matching_sim_stamp_gap_ms":round(sim_ms,3),
                          "at_wall_epoch_ns":t,"until_wall_epoch_ns":nt}
    scan=report.get("/scan")
    clock=samples.get("/clock",[])
    if scan and clock:
        inside=[(t,c) for t,c in clock if
                scan["at_wall_epoch_ns"]<=t<=scan["until_wall_epoch_ns"]
                and c is not None]
        if len(inside)>=2:
            t0,sim0=inside[0];t1,sim1=inside[-1]
            wall=(t1-t0)/1e9
            report["clock"]={"local_wall_sec":round(wall,6),
                             "local_sim_sec":round(sim1-sim0,6),
                             "local_rtf":round((sim1-sim0)/wall,4) if wall>0 else None}
    return report


def evaluate(rows,hosts,root,result,violation):
    wake=[r.get("gap_ms",0) for r in rows if isinstance(r.get("gap_ms"),(int,float))]
    max_gap=max(wake,default=0)
    target_t=violation.get("first_violation_at") if violation else None
    matching=([] if target_t is None else
        [r for r in rows if abs(r["mono_ns"]/1e9-target_t)<=.6])
    near_max=max((r.get("gap_ms",0) for r in matching),default=None)
    # Same wall-time alignment as the original ROS bag, not a run-wide
    # maximum that could occur minutes away from the actual Scan violation.
    event_epoch_ms=None
    if target_t is not None and rows:
        anchor=min(rows,key=lambda r:abs(r["mono_ns"]/1e9-target_t))
        if abs(anchor["mono_ns"]/1e9-target_t)<=2:
            event_epoch_ms=(anchor["realtime_ns"]/1e6+
                            1000*(target_t-anchor["mono_ns"]/1e9))
    nearby_hosts=([h for h in hosts
                   if isinstance(h.get("epoch_ms"),(int,float))
                   and abs(h["epoch_ms"]-event_epoch_ms)<=600]
                  if event_epoch_ms is not None else [])
    nearby_host_gaps=[h["gap_ms"] for h in nearby_hosts
                      if isinstance(h.get("gap_ms"),(int,float))]
    nearby_cpu=[h["host_cpu_pct"] for h in nearby_hosts
                if isinstance(h.get("host_cpu_pct"),(int,float))]
    sampled=[r for r in rows if "steal_jiffies" in r and r["steal_jiffies"] is not None]
    steal=(sampled[-1]["steal_jiffies"]-sampled[0]["steal_jiffies"]
           if len(sampled)>1 else None)
    psi=[r["cpu_pressure_some_us"] for r in rows
         if isinstance(r.get("cpu_pressure_some_us"),int)]
    psi_delta=psi[-1]-psi[0] if len(psi)>1 else None
    host_wakes=[h.get("gap_ms") for h in hosts
                if isinstance(h.get("gap_ms"),(int,float))]
    report={"status":"HYPOTHESIS_REQUIRES_CORRELATED_EVIDENCE",
      "hypervisor_cpu_preemption":"HOST_CPU_PREEMPTION_UNCONFIRMED",
      "first_timing_violation":violation,
      "monitor_sample_count":len(rows),
      "guest_monotonic_max_gap_ms":round(max_gap,3),
      "guest_monotonic_gaps_over_100ms":sum(x>100 for x in wake),
      "guest_monotonic_max_gap_near_violation_ms":near_max,
      "steal_jiffies_delta":steal,
      "steal_zero_does_not_exclude_host_pause":True,
      "cpu_pressure_some_us_delta":psi_delta,
      "windows_host_max_gap_near_violation_ms":max(nearby_host_gaps,default=None),
      "windows_host_cpu_peak_pct_near_violation":max(nearby_cpu,default=None),
      "windows_host_sample_count":len(hosts),
      "windows_host_max_sample_gap_ms":max(host_wakes,default=None),
      "windows_host_monitor_available":len(hosts)>3,
      "process_schedstat_is_thread_leader_only":True,
      "realtime_clock_step_not_excluded":True,
      "safety_ttl_modified":False,
      "original_goal_unchanged":True}
    if violation and root:
        report["original_bag_clock"]=local_bag_clock(root,violation,rows)
    return report


def analyze(args):
    rows=jsonlines(args.guest)
    hosts=jsonlines(args.host)
    root,result,violation=scan_result(args.owner_console)
    report=evaluate(rows,hosts,root,result,violation)
    Path(args.output).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("AXIA_G07_CV2_FIRST_TIMING_VIOLATION="+json.dumps(violation,ensure_ascii=False))
    print("AXIA_G07_CV2_GUEST_GAP_MAX_MS="+str(report["guest_monotonic_max_gap_ms"]))
    print("AXIA_G07_CV2_NEAR_SCAN_GAP_MS="+str(report["guest_monotonic_max_gap_near_violation_ms"]))
    print("AXIA_G07_CV2_WINDOWS_HOST_MONITOR="+("AVAILABLE" if hosts else "UNAVAILABLE"))
    print("AXIA_G07_CV2_HYPERVISOR_CPU_PREEMPTION=HOST_CPU_PREEMPTION_UNCONFIRMED")
    print("AXIA_G07_CV2_SAFETY_TTL_UNCHANGED=true")


def selftest():
    rows=[{"mono_ns":int(t*1e9),"realtime_ns":int((1800000000+t)*1e9),
           "gap_ms":g,"steal_jiffies":0,
           "cpu_pressure_some_us":0}
          for t,g in [(10,40),(10.04,40),(10.39,350),(10.43,40)]]
    v={"channel":"scan","first_violation_at":10.39,
       "first_violation_sec":.35,"limit_sec":.3}
    result=evaluate(rows,[],None,{},v)
    assert result["guest_monotonic_max_gap_ms"]>=350
    assert result["guest_monotonic_max_gap_near_violation_ms"]>=350
    assert result["steal_jiffies_delta"]==0
    assert result["hypervisor_cpu_preemption"]=="HOST_CPU_PREEMPTION_UNCONFIRMED"
    assert result["safety_ttl_modified"] is False
    print("AXIA_G07_CV2_SIMULATED_350MS_GAP_FOUND")
    print("AXIA_G07_CV2_HOST_CPU_PREEMPTION_UNCONFIRMED")
    print("AXIA_G07_CV2_SELFTEST_PASS_NO_ROS_NO_GOAL")


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("selftest")
    m=sub.add_parser("monitor")
    m.add_argument("--output",required=True)
    m.add_argument("--stop",required=True)
    m.add_argument("--interval-ms",type=int,default=40)
    a=sub.add_parser("analyze")
    for field in ("guest","host","owner-console","output"):
        a.add_argument("--"+field,required=True)
    args=p.parse_args()
    if args.command=="selftest":selftest()
    elif args.command=="monitor":monitor(args.output,args.stop,args.interval_ms)
    elif args.command=="analyze":analyze(args)


if __name__=="__main__":
    main()
