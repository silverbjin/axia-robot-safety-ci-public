#!/usr/bin/env python3
"""C16 read-only independent WSLg GPU-host G3 capability classifier.

This probe starts no Gazebo/ROS nodes, changes no driver, runs no Goal,
installs nothing and never grants final acceptance. The same assess() is
covered by public L0 mocked evidence. Real G3 still requires a separate
matching GPU host, first Gazebo native core and full safety timing.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

TOOLS=("glxinfo","nvidia-smi","gdb","coredumpctl","gz","ros2")

def assess(facts):
    issues=[]
    kernel=str(facts.get("kernel","")).lower()
    if not ("microsoft" in kernel or "wsl2" in kernel):
        issues.append("NOT_WSL2_KERNEL")
    if (str(facts.get("os_id","")).lower()!="ubuntu" or
            str(facts.get("os_version",""))!="24.04"):
        issues.append("NOT_UBUNTU_2404")
    if not facts.get("display") or not facts.get("wayland"):
        issues.append("WSLG_DISPLAY_NOT_PROVEN")
    renderer=str(facts.get("glxinfo",""))
    if not ("D3D12" in renderer and "NVIDIA" in renderer.upper()):
        issues.append("D3D12_NVIDIA_RENDERER_NOT_PROVEN")
    gpu=str(facts.get("nvidia","")).lower()
    if not ("rtx 2060" in gpu and "nvidia" in gpu):
        issues.append("RTX2060_REFERENCE_GPU_NOT_MATCHED")
    binaries=facts.get("binaries",{})
    for key in TOOLS:
        if not binaries.get(key,False):
            issues.append("MISSING_TOOL_"+key)
    if not facts.get("jazzy_overlay",False):
        issues.append("ROS_JAZZY_NOT_PRESENT")
    core_pattern=str(facts.get("core_pattern",""))
    if "systemd-coredump" not in core_pattern:
        issues.append("CORE_SYSTEMD_HANDLER_NOT_CONFIGURED")
    return {
        "decision":("G3_CAPABILITY_HOLD" if issues
                    else "G3_HOST_CANDIDATE_NOT_ACCEPTED"),
        "issues":issues,
        "gazebo_l2_executed":False,
        "wslg_sigsegv_resolved":False,
        "core_backend_real_crash_tested":False,
        "certified_estop":False
    }

def read(path):
    try:
        return Path(path).read_text(errors="replace").strip()
    except OSError:
        return ""

def command_output(args):
    try:
        result=subprocess.run(args,capture_output=True,text=True,timeout=12,
                              check=False)
        return result.stdout if result.returncode==0 else ""
    except (OSError,subprocess.TimeoutExpired):
        return ""

def actual_facts():
    entries={}
    for row in read("/etc/os-release").splitlines():
        if "=" in row:
            k,v=row.split("=",1)
            entries[k]=v.strip().strip('"')
    bins={name:bool(shutil.which(name)) for name in TOOLS}
    nv=shutil.which("nvidia-smi")
    if not nv and Path("/usr/lib/wsl/lib/nvidia-smi").exists():
        nv="/usr/lib/wsl/lib/nvidia-smi"
        bins["nvidia-smi"]=True
    return {
        "kernel":read("/proc/sys/kernel/osrelease"),
        "os_id":entries.get("ID",""),
        "os_version":entries.get("VERSION_ID",""),
        "display":os.environ.get("DISPLAY",""),
        "wayland":os.environ.get("WAYLAND_DISPLAY",""),
        "glxinfo":command_output(["glxinfo","-B"]) if bins["glxinfo"] else "",
        "nvidia":command_output([nv,"--query-gpu=name","--format=csv,noheader"])
                  if nv else "",
        "binaries":bins,
        "jazzy_overlay":Path("/opt/ros/jazzy/setup.bash").is_file(),
        "core_pattern":read("/proc/sys/kernel/core_pattern"),
    }

def main():
    if sys.argv[1:]:
        print("D06_G3_CAPABILITY_USAGE=NO_ARGUMENTS",file=sys.stderr)
        return 2
    verdict=assess(actual_facts())
    print(json.dumps(verdict,sort_keys=True,ensure_ascii=False))
    print("D06_"+verdict["decision"])
    print("D06_G3_WSLG_GAZEBO_SHUTDOWN=NOT_VERIFIED")
    print("AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false")
    return 3 if verdict["issues"] else 0

if __name__=="__main__":
    sys.exit(main())
