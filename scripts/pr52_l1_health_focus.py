#!/usr/bin/env python3
"""P1-T08 L1 focused RED diagnosis. Real Jazzy, fake ROS graph, no Gazebo/Goal."""
from __future__ import annotations
import json, os, re, subprocess, sys, tempfile
from pathlib import Path
import private_ci_bridge as bridge

PIN="124fa3893a8266e3da230ed5c614fac5d8d60624"
BASE="d86ee9860de8924f6a5b2c5828d493fb7ef7f9eb"
CASE_IDS={
    "G03_GOAL_CANCEL":"tests/ros_integration/test_p1_t04_action.py::test_supervisor_goal_stop_cancel_reset_rearm_has_no_auto_resume",
    "G03_HEARTBEAT":"tests/ros_integration/test_p1_t04_action.py::test_received_command_heartbeat_loss_trips_protective_stop",
    "G04_HEARTBEAT":"tests/ros_integration/test_p1_t06_faults.py::test_t06_command_heartbeat_loss_and_no_automatic_resume",
}
CAUSE={
    "initial health never ready":"SUPERVISOR_BOOT_HEALTH_TIMEOUT",
    "Fake CM graph + synthetic scan not ready":"SUPERVISOR_BOOT_HEALTH_TIMEOUT",
    "No steady-clock zero publications":"SUPERVISOR_STEADY_TIMER_MISSING",
    "Fake NavigateToPose action server unavailable":"ACTION_DISCOVERY_TIMEOUT",
    "ROS test service not ready":"SERVICE_DISCOVERY_TIMEOUT",
    "Stale input must latch PROTECTIVE_STOP":"COMMAND_STALE_NOT_LATCHED",
    "Wrong stop cause":"WRONG_PROTECTIVE_STOP_CAUSE",
    "missing NavigateToPose cancellation":"NAV2_CANCEL_MISSING",
    "assert wait_until":"ROS_CALLBACK_ASSERTION_FAILED",
}
KEYS=("clock_ok","scan_ok","graph_ok","cm_ok","action_ready")


def diagnosis(text):
    if not isinstance(text,str):
        return {"reason":"MISSING_DIAGNOSTICS","flags":{}}
    flags={}
    for key in KEYS:
        p=re.search(r"\b"+key+r"=(True|False|None)\b",text)
        if p:flags[key]=p.group(1)
    reason=next((code for marker,code in CAUSE.items() if marker in text),
                "ASSERTION_FAILED_UNCLASSIFIED")
    # Pytest frames are cited as test_file.py:LINE on failures. Emit only
    # allowlisted test line numbers, never the private assertion text.
    source_lines=re.findall(r"test_p1_t0[46]_[a-z_]+\.py:(\d+):",text)
    line=int(source_lines[-1]) if source_lines else None
    return {"reason":reason,"flags":flags,
            "assert_line":line if line is not None and 1 <= line <= 600 else None}


def main():
    result={"status":"L1_FOCUSED_RED_DIAG_BLOCKED","cases":[],
            "gazebo_executed":False,"gate_accepted":False}
    if not (os.environ.get("CI")=="true" and os.environ.get("GITHUB_ACTIONS")=="true"
            and os.environ.get("GITHUB_REPOSITORY")=="silverbjin/axia-robot-safety-ci-public"
            and os.environ.get("GITHUB_ACTOR")=="silverbjin"
            and os.environ.get("GITHUB_REF")=="refs/heads/feat/secure-instructor-cloud-bridge"
            and bridge.PIN==BASE):
        print("AXIA_P1_L1_FOCUS "+json.dumps(result,sort_keys=True))
        return 3
    bridge.PIN=PIN
    try:
        private=bridge.validate_private_commit(Path("_instructor_private"))
        with tempfile.TemporaryDirectory(prefix="axia_l1_focus_",
                                         dir=os.getenv("RUNNER_TEMP") or None) as t:
            tmp=Path(t)
            env=bridge.private_runtime_env(private,os.environ)
            setup=bridge.ros_workspace_build(private,env,tmp)
            for i in (1,2,3):
                for name,case in CASE_IDS.items():
                    use=dict(env, ROS_DOMAIN_ID=str(60+(i-1)*3+list(CASE_IDS).index(name)),
                             ROS_AUTOMATIC_DISCOVERY_RANGE="LOCALHOST")
                    command=bridge.bash_with_ros_overlay(setup,
                        ["python3","-m","pytest","-q","-ra",case])
                    try:
                        run=subprocess.run(command,cwd=private,env=use,
                                           capture_output=True,timeout=60,check=False)
                        code=run.returncode
                        data=(run.stdout+run.stderr).decode("utf-8",errors="replace")[-60000:]
                    except (OSError,subprocess.TimeoutExpired):
                        code=124; data=""
                    row={"repeat":i,"case":name,"pass":code==0,
                         "rc":code if code in (0,1,2,3,4,124) else 127}
                    if code!=0:
                        row.update(diagnosis(data))
                    result["cases"].append(row)
                    print("AXIA_P1_L1_FOCUS_CASE "+json.dumps(row,sort_keys=True),flush=True)
            result["status"]=("L1_FOCUSED_9_CASES_PASS" if len(result["cases"])==9
                              and all(x["pass"] for x in result["cases"])
                              else "L1_FOCUSED_REPRODUCED_FAILURE")
    except bridge.GateBlocked:
        result["reason"]="PROTECTED_SOURCE_OR_COLCON_NOT_READY"
    except Exception:
        result["reason"]="UNKNOWN_FAKE_ROS_DIAGNOSTIC_ERROR"
    print("AXIA_P1_L1_FOCUS "+json.dumps(result,sort_keys=True),flush=True)
    return 0 if result["status"]=="L1_FOCUSED_9_CASES_PASS" else 3


if __name__=="__main__":raise SystemExit(main())
