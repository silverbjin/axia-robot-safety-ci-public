#!/usr/bin/env python3
"""Private live G00 simulation bridge. Never writes Goal, Twist or Fault itself.
Executes the PINNED private guarded Gazebo field runner in protected Actions,
observes sealed rosbag2 and real Goal UUID/terminal, prints only allowlisted
status. No private source, logs, rosbag or stdout is uploaded to public CI.
"""
import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import private_ci_bridge as bridge

PIN = "5a458a0ca8533b77e548dbb500b00fbe70d61942"
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
    blocked_lines=[line for line in content.splitlines() if "[BLOCKED]" in line]
    if not blocked_lines:
        return "NO_RECORDED_BLOCKED_LINE"
    for marker,code in rules:
        if any(marker in line for line in blocked_lines):
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
            session_id=att.get("session_id"),now_monotonic_ns=now,
            require_live_start_boundary=True)
        codes=result.get("reasons") or []
        return [c if c in _SAFE_R05 else "UNRECOGNIZED" for c in codes][:12]
    except (OSError,ValueError,TypeError,KeyError,ImportError):
        return ["R05_DIAGNOSTIC_UNAVAILABLE"]


# Read-only, allowlisted diagnostic ONLY. The private R06 custody validator
# remains the sole admission gate and all required topics stay unchanged.
_EXPECTED_BAG_TOPICS=('/clock','/odom','/cmd_vel','/axia/safety/state',
                      '/navigate_to_pose/_action/status')



def _fake_preflight_diagnostic(run):
    """Only public stage enums/counts, never private stdout, tests or paths."""
    summary_dir=Path(run)/"partial"
    if not summary_dir.is_dir() or summary_dir.is_symlink():
        return {"status":"PREFLIGHT_SUMMARY_MISSING"}
    files=list(summary_dir.glob("p1-*/summary.json"))
    if len(files)!=1 or files[0].is_symlink():
        return {"status":"PREFLIGHT_SUMMARY_MISSING"}
    try:
        summary=json.loads(files[0].read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError):
        return {"status":"PREFLIGHT_SUMMARY_INVALID"}
    if not isinstance(summary,dict) or not isinstance(summary.get("stage_results"),list):
        return {"status":"PREFLIGHT_SUMMARY_INVALID"}
    allowed_stages=frozenset(("G02_UNIT","G04_UNIT","G03_ROS_FAKE","G04_ROS_FAKE"))
    allowed_status=frozenset(("PASS","FAIL","ERROR","BLOCKED","INCONCLUSIVE","NOT_RUN"))
    report={"status":"PREFLIGHT_STAGE_DIAGNOSTIC_ONLY",
            "first_nonpassing_stage":"NONE","first_nonpassing_status":"NONE",
            "failed_case_count":0,"stage_counts":{}}
    for item in summary["stage_results"][:30]:
        if not isinstance(item,dict):
            continue
        stage=item.get("stage_id")
        status=item.get("status")
        if stage not in allowed_stages or status not in allowed_status:
            continue
        count=report["stage_counts"].setdefault(stage,{"passes":0,"nonpasses":0})
        count["passes" if status=="PASS" else "nonpasses"]+=1
        fails=item.get("failures",0)
        if type(fails) is int and 0<=fails<=1000:
            report["failed_case_count"]+=fails
        if status!="PASS" and report["first_nonpassing_stage"]=="NONE":
            report["first_nonpassing_stage"]=stage
            report["first_nonpassing_status"]=status
    blocked=summary.get("blocked_reason")
    if blocked=="SOURCE_COMMIT_MISSING_OR_CI_MISMATCH":
        report["blocked_code"]="SOURCE_PIN_MISMATCH"
    elif blocked=="ROS_JAZZY_NOT_SOURCED":
        report["blocked_code"]="ROS_SETUP_MISSING"
    elif isinstance(blocked,str) and blocked.startswith("ROS_ACTION_DEPENDENCY_MISSING:"):
        report["blocked_code"]="ROS_ACTION_DEPENDENCY_MISSING"
    return report



