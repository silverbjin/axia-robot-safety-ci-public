#!/usr/bin/env python3
"""Exactly 3 independent *real* installed D04 ROS2+Nav2+Gazebo+YOLO sessions.

Reuse one Jazzy/Gazebo install and one C++/ONNX build. Each round starts and
stops a separate real Gazebo process and collects annotated RGB/YOLO evidence.
No fake ROS data, P1 private source, motor command, Fault, Goal, or E-Stop.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

def check_round(folder: Path, rc: int) -> dict:
    f=folder/"verdict.json"
    if not f.is_file():
        return {"passed":False,"reason":"NO_VERDICT","exit_code":rc}
    v=json.loads(f.read_text())
    seen=v.get("ros_evidence") or {}
    motion=seen.get("motion_evidence") or {}
    good=(rc==0 and v.get("status")=="PASS_PACKAGED_OFFICIAL_NAV2_GAZEBO_PERSON"
          and v.get("rgb_valid") is True
          and v.get("person_valid") is True
          and v.get("debug_saved") is True
          and v.get("motion_verified") is True
          and motion.get("passed") is True
          and v.get("shutdown_quality")=="PASS_NAV2_MANAGED_NO_SIGABRT"
          and (v.get("shutdown_service") or {}).get("passed") is True
          and (folder/"camera_frame.png").is_file()
          and (folder/"debug_frame.png").is_file())
    return {
        "passed":good,"exit_code":rc,"status":v.get("status"),
        "shutdown_quality":v.get("shutdown_quality"),
        "shutdown_service":(v.get("shutdown_service") or {}).get("passed"),
        "real_bbox_motion_px":motion.get("bbox_center_x_range_px"),
        "sim_time_span_s":motion.get("sim_time_span_s"),
        "person_samples":motion.get("person_detection_samples"),
        "blocker":v.get("blocker"),
    }


def run() -> int:
    parent=Path("results/d04-packaged-nav2-stability")
    parent.mkdir(parents=True,exist_ok=True)
    rounds=[]
    for n in range(1,4):
        dest=parent/f"round-{n}"
        dest.mkdir(parents=True,exist_ok=True)
        env=os.environ.copy()
        env["D04_OUTPUT_DIR"]=str(dest.resolve())
        start=time.monotonic()
        print(f"[D04][STABILITY] Round {n}/3 starting real Gazebo+ONNX",flush=True)
        try:
            result=subprocess.run(
                [sys.executable,"-u","scripts/d04_package_nav2_real_smoke.py"],
                env=env,text=True,capture_output=True,timeout=240,check=False)
            rc=result.returncode
            (dest/"runner_stdout.log").write_text(result.stdout)
            (dest/"runner_stderr.log").write_text(result.stderr)
        except subprocess.TimeoutExpired as exc:
            rc=124
            (dest/"runner_stdout.log").write_text(str(exc.stdout or "")[:20000])
            (dest/"runner_stderr.log").write_text("TIMEOUT:"+str(exc))
        status=check_round(dest,rc)
        status["round"]=n
        status["elapsed_s"]=round(time.monotonic()-start,2)
        rounds.append(status)
        print(json.dumps(status,ensure_ascii=False),flush=True)
        if not status["passed"]:
            break
    summary={
        "gate":"G-D04-PACKAGED-REAL-3X-COLD_START",
        "required_rounds":3,"completed_rounds":len(rounds),
        "passed":len(rounds)==3 and all(x["passed"] for x in rounds),
        "private_p1_included":False,
        "source_sha":os.environ.get("AXIA_TESTED_HEAD_SHA","NOT_PINNED"),
        "goal_sent":False,"fault_injected":False,
        "results":rounds,
    }
    (parent/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    files=[f for f in sorted(parent.rglob("*")) if f.is_file() and f.name!="SHA256SUMS"]
    (parent/"SHA256SUMS").write_text("".join(
        hashlib.sha256(f.read_bytes()).hexdigest()+"  "+f.relative_to(parent).as_posix()+"\n"
        for f in files),encoding="utf-8")
    print(json.dumps({k:summary[k] for k in
         ("gate","passed","required_rounds","completed_rounds")},ensure_ascii=False),flush=True)
    return 0 if summary["passed"] else 2

if __name__=="__main__":
    raise SystemExit(run())
