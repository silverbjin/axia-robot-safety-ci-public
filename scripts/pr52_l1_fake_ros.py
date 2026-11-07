#!/usr/bin/env python3
"""P1 L1 diagnostic for exact private SHA: NO Gazebo/Start/Goal/Fault.
All raw private stderr/JUnit live in TemporaryDirectory; public log is enums.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import private_ci_bridge as bridge

PIN = "13ddf2719d6e9c7ca98148783a06083e6975d8ce"
BRIDGE_PIN = "d86ee9860de8924f6a5b2c5828d493fb7ef7f9eb"
SAFE_STAGES = {"G02_UNIT", "G04_UNIT", "G03_ROS_FAKE", "G04_ROS_FAKE"}
SAFE_REASONS = (
    ("ROS_DIAGNOSTIC_UNAVAILABLE", "ROS_DIAGNOSTIC_UNAVAILABLE"),
    ("ModuleNotFoundError", "PYTHON_MODULE_MISSING"),
    ("ImportError", "IMPORT_FAILED"),
    ("No module named", "PYTHON_MODULE_MISSING"),
    ("ROS service response timeout", "ROS_SERVICE_RESPONSE_TIMEOUT"),
    ("initial health never ready", "ROS_HEALTH_NOT_READY"),
    ("health_diagnostics=", "HEALTH_ASSERTION_FAILED"),
    ("assert wait_until", "ROS_HEALTH_ASSERTION_FAILED"),
    ("rclpy.exceptions", "ROS_MIDDLEWARE_EXCEPTION"),
    ("Segmentation fault", "ROS_PROCESS_CRASH"),
    ("Traceback", "PYTHON_EXCEPTION"),
    ("FAILED", "ASSERTION_FAILED"),
)


def classify(text):
    if not isinstance(text, str):
        return "MISSING_DIAGNOSTIC"
    for marker, code in SAFE_REASONS:
        if marker in text:
            return code
    return "OTHER_OR_MISSING_DIAGNOSTIC"


_HEALTH_KEYS=("clock_ok","scan_ok","graph_ok","cm_ok","action_ready")
def extract_health_flags(content):
    """Expose only bounded known tri-state health fields; never private text."""
    out={}
    if not isinstance(content,str):
        return out
    for key in _HEALTH_KEYS:
        match=re.search(r"\b"+key+r"=(True|False|None)\b",content)
        if match:
            out[key]=match.group(1)
    return out


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")[-40000:]
    except OSError:
        return ""


def _evidence(results):
    roots = sorted(Path(results).glob("p1-*/summary.json"))
    if len(roots) != 1:
        return {"reason":"SUMMARY_MISSING_OR_AMBIGUOUS","stages":[]}, False
    base = roots[0].parent
    try:
        s = json.loads(roots[0].read_text())
    except (OSError, ValueError):
        return {"reason":"SUMMARY_INVALID","stages":[]}, False
    stages = []
    for stage in s.get("stage_results", []):
        name=stage.get("stage_id")
        if name not in SAFE_STAGES:
            stages.append({"stage":"UNRECOGNIZED","status":"BLOCKED"})
            continue
        row={"stage":name,"status":stage.get("status") if stage.get("status") in ("PASS","FAIL","ERROR","INCONCLUSIVE") else "BLOCKED",
             "repeat":stage.get("repeat") if type(stage.get("repeat")) is int else 0}
        if row["status"] != "PASS":
            folder=base/stage.get("gate","UNKNOWN")/("run_%02d" % row["repeat"])/name
            cases=stage.get("case_results") or []
            failures=[]
            for i,case in enumerate(cases,1):
                if case.get("status")=="PASS":
                    continue
                p=folder/"cases"/("case_%02d" % i)
                diagnostic=(_read(p/"stdout.log")+"\n"+_read(p/"stderr.log"))
                failures.append({"case_number":i,
                                 "returncode":case.get("returncode") if type(case.get("returncode")) is int else -1,
                                 "reason":classify(diagnostic),
                                 "health_flags":extract_health_flags(diagnostic)})
            if not failures:
                failures.append({"case_number":0,
                                 "returncode":stage.get("returncode",-1),
                                 "reason":classify(_read(folder/"stdout.log")+"\n"+_read(folder/"stderr.log"))})
            row["case_failures"]=failures[:20]
        stages.append(row)
    passed=s.get("overall_status")=="PARTIAL_VERIFIED" and s.get("exit_code")==0 and len(stages)==12
    passed=passed and all(x["status"]=="PASS" for x in stages)
    return {"status":s.get("overall_status") if s.get("overall_status") in ("PARTIAL_VERIFIED","FAIL","ERROR","INCONCLUSIVE","BLOCKED") else "BLOCKED",
            "stages":stages,"gate_accepted":False,"gazebo_executed":False}, passed


def run(private_root):
    if not (os.environ.get("GITHUB_ACTIONS")=="true"
            and os.environ.get("GITHUB_REPOSITORY")=="silverbjin/axia-robot-safety-ci-public"
            and os.environ.get("GITHUB_ACTOR")=="silverbjin"
            and bridge.PIN==BRIDGE_PIN):
        print('AXIA_P1_L1 '+json.dumps({"status":"BLOCKED","reason":"CONTEXT_INVALID","gate_accepted":False}))
        return 3
    bridge.PIN=PIN
    with tempfile.TemporaryDirectory(prefix="axia_p1_l1_", dir=os.getenv("RUNNER_TEMP") or None) as tmp:
        temp=Path(tmp)
        try:
            root=bridge.validate_private_commit(private_root)
            env=bridge.private_runtime_env(root,os.environ)
            env["GITHUB_SHA"]=PIN
            setup=bridge.ros_workspace_build(root,env,temp)
            results=temp/"fake-result"
            cmd=bridge.bash_with_ros_overlay(setup,[
                "python3","scripts/run_p1_evidence.py","--all","--profile","ros-fake",
                "--repeat","3","--timeout-sec","120","--allow-partial-ci",
                "--results-root",str(results)])
            with (temp/"private-l1.log").open("wb") as f:
                try:
                    p=subprocess.run(cmd,cwd=root,env=env,stdout=f,
                                     stderr=subprocess.STDOUT,timeout=700,check=False)
                    rc=p.returncode
                except subprocess.TimeoutExpired:
                    rc=124
            out,passed=_evidence(results)
            out["process_rc"]=rc if rc in (0,1,2,3,4,124) else 127
            out["status"]="L1_ROS_FAKE_PASS" if passed and rc==0 else "L1_ROS_FAKE_BLOCKED"
            out["private_source_sha_verified"]=True
            if not passed and not out.get("stages"):
                out["diagnostic"]=classify(_read(temp/"private-l1.log"))
        except bridge.GateBlocked:
            out={"status":"L1_ROS_FAKE_BLOCKED","reason":"PRIVATE_DEPENDENCY_OR_BUILD_BLOCKED",
                 "private_source_sha_verified":False}
        except Exception:
            out={"status":"L1_ROS_FAKE_BLOCKED","reason":"L1_RUNNER_EXCEPTION",
                 "private_source_sha_verified":False}
        out.update(gate_accepted=False,gazebo_executed=False,certified_estop_verified=False)
        print("AXIA_P1_L1 "+json.dumps(out,sort_keys=True),flush=True)
        return 0 if out["status"]=="L1_ROS_FAKE_PASS" else 3


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--private-root",required=True,type=Path)
    a=p.parse_args()
    raise SystemExit(run(a.private_root))