def _shutdown_failure_diagnostic(child):
    """Map private lifecycle shutdown receipts to a fixed safe status vocabulary."""
    result={"reason_code":"DIAGNOSTIC_UNAVAILABLE",
            "manager_ack_navigation":False,
            "manager_ack_localization":False,
            "manager_active_after_timeout":"UNKNOWN",
            "amcl_state":"UNKNOWN","map_server_state":"UNKNOWN",
            "lifecycle_acknowledged":False,
            "fatal_detected":False}
    try:
        ctrl=Path(child)/"shutdown_control.json"
        verdict=Path(child)/"shutdown_verdict.json"
        if (not ctrl.is_file() or ctrl.is_symlink()
                or not verdict.is_file() or verdict.is_symlink()):
            return result
        control=json.loads(ctrl.read_text(encoding="utf-8"))
        stop=json.loads(verdict.read_text(encoding="utf-8"))
        if not isinstance(control,dict) or not isinstance(stop,dict):
            return result
        allowed_reasons={
            "SIMULATION_MARKERS_MISSING","ROS_JAZZY_REQUIRED",
            "INVALID_TIMEOUT","PREPAUSE_NOT_AUTHORIZED",
            "NAVIGATION_SERVICE_UNAVAILABLE","LOCALIZATION_SERVICE_UNAVAILABLE",
            "NAVIGATION_SERVICE_RESPONSE_TIMEOUT","LOCALIZATION_SERVICE_RESPONSE_TIMEOUT",
            "NAVIGATION_SERVICE_EXCEPTION","LOCALIZATION_SERVICE_EXCEPTION",
            "NAVIGATION_SERVICE_REPORTED_FAILURE","LOCALIZATION_SERVICE_REPORTED_FAILURE",
            "NAVIGATION_PREPAUSE_SERVICE_RESPONSE_TIMEOUT",
            "LOCALIZATION_PREPAUSE_SERVICE_RESPONSE_TIMEOUT",
            "SHUTDOWN_EXCEPTION","BOTH_MANAGERS_ACKNOWLEDGED_SHUTDOWN",
        }
        val=control.get("reason")
        result["reason_code"]=val if val in allowed_reasons else "UNCLASSIFIED_SHUTDOWN_BLOCK"
        managers=control.get("managers")
        managers=managers if isinstance(managers,dict) else {}
        for key in ("navigation","localization"):
            entry=managers.get(key)
            result["manager_ack_"+key]=(isinstance(entry,dict)
                                         and entry.get("success") is True)
        loc=managers.get("localization")
        loc=loc if isinstance(loc,dict) else {}
        allowed_probe={"ACTIVE","INACTIVE","NO_RESPONSE","SERVICE_UNAVAILABLE",
                       "SERVICE_ERROR","INVALID_RESPONSE","UNKNOWN"}
        observed=loc.get("manager_active_after_timeout")
        if observed in allowed_probe:
            result["manager_active_after_timeout"]=observed
        states=loc.get("managed_nodes_after_timeout")
        states=states if isinstance(states,dict) else {}
        allowed_states={"UNCONFIGURED","INACTIVE","ACTIVE","FINALIZED",
                        "SERVICE_UNAVAILABLE","NO_RESPONSE","SERVICE_ERROR","UNKNOWN"}
        for key in ("amcl","map_server"):
            state=states.get(key)
            if state in allowed_states:
                result[key+"_state"]=state
        result["lifecycle_acknowledged"]=(stop.get("lifecycle_shutdown_acknowledged") is True)
        fatal=stop.get("fatal_signatures")
        result["fatal_detected"]=isinstance(fatal,list) and bool(fatal)
    except (OSError,ValueError,UnicodeError,TypeError):
        return {"reason_code":"DIAGNOSTIC_UNAVAILABLE"}
    return result



def _verified_shared_preflight_proof(private,run,expected_sha,*,verifier=None):
    """Only a same-job, signed, source-bound ROS-fake proof can be reused.

    This does not cache Gazebo/Map/TF/CM readiness, Goal permission or Shutdown.
    Invalid proof safely falls back to the complete fresh ROS-fake preflight.
    """
    proof=Path(run)/"preflight_proof.json"
    if proof.is_symlink() or not proof.is_file():
        return None
    try:
        if verifier is None:
            from tools.p1_t08_preflight import verify_proof as verifier
        checked=verifier(proof=proof,repo=Path(private))
        if (not isinstance(checked,dict)
                or checked.get("source_commit")!=expected_sha
                or checked.get("stage_count")!=12
                or checked.get("gate_accepted") is not False
                or checked.get("preflight")!="VERIFIED_REUSED"):
            return None
        return str(proof)
    except Exception:
        # A missing/corrupt/expired/mismatched proof is NOT a passing test.
        return None


