#!/usr/bin/env python3
"""AXIA D07-H01 read-only WSL2 resource/renderer/Gazebo transport monitor.

Run IN PARALLEL with the existing GUI demonstration, in a second terminal.
No ROS motion/Goal, no Gazebo spawn, no sudo, no environment mutation.
Records host-only diagnostics; does NOT grant L2/L3 safety or visual PASS.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

STOP=False
def stop(_signal, _frame):
    global STOP
    STOP=True

def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def gib(kib):
    return round(float(kib)/1048576, 4)

def parse_meminfo(raw):
    vals={str(k):int(v) for k,v in re.findall(r"^([A-Za-z_()]+):\s*(\d+)\s+kB",raw,re.M)}
    return {
        "ram_total_gib":gib(vals.get("MemTotal",0)),
        "ram_available_gib":gib(vals.get("MemAvailable",0)),
        "ram_used_est_gib":gib(max(0,vals.get("MemTotal",0)-vals.get("MemAvailable",0))),
        "swap_total_gib":gib(vals.get("SwapTotal",0)),
        "swap_free_gib":gib(vals.get("SwapFree",0)),
    }

def classify_process(argv):
    if not argv:
        return None
    cmd=Path(argv[0]).name.lower()
    joined=" ".join(argv[:6]).lower()
    if "rviz2" in cmd:
        return "rviz2"
    # Gazebo Harmonic's 'gz sim' launcher is frequently a Ruby interpreter.
    # Actual Owner cNAPf8A0 ps evidence: server PID4581 and GUI PID5767
    # appear as 'ruby'. The old monitor labelled both as absent.
    # Require a literal gz executable followed by the 'sim' subcommand
    # so unrelated Ruby applications never masquerade as Gazebo.
    gz_sim_command=any(
        (Path(argv[i]).name.lower()=="gz" and i+1<len(argv)
         and argv[i+1].lower()=="sim")
        for i in range(min(len(argv),6))
    )
    if ("gz-sim" in cmd or "gz-sim" in joined or "gazebo" in cmd
        or gz_sim_command):
        if "-g" in argv or "gui" in cmd:
            return "gazebo_gui"
        if "-s" in argv or "server" in cmd:
            return "gazebo_server"
        return "gazebo_unknown"
    if ("ros2" in cmd and "launch" in joined) or "ros2launch" in cmd:
        return "ros2_launch"
    return None

def assess_gz_partitions(processes):
    servers=[p for p in processes if p.get("role")=="gazebo_server"]
    guis=[p for p in processes if p.get("role")=="gazebo_gui"]
    base={"servers":len(servers),"guis":len(guis),"gui_connection_verified":False}
    if not servers or not guis:
        return {**base,"status":"NO_SERVER_OR_GUI_PROCESS"}
    a={p.get("gz_partition") for p in servers if p.get("gz_partition")}
    b={p.get("gz_partition") for p in guis if p.get("gz_partition")}
    if a and b and a.isdisjoint(b):
        return {**base,"status":"MISMATCH","server_partitions":sorted(a),"gui_partitions":sorted(b)}
    if a and b and a.intersection(b):
        return {**base,"status":"MATCH_NOT_CONNECTION_PROOF","server_partitions":sorted(a),
                "gui_partitions":sorted(b)}
    return {**base,"status":"UNKNOWN_PARTITION","server_partitions":sorted(a),
            "gui_partitions":sorted(b)}

def assess_renderer(text, forced_software=False):
    match=re.search(r"(?:OpenGL renderer string|Device):\s*(.+)",text,re.I)
    renderer=match.group(1).strip() if match else ""
    lower=renderer.lower()
    if "llvmpipe" in lower or "softpipe" in lower or "swrast" in lower:
        status="SOFTWARE_RENDERER"
    elif forced_software and renderer:
        status="GUI_SOFTWARE_FORCED_IN_ENV_VERIFY_EFFECTIVE_RENDERER"
    elif "d3d12" in lower:
        status="WSLG_D3D12_RENDERER"
    elif renderer:
        status="RENDERER_IDENTIFIED_GPU_USAGE_UNPROVEN"
    else:
        status="RENDERER_UNKNOWN"
    return {"status":status,"renderer":renderer or "unavailable",
            "forced_software_env":bool(forced_software),
            "gpu_utilization_proven":False}

def cpu_percent(previous, current):
    if not previous:
        return None
    busy0,total0=previous
    busy1,total1=current
    if total1<=total0 or busy1<busy0:
        return None
    return round(100*(busy1-busy0)/(total1-total0),2)

def cpu_ticks():
    parts=Path("/proc/stat").read_text().splitlines()[0].split()
    numbers=[int(n) for n in parts[1:]]
    idle=numbers[3]+(numbers[4] if len(numbers)>4 else 0)
    return sum(numbers)-idle,sum(numbers)

def read_text(path, max_bytes=262144):
    try:
        with open(path,"rb") as stream:
            return stream.read(max_bytes).decode("utf-8","replace")
    except (OSError,PermissionError):
        return ""

def process_rows(previous, now):
    rows=[]
    stats={}
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        pid=int(d.name)
        args=[s for s in read_text(d/"cmdline",32768).split("\0") if s]
        role=classify_process(args)
        if not role:
            continue
        # Only fixed allowlisted diagnostics from /proc/environ. Never
        # export credentials, command arguments, entire environment or source.
        envraw=read_text(d/"environ",65536)
        env={}
        for item in envraw.split("\0"):
            if "=" not in item:
                continue
            k,v=item.split("=",1)
            if k in ("GZ_PARTITION","ROS_DOMAIN_ID","LIBGL_ALWAYS_SOFTWARE",
                     "DISPLAY","WAYLAND_DISPLAY","QT_QPA_PLATFORM"):
                env[k]=v[:180]
        line=read_text(d/"stat")
        stat={}
        if ")" in line:
            try:
                fields=line.rsplit(")",1)[1].strip().split()
                stat={"ticks":int(fields[11])+int(fields[12]),"rss_pages":int(fields[21])}
            except (ValueError,IndexError):
                pass
        old=previous.get(pid)
        pct=None
        if old and "ticks" in stat and old[1]<now and stat["ticks"]>=old[0]:
            pct=round(100*(stat["ticks"]-old[0])/
                      (os.sysconf("SC_CLK_TCK")*(now-old[1])),2)
        if "ticks" in stat:
            stats[pid]=(stat["ticks"],now)
        rows.append({
            "pid":pid,"role":role,"gz_partition":env.get("GZ_PARTITION"),
            "ros_domain_id":env.get("ROS_DOMAIN_ID"),
            "libgl_always_software":env.get("LIBGL_ALWAYS_SOFTWARE"),
            "display_set":bool(env.get("DISPLAY")),
            "cpu_percent_one_core":pct,
            "rss_mib":round(stat.get("rss_pages",0)*os.sysconf("SC_PAGE_SIZE")/1048576,2)
        })
    return sorted(rows,key=lambda x:(x["role"],x["pid"])),stats

def command_result(args, timeout=8, env=None):
    if not shutil.which(args[0]):
        return "NOT_INSTALLED: "+args[0]+"\n"
    try:
        proc=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                            text=True,errors="replace",timeout=timeout,env=env,
                            check=False)
        return f"exit_code={proc.returncode}\n"+proc.stdout[:40000]
    except (OSError,subprocess.TimeoutExpired) as exc:
        return "UNAVAILABLE_OR_TIMEOUT: "+type(exc).__name__+"\n"

def optional_context(folder):
    (folder/"kernel.txt").write_text(command_result(["uname","-a"]))
    (folder/"wsl_status.txt").write_text(
        "dxg_device_exists="+str(Path("/dev/dxg").exists())+"\n"+
        "wslg_mount_exists="+str(Path("/mnt/wslg").exists())+"\n"+
        "display_set="+str(bool(os.environ.get("DISPLAY")))+"\n"+
        "wayland_set="+str(bool(os.environ.get("WAYLAND_DISPLAY")))+"\n")
    (folder/"renderer_glxinfo_B.txt").write_text(command_result(["glxinfo","-B"],timeout=8))
    gpu_cmd=shutil.which("nvidia-smi") or "/usr/lib/wsl/lib/nvidia-smi"
    (folder/"nvidia_gpu.txt").write_text(
        command_result([gpu_cmd,"--query-gpu=name,memory.total,memory.used,utilization.gpu",
                        "--format=csv,noheader,nounits"],timeout=6)
        if Path(gpu_cmd).exists() else "NVIDIA_SMI_NOT_AVAILABLE_AMD_INTEL_MAY_EXIST\n")
    # Host-side capacity and adapter names, never entire host registry.
    # .wslconfig may not exist; only memory / swap / processors lines exposed.
    ps = (
        "$ErrorActionPreference='SilentlyContinue';"
        "$o=Get-CimInstance Win32_OperatingSystem;"
        "if($o){'WINDOWS_RAM_TOTAL_GIB='+[math]::Round($o.TotalVisibleMemorySize/1048576,2);"
        "'WINDOWS_RAM_FREE_GIB='+[math]::Round($o.FreePhysicalMemory/1048576,2)};"
        "Get-CimInstance Win32_VideoController | ForEach-Object {'GPU_ADAPTER='+$_.Name};"
        "$p=Join-Path $env:USERPROFILE '.wslconfig';"
        "if(Test-Path $p){'WSLCONFIG_RELEVANT_LINES';"
        "Get-Content $p | Where-Object {$_ -match '^\\s*(memory|processors|swap)\\s*='}}"
        "else{'WSLCONFIG_NOT_PRESENT_DEFAULTS_APPLY'}"
    )
    (folder/"windows_host_readonly.txt").write_text(
        command_result(["powershell.exe","-NoProfile","-NonInteractive","-Command",ps],
                       timeout=12))
    wslg=Path("/mnt/wslg/versions.txt")
    if wslg.is_file():
        (folder/"wslg_versions.txt").write_text(read_text(wslg,8192))
    (folder/"gazebo_topic_discovery.txt").write_text(
        "NO_ACTIVE_GAZEBO_SERVER_PARTITION_YET\n")

def monitor(args):
    root=Path(args.outdir).expanduser().resolve()
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(root,0o700)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder=Path(tempfile.mkdtemp(prefix=f"axia-wsl2-monitor-{stamp}-",dir=root))
    os.chmod(folder,0o700)
    summary={"schema":"axia_d07_readonly_wsl2_gpu_memory_monitor_v1",
             "validation_level":"HOST_METRICS_ONLY","safety_accepted":False,
             "gazebo_gui_render_pass":False,"source_path":"live_proc_and_tools",
             "begin_utc":utc(),"sample_count":0,
             "target_process_observed":False,"max_host_cpu_percent":0,
             "min_wsl_available_ram_gib":None,"max_target_rss_mib":0}
    if not args.no_external:
        optional_context(folder)
    else:
        (folder/"context_skipped.txt").write_text("NO_EXTERNAL_TEST_MODE\n")
    prev_cpu=None
    prev_procs={}
    first_gz_probe=False
    samples_file=folder/"samples.jsonl"
    deadline=time.monotonic()+args.duration
    print("AXIA_WSL2_MONITOR_READONLY_NO_GOAL BEGIN="+str(folder),flush=True)
    try:
        with samples_file.open("w") as out:
            while True:
                start=time.monotonic()
                mem=parse_meminfo(read_text("/proc/meminfo"))
                ticks=cpu_ticks()
                proc,next_procs=process_rows(prev_procs,start)
                assessment=assess_gz_partitions(proc)
                row={"utc":utc(),"seconds_elapsed":round(args.duration-max(0,deadline-start),2),
                     "wsl_memory":mem,"host_cpu_percent":cpu_percent(prev_cpu,ticks),
                     "gz_partition_alignment":assessment,"processes":proc,
                     "dxg_device_exists":Path("/dev/dxg").exists()}
                out.write(json.dumps(row,sort_keys=True)+"\n")
                out.flush()
                summary["sample_count"]+=1
                summary["target_process_observed"] |= bool(proc)
                cp=row["host_cpu_percent"]
                if cp is not None:
                    summary["max_host_cpu_percent"]=max(summary["max_host_cpu_percent"],cp)
                ram=mem["ram_available_gib"]
                previous=summary["min_wsl_available_ram_gib"]
                summary["min_wsl_available_ram_gib"]=ram if previous is None else min(previous,ram)
                summary["max_target_rss_mib"]=max(summary["max_target_rss_mib"],
                    sum(p["rss_mib"] for p in proc))
                if assessment["status"]=="MISMATCH":
                    summary["gz_partition_mismatch_observed"]=True
                if (not first_gz_probe and not args.no_external
                    and assessment["servers"]>0):
                    first_gz_probe=True
                    partitions=assessment.get("server_partitions") or [
                        p["gz_partition"] for p in proc if p["role"]=="gazebo_server"
                        and p["gz_partition"]]
                    env=os.environ.copy()
                    if partitions:
                        env["GZ_PARTITION"]=partitions[0]
                    (folder/"gazebo_topic_discovery.txt").write_text(
                        command_result(["gz","topic","-l"],timeout=5,env=env))
                if summary["sample_count"]==1 or summary["sample_count"]%5==0:
                    print(f"AXIA_SAMPLE n={summary['sample_count']} "
                          f"WSL_RAM_GiB={mem['ram_total_gib']:.2f} "
                          f"AVAILABLE_GiB={ram:.2f} "
                          f"CPU={cp if cp is not None else 'warming'}% "
                          f"GazeboServer={assessment['servers']} "
                          f"GazeboGUI={assessment['guis']} "
                          f"RViz={sum(p['role']=='rviz2' for p in proc)} "
                          f"PARTITION={assessment['status']}",flush=True)
                prev_cpu=ticks
                prev_procs=next_procs
                if STOP or time.monotonic()>=deadline:
                    break
                time.sleep(min(args.interval,max(0,deadline-time.monotonic())))
    finally:
        summary["end_utc"]=utc()
        summary["monitor_interrupted"]=bool(STOP)
        summary["wsl_vm_ram_gib"]=mem["ram_total_gib"] if "mem" in locals() else None
        summary["first_invalid_boundary"]=(
            "GZ_SERVER_GUI_PARTITION_MISMATCH" if summary.get("gz_partition_mismatch_observed")
            else "GUI_RENDER_NOT_PROVEN_BY_RESOURCE_MONITOR")
        (folder/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,
                                                       indent=2,sort_keys=True)+"\n")
        archive=root/(folder.name+".tar.gz")
        with tarfile.open(archive,"w:gz") as tar:
            tar.add(folder,arcname=folder.name,recursive=True)
        checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
        side=Path(str(archive)+".sha256")
        side.write_text(f"{checksum}  {archive.name}\n")
        print("AXIA_WSL2_MONITOR_SUMMARY="+str(folder/"summary.json"),flush=True)
        print("AXIA_WSL2_RESOURCE_MONITOR_BUNDLE="+str(archive),flush=True)
        print("AXIA_WSL2_RESOURCE_MONITOR_SHA256="+str(side),flush=True)
        print("AXIA_WSL2_RESOURCE_MONITOR_HOST_ONLY_L3_GUI_NOT_PROVEN",flush=True)
    return 0

def self_check():
    assert parse_meminfo("MemTotal: 1048576 kB\nMemAvailable: 524288 kB")["ram_total_gib"]==1.0
    assert assess_gz_partitions([{"role":"gazebo_server","gz_partition":"A"},
                                 {"role":"gazebo_gui","gz_partition":"B"}])["status"]=="MISMATCH"
    assert classify_process(["/usr/bin/gz","sim","-g"])=="gazebo_gui"
    assert assess_renderer("OpenGL renderer string: llvmpipe",True)["status"]=="SOFTWARE_RENDERER"
    print("AXIA_WSL2_MONITOR_L0_PASS_NO_ROS_NO_GUI")
    return 0

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--duration",type=float,default=120.,
                   help="monitor seconds, 1..600 (default 120)")
    p.add_argument("--interval",type=float,default=2.,
                   help="sampling seconds, 0.25..30 (default 2)")
    p.add_argument("--outdir",default=str(Path.home()/"axia_wsl2_monitor"))
    p.add_argument("--no-external",action="store_true",help=argparse.SUPPRESS)
    p.add_argument("--self-check",action="store_true")
    args=p.parse_args(argv)
    if args.self_check:
        return self_check()
    if not 1<=args.duration<=600 or not .25<=args.interval<=30:
        p.error("duration must be 1..600, interval 0.25..30")
    signal.signal(signal.SIGINT,stop)
    signal.signal(signal.SIGTERM,stop)
    return monitor(args)

if __name__=="__main__":
    raise SystemExit(main())
