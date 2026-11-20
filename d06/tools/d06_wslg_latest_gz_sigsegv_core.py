#!/usr/bin/env python3
"""Choose latest Gazebo SIGSEGV from a local systemd coredump JSON listing.

This script is a pure parser. It never starts Gazebo, GDB, ROS or a network
request, and never reads process memory. Only PID goes to stdout.
"""
import argparse
import json
import pathlib
import re
import sys


def latest_gazebo_sigsegv_pid(raw, *, server_only=False):
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        try:
            parsed = [json.loads(x) for x in raw.splitlines() if x.strip()]
        except (ValueError, TypeError):
            return None
    if isinstance(parsed, dict):
        parsed = parsed.get("entries", [parsed])
    if not isinstance(parsed, list):
        return None
    candidates=[]
    for index,row in enumerate(parsed):
        if not isinstance(row,dict):
            continue
        exe=str(row.get("COREDUMP_EXE",row.get("EXE",row.get("exe",""))))
        comm=str(row.get("COREDUMP_COMM",row.get("COMM","")))
        exe_name=pathlib.PurePosixPath(exe).name
        if server_only:
            # The original -11 was gz sim -s. A generic 'gz' SIGSEGV
            # can be the separate -g GUI process. Never infer a server
            # stack from its executable name alone.
            cmdline=str(row.get("COREDUMP_CMDLINE",
                                row.get("CMDLINE",row.get("cmdline",""))))
            definitely_server=(exe_name=="gz-sim-server" or (
                comm=="gz-sim-server" and exe_name not in (
                    "gz-sim-gui-client","gz-sim-gui")))
            gz_server_arg=(exe_name=="gz" and re.search(
                r"(?<!\\S)(?:-s|--server-only)(?!\\S)",cmdline) is not None)
            if not (definitely_server or gz_server_arg):
                continue
        elif exe_name not in ("gz","gz-sim-server") and comm not in (
                "gz","gz-sim-server"):
            continue
        sig=str(row.get("COREDUMP_SIGNAL",row.get("SIGNAL",row.get("SIG",""))))
        if sig not in ("11","SIGSEGV"):
            continue
        pid=str(row.get("COREDUMP_PID",row.get("PID",row.get("pid",""))))
        if not pid.isdecimal() or int(pid)<=0:
            continue
        raw_tick=str(row.get("COREDUMP_TIMESTAMP",row.get("TIMESTAMP","")))
        try:tick=int(raw_tick)
        except (ValueError,TypeError):tick=index
        candidates.append((tick,index,int(pid)))
    return max(candidates)[2] if candidates else None


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--json-file",required=True,type=pathlib.Path)
    p.add_argument("--server-only",action="store_true")
    args=p.parse_args()
    try:
        pid=latest_gazebo_sigsegv_pid(args.json_file.read_text(),
                                         server_only=args.server_only)
    except OSError:
        return 3
    if pid is None:
        print("D06_WSLG_GAZEBO_SIGSEGV_CORE_NOT_PRESENT")
        return 3
    print(pid)
    return 0


if __name__=="__main__":
    sys.exit(main())
