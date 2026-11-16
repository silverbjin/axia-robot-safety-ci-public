#!/usr/bin/env python3
"""Interpret actual Owner GUI failure evidence conservatively, without ROS or Goal.

Do not equate an expensive gz model /world/default/state timeout to absent
Gazebo when both live ROS LaserScan and real Gazebo World/Waffle services exist.
Nor equate service existence to a rendered GUI pixel or formal acceptance.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

def classify_renderer_warning(log: str) -> str:
    if "Not allowed to force software rendering when API explicitly selects a hardware device" in log:
        return "FORCED_SOFTWARE_EGL_CONFLICT_CANDIDATE"
    return "RENDERER_FAILURE_UNCLASSIFIED_NOT_WSLG_PROVEN"

def interpret_world_probe(services: str, models: str, monitor: str) -> dict:
    names=set(line.strip() for line in services.splitlines())
    world="/world/default/control" in names
    waffle=any(line.startswith("/world/default/model/turtlebot3_waffle/")
               for line in names)
    scan=bool(re.search(r'"front_m":\s*[0-9]+(?:\.[0-9]+)?',monitor))
    model_timeout=("timed out" in models.lower() or "timeout" in models.lower())
    evidence=world and waffle and scan
    status=("MODEL_QUERY_TIMEOUT_WITH_LIVE_ROS_AND_WORLD_SERVICES_NO_GOAL"
            if evidence and model_timeout
            else "WORLD_TRANSPORT_OR_MODEL_UNVERIFIED_HOLD")
    return {"schema":"axia.g07.rollback.wslg_evidence_v1",
            "status":status,
            "gazebo_world_service_seen":world,
            "waffle_sensor_service_seen":waffle,
            "ros_scan_seen":scan,
            "model_query_timed_out":model_timeout,
            "world_absence_proven":False,
            "wslg_pixels_verified":False,
            "goal_sent":False,
            "certified_estop":False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--services",required=True,type=Path)
    ap.add_argument("--models",required=True,type=Path)
    ap.add_argument("--monitor",required=True,type=Path)
    ap.add_argument("--gazebo-gui-log",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args()
    if a.output.exists() or a.output.is_symlink():
        print("AXIA_G07_ROLLBACK_EVIDENCE_DEST_EXISTS_HOLD");return 3
    try:
        r=interpret_world_probe(
            a.services.read_text(encoding="utf-8",errors="replace"),
            a.models.read_text(encoding="utf-8",errors="replace"),
            a.monitor.read_text(encoding="utf-8",errors="replace"))
        r["renderer_diagnostic"]=classify_renderer_warning(
            a.gazebo_gui_log.read_text(encoding="utf-8",errors="replace"))
        a.output.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print("AXIA_G07_ROLLBACK_EVIDENCE_READONLY "+json.dumps(r,sort_keys=True),flush=True)
        return 0 if r["gazebo_world_service_seen"] and r["waffle_sensor_service_seen"] and r["ros_scan_seen"] else 3
    except (OSError,UnicodeError) as exc:
        print("AXIA_G07_ROLLBACK_EVIDENCE_READ_ERROR "+type(exc).__name__);return 3

if __name__=="__main__":
    raise SystemExit(main())