def _raw_bag_blocker(run, source_sha):
    part=Path(run)/'cold_run_01'
    bag=part/'rosbag2'
    manifest=part/'checksums.sha256'
    source=Path(run)/'source_commit.txt'
    if not source.is_file() or source.is_symlink() or source.read_text().strip()!=source_sha:
        return {'status':'SOURCE_MARKER_INVALID'}
    if not manifest.is_file() or manifest.is_symlink():
        return {'status':'CHECKSUM_MANIFEST_MISSING'}
    if not bag.is_dir() or bag.is_symlink():
        return {'status':'ROS_BAG_DIRECTORY_MISSING'}
    meta=bag/'metadata.yaml'
    dbs=sorted(bag.glob('*.db3'))
    if not meta.is_file() or meta.is_symlink():
        return {'status':'ROS_BAG_METADATA_MISSING'}
    if not dbs:
        return {'status':'ROS_BAG_SQLITE_MISSING'}
    try:
        if 'sqlite3' not in meta.read_text(encoding='utf-8'):
            return {'status':'ROS_BAG_STORAGE_ID_INVALID'}
        sealed={}
        for entry in manifest.read_text(encoding='utf-8').splitlines():
            parts=entry.split('  ',1)
            if len(parts)!=2:
                return {'status':'CHECKSUM_MANIFEST_INVALID'}
            digest,relative=parts
            if (len(digest)!=64 or any(ch not in '0123456789abcdef' for ch in digest)
                or relative in sealed or relative.startswith('/')
                or any(x in ('','.','..') for x in relative.split('/'))):
                return {'status':'CHECKSUM_MANIFEST_INVALID'}
            sealed[relative]=digest
        for f in [meta]+dbs:
            key=f.relative_to(part).as_posix()
            if (f.is_symlink() or key not in sealed
                    or hashlib.sha256(f.read_bytes()).hexdigest()!=sealed[key]):
                return {'status':'BAG_CHECKSUM_OR_MANIFEST_MISMATCH'}
        counts=dict.fromkeys(_EXPECTED_BAG_TOPICS,0)
        for db in dbs:
            with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as con:
                con.execute('PRAGMA query_only = ON')
                if con.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                    return {'status':'SQLITE_INTEGRITY_INVALID'}
                for topic, count in con.execute(
                    'SELECT topics.name, COUNT(messages.id) FROM topics '
                    'JOIN messages ON messages.topic_id=topics.id '
                    'GROUP BY topics.name'):
                    if topic in counts:
                        counts[topic]+=count
        missing=[t for t in _EXPECTED_BAG_TOPICS if counts[t]<1]
        if missing:
            return {'status':'REQUIRED_TOPICS_NOT_RECORDED',
                    'missing_expected_topics':missing}
        return {'status':'R06_POLICY_REJECTION_NOT_CLASSIFIED'}
    except (OSError,UnicodeError,ValueError,IndexError,sqlite3.DatabaseError):
        return {'status':'ROS_BAG_READ_ERROR'}


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
            env.pop("AXIA_T08_PREFLIGHT_PROOF",None)
            goals=set()
            approved_runs=[]
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
                    row["raw_bag_blocker"]=(
                        {'status':'NONE'} if row["sealed_raw_bag"]
                        else _raw_bag_blocker(run,PIN))
                    if (code==3 and row["startup"]=="SMOKE_READY"
                            and row["start_ack"]=="START_ACK_VERIFIED"
                            and row["goal_trace"]=="PASS"
                            and row["shutdown"]=="SHUTDOWN_CLEAN"
                            and row["sealed_goal"] and row["sealed_raw_bag"]
                            and candidate.get("goal_uuid") not in goals):
                        goals.add(candidate["goal_uuid"])
                        approved_runs.append(run)
                        row["candidate"]=True
                    else:
                        row["candidate"]=False
                except Exception:
                    row["candidate"]=False
                    row["evidence_classification"]="BLOCKED"
                if row["block_phase"]=="PREFLIGHT_FAKE_ROS_FAILED":
                    row["preflight_diagnostic"]=_fake_preflight_diagnostic(run)
                if row["shutdown"]!="SHUTDOWN_CLEAN":
                    row["shutdown_diagnostic"]=_shutdown_failure_diagnostic(child)

                if row["candidate"] and i<3:
                    # Only after the preceding real G00 passed every original
                    # Startup/Goal/Shutdown/raw-bag gate. The next script
                    # verifies the HMAC, original stage JUnit, SHA and RMW.
                    proof=_verified_shared_preflight_proof(private,run,PIN)
                    if proof is None:
                        env.pop("AXIA_T08_PREFLIGHT_PROOF",None)
                        row["next_preflight"]="FRESH_ROS_FAKE_REQUIRED"
                    else:
                        env["AXIA_T08_PREFLIGHT_PROOF"]=proof
                        row["next_preflight"]="SIGNED_SAME_RUNNER_PROOF_VERIFIED"
                report["runs"].append(row)
                print("AXIA_PR52_REAL_G00_RUN "+json.dumps(row,sort_keys=True),flush=True)
                if not row["candidate"]:break
            report["three_independent_runs"]=len(goals)==3
            report["real_goal_verified"]=len(goals)==3
            report["gazebo_executed"]=any(r["startup"]=="SMOKE_READY" for r in report["runs"])
            if report["three_independent_runs"]:
                # Fail closed if original 3x bag/Goal custody cannot be encrypted
                # and uploaded. A later independent CI job checks remote cipher.
                from pr52_gdrive_custody import CustodyBlocked, seal
                try:
                    upload=seal(private,approved_runs,os.environ)
                    report["encrypted_drive_upload"]=upload["status"]
                    report["status"]="CLOUD_G00_3X_AGE_CIPHER_UPLOADED"
                except CustodyBlocked as fault:
                    report["status"]="CLOUD_G00_3X_CUSTODY_BLOCKED"
                    report["custody_reason"]=fault.code
    except bridge.GateBlocked:
        report["reason"]="PROTECTED_SOURCE_OR_OVERLAY_BLOCKED"
    except Exception:
        report["reason"]="PRIVATE_RUNTIME_ERROR"
    print("AXIA_PR52_REAL_G00 "+json.dumps(report,sort_keys=True),flush=True)
    return 0 if report["status"]=="CLOUD_G00_3X_AGE_CIPHER_UPLOADED" else 3


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--private-root",required=True,type=Path)
    args=parser.parse_args()
    raise SystemExit(run(args.private_root))
