#!/usr/bin/env python3
"""Private live G00 simulation bridge. Never writes Goal, Twist or Fault itself.
Executes the PINNED private guarded Gazebo field runner in protected Actions,
observes sealed rosbag2 and real Goal UUID/terminal, prints only allowlisted
status. No private source, logs, rosbag or stdout is uploaded to public CI.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import private_ci_bridge as bridge

PIN = "b75d971b3d6655105ad9055bcbbcb043ac2feaa8"
BASE = "d86ee9860de8924f6a5b2c5828d493fb7ef7f9eb"
ALLOWED = {"START_ACK_VERIFIED","START_ACK_BLOCKED","R05_TYPED_ACK_BLOCKED",
    "R05_BOUND_TYPED_PRE_SEND_CANDIDATE","SHUTDOWN_CLEAN",
    "SHUTDOWN_FAILED","SHUTDOWN_INCONCLUSIVE","SMOKE_READY",
    "R06_G00_EVIDENCE_CANDIDATE","BLOCKED","INCONCLUSIVE","PASS",
    "SHUTDOWN_CONFIRMED","SHUTDOWN_BLOCKED","MISSING"}


def _status(path, field="status"):
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
        value=data.get(field)
        return value if value in ALLOWED else "BLOCKED"
    except (OSError, ValueError, TypeError):
        return "MISSING"


def _blocked_phase(log_file):
    """Only constant status enums from ephemeral private console; no raw data."""
    try:
        content=log_file.read_text(encoding="utf-8",errors="replace")[-100_000:]
    except OSError:
        return "PRIVATE_CONSOLE_MISSING"
    rules=(
        ("CLOUD_CI_G00_ONLY", "CLOUD_CONTEXT_DENIED"),
        ("fake ROS regressions failed", "PREFLIGHT_FAKE_ROS_FAILED"),
        ("official pinned Nav2 overlay verification failed", "NAV2_OVERLAY_POLICY_FAILED"),
        ("build failed", "COLCON_BUILD_FAILED"),
        ("Baseline hash mismatch", "BASELINE_MISMATCH"),
        ("missing ROS package", "ROS_PACKAGES_MISSING"),
        ("R07_FAULT_REQUIRES_INDEPENDENT_REVIEW", "FAULT_BOUNDARY_BLOCKED"),
        ("SUPERVISOR_START_NOT_ACKNOWLEDGED", "START_OR_PRE_SEND_BOUNDARY_BLOCKED"),
        ("PRE_GOAL_BLOCKED", "PRE_GOAL_BLOCKED"),
        ("READINESS_OR_P1_GRAPH_NOT_VERIFIED", "NAV2_READINESS_OR_GRAPH_BLOCKED"),
        ("SUPERVISOR_PRESTART_BLOCKED", "SUPERVISOR_PRESTART_BLOCKED"),
        ("Final field collection complete", "FINAL_FIELD_COLLECTION_RECORDED"),
    )
    # A successful CLOUD_CI_G00_ONLY status log must NEVER be treated as
    # a denial. Only actual [BLOCKED] lines provide a matching phase.
    if "CLOUD_CI_G00_ONLY" in content and "[BLOCKED]" not in content:
        return "NO_RECORDED_BLOCKED_LINE"
    if "[BLOCKED]" not in content:
        return "NO_RECORDED_BLOCKED_LINE"
    for marker,code in rules:
        if marker in content:
            return code
    return "BLOCKED_UNCLASSIFIED"


_SAFE_R05 = frozenset((
    "RUN_SESSION_INVALID","SOURCE_SHA_MISMATCH","SIMULATION_CONTEXT_INVALID",
    "MONOTONIC_CLOCK_INVALID","SUPERVISOR_RECEIPT_TOO_OLD",
    "START_ACK_INVALID","ACK_BEFORE_PREFLIGHT","LEGACY_PRECHECK_BLOCKED",
    "LEGACY_PRECHECK_ERROR",
    *(f"PROVENANCE_MISMATCH:{n}" for n in
      ("pre_goal_gate","corridor","graph","supervisor_prestart","start_ack")),
    *(f"EVIDENCE_TIME_INVALID:{n}" for n in
      ("pre_goal_gate","corridor","graph","supervisor_prestart","start_ack"))
))


def _private_r05_codes(child, private, source_sha):
    """Return allowlisted reason codes without publishing private state or bag."""
    try:
        from tools.p1_t08_r01_binding import assess_bound_candidate
        names=("corridor","graph","pre_goal_gate","supervisor_prestart","start_ack")
        evidence={k:json.loads((child/(k+".json")).read_text()) for k in names}
        ack=evidence["start_ack"]
        att=ack.get("provenance",{})
        env={"ROS_DISTRO":"jazzy","AXIA_P0_SIM_ONLY":"1",
             "ROS_DOMAIN_ID":att.get("ros_domain_id"),
             "GZ_PARTITION":att.get("gz_partition"),
             "AXIA_P1_CLOUD_G00_OPT_IN":"YES",
             "AXIA_P1_CLOUD_G00_START_APPROVED":"YES",
             "AXIA_P1_CLOUD_G00_SCENARIO":"g00",
             "AXIA_T08_FAULT_APPROVED":"NO"}
        now=ack.get("received_monotonic_ns")
        result=assess_bound_candidate(evidence,expected_sha=source_sha,
            actual_sha=source_sha,env=env,run_id=ack.get("run_id"),
            session_id=att.get("session_id"),now_monotonic_ns=now)
        codes=result.get("reasons") or []
        return [c if c in _SAFE_R05 else "UNRECOGNIZED" for c in codes][:12]
    except (OSError,ValueError,TypeError,KeyError,ImportError):
        return ["R05_DIAGNOSTIC_UNAVAILABLE"]


def run(private_root):
    report={"status":"CLOUD_G00_BLOCKED","private_sha_verified":False,
            "gazebo_executed":False,"real_goal_verified":False,
            "three_independent_runs":False,"gate_accepted":False,
            "fault_injected":False,"certified_estop_verified":False,
            "runs":[]}
    if not (os.environ.get("GITHUB_ACTIONS")=="true"
            and os.environ.get("CI")=="true"
            and os.environ.get("GITHUB_REPOSITORY")=="silverbjin/axia-robot-safety-ci-public"
            and os.environ.get("GITHUB_ACTOR")=="silverbjin"
            and bridge.PIN==BASE):
        report["reason"]="PROTECTED_CI_CONTEXT_REQUIRED"
        print("AXIA_PR52_REAL_G00 "+json.dumps(report,sort_keys=True),flush=True)
        return 3
    bridge.PIN=PIN
    try:
        private=bridge.validate_private_commit(private_root)
        report["private_sha_verified"]=True
        env=bridge.private_runtime_env(private,os.environ)
        env.update(CI="true",AXIA_P0_SIM_ONLY="1",GITHUB_SHA=PIN,
                   AXIA_T08_CLOUD_G00_OPT_IN="YES_SIM_ONLY",
                   AXIA_T08_CLOUD_EXPECTED_PRIVATE_SHA=PIN,
                   AXIA_T08_SCENARIO="g00",AXIA_T08_MAX_RUNS="1",
                   AXIA_T08_FAULT_APPROVED="NO",
                   AXIA_NAV2_USE_COMPOSITION="False",
                   LIBGL_ALWAYS_SOFTWARE="1",QT_QPA_PLATFORM="offscreen")
        with tempfile.TemporaryDirectory(prefix="axia_pr52_live_g00_",
                 dir=os.environ.get("RUNNER_TEMP") or None) as t:
            tmp=Path(t)
            overlay=tmp/"official-nav2-overlay"
            bridge.scrubbed_run("UPSTREAM_OFFICIAL_NAV2_OVERLAY",
                ["bash","scripts/build_official_nav2_lifecycle_overlay.sh",str(overlay)],
                private,env,tmp,1200)
            env["AXIA_NAV2_LIFECYCLE_OVERLAY_SETUP"]=str(overlay/"install/setup.bash")
            goals=set()
            for i in (1,2,3):
                run=private/"results"/("pr52-cloud-g00-"+str(i)+"-"+str(os.getpid()))
                env["AXIA_T08_EXACT_RUN_DIR"]=str(run)
                log=tmp/("g00_"+str(i)+".private.log")
                timed_out=False
                with log.open("wb") as out:
                    proc=subprocess.Popen(
                        ["bash","scripts/run_p1_t08_wsl2_field_capture.sh"],
                        cwd=private,env=env,stdout=out,stderr=subprocess.STDOUT,
                        start_new_session=True)
                    try:
                        code=proc.wait(timeout=1400)
                    except subprocess.TimeoutExpired:
                        timed_out=True
                        try:os.killpg(proc.pid,signal.SIGTERM)
                        except ProcessLookupError:pass
                        try:code=proc.wait(timeout=30)
                        except subprocess.TimeoutExpired:
                            try:os.killpg(proc.pid,signal.SIGKILL)
                            except ProcessLookupError:pass
                            code=124
                child=run/"cold_run_01"
                row={"run":i,"exit":code if code in (0,2,3,124,130,143) else 127,
                     "block_phase":_blocked_phase(log),
                     "startup":_status(child/"startup_verdict.json"),
                     "start_ack":_status(child/"start_ack.json"),
                     "field_gate":_status(child/"r05_bound_pre_send.json"),
                     "shutdown_control":_status(child/"shutdown_control.json"),
                     "goal_trace":_status(child/"live_result.json"),
                     "shutdown":_status(child/"shutdown_verdict.json"),
                     "timeout":timed_out}
                try:
                    sys.path.insert(0,str(private))
                    from tools.p1_t08_local_batch import classify_g00_evidence
                    from tools.p1_t08_raw_custody import assess_raw_g00
                    row["r05_reason_codes"]=_private_r05_codes(child,private,PIN)
                    candidate=classify_g00_evidence(run,expected_sha=PIN)
                    raw=assess_raw_g00(run,source_sha=PIN)
                    row["sealed_goal"]=candidate.get("status")=="R06_G00_EVIDENCE_CANDIDATE"
                    row["sealed_raw_bag"]=raw.get("status")=="R06_RAW_CUSTODY_REVIEW_PENDING"
                    if (code==3 and row["startup"]=="SMOKE_READY"
                            and row["start_ack"]=="START_ACK_VERIFIED"
                            and row["goal_trace"]=="PASS"
                            and row["shutdown"]=="SHUTDOWN_CLEAN"
                            and row["sealed_goal"] and row["sealed_raw_bag"]
                            and candidate.get("goal_uuid") not in goals):
                        goals.add(candidate["goal_uuid"])
                        row["candidate"]=True
                    else:
                        row["candidate"]=False
                except Exception:
                    row["candidate"]=False
                    row["evidence_classification"]="BLOCKED"
                report["runs"].append(row)
                print("AXIA_PR52_REAL_G00_RUN "+json.dumps(row,sort_keys=True),flush=True)
                if not row["candidate"]:break
            report["three_independent_runs"]=len(goals)==3
            report["real_goal_verified"]=len(goals)==3
            report["gazebo_executed"]=any(r["startup"]=="SMOKE_READY" for r in report["runs"])
            if report["three_independent_runs"]:
                report["status"]="CLOUD_G00_3X_CANDIDATE_REVIEW_PENDING"
    except bridge.GateBlocked:
        report["reason"]="PROTECTED_SOURCE_OR_OVERLAY_BLOCKED"
    except Exception:
        report["reason"]="PRIVATE_RUNTIME_ERROR"
    print("AXIA_PR52_REAL_G00 "+json.dumps(report,sort_keys=True),flush=True)
    return 0 if report["status"]=="CLOUD_G00_3X_CANDIDATE_REVIEW_PENDING" else 3


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--private-root",required=True,type=Path)
    args=parser.parse_args()
    raise SystemExit(run(args.private_root))
