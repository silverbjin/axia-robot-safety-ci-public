#!/usr/bin/env python3
"""Read-only field G07 first-failure and persistent WSL2 release preflight.

This is *not* a Goal runner or a new safety controller. No ROS, no write,
no replay of owner data, no old-attempt reset. All candidate admissions stay
HOLD until a new exact private source and real L2 margin are approved.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re

SCHEMA="axia.g07.field_first_failure_sanitized.v1"
CM_HARD_MS=150
CM_RELEASE_TARGET_MS=120
SENSOR_HARD_MS=300
SENSOR_RELEASE_TARGET_MS=240

def _number(v):
    return type(v) in (int,float) and math.isfinite(v) and v>=0

def _blocked(status, **other):
    return {"status":status,"owner_attempt_eligible":False,
            "owner_l3_accepted":False,"certified_estop":False,
            "no_ros_no_goal":True, **other}

def inspect_persistent_home(home:Path, private_sha:str, ci_run:int):
    if not isinstance(home,Path) or not re.fullmatch(r"[a-f0-9]{40}",private_sha):
        return _blocked("BLOCKED_INVALID_SOURCE_OR_HOME")
    if type(ci_run) is not int or ci_run<=0:
        return _blocked("BLOCKED_INVALID_CI_RUN")
    if home.is_symlink() or not home.is_dir():
        return _blocked("BLOCKED_UNTRUSTED_HOME")
    root=home/".axia_g07_final_owner_attempts"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        return _blocked("BLOCKED_UNTRUSTED_ATTEMPT_STATE")
    prior=root/f"{private_sha}-{ci_run}"
    if prior.is_symlink() or (prior.exists() and not prior.is_dir()):
        return _blocked("BLOCKED_UNTRUSTED_ATTEMPT_STATE")
    if prior.is_dir():
        return _blocked("BLOCKED_EXISTING_FAILED_ATTEMPT",
                        previous_attempt_exists=True,
                        previous_attempt_preserved=True)
    return _blocked("NO_PRIOR_ATTEMPT", previous_attempt_exists=False)

def classify_guard_first_failure(record):
    if (not isinstance(record,dict) or record.get("schema")!=SCHEMA
            or not _number(record.get("cm_guard_age_sec"))
            or not _number(record.get("cm_ttl_sec"))
            or record["cm_ttl_sec"]!=0.15
            or record.get("first_transition")!="UPSTREAM_STALE_AFTER_MOTION"
            or record.get("phase")!="GOAL_WINDOW"
            or record.get("guard_last_emitted_is_zero") is not True):
        return {**_blocked("FIELD_FIRST_GUARD_EVIDENCE_INVALID_HOLD"),
                "first_failure":"UNVERIFIED"}
    age=record["cm_guard_age_sec"]
    ttl=record["cm_ttl_sec"]
    breach=age>ttl
    return {**_blocked("FIELD_GUARD_TTL_BREACH_OWNER_RELEASE_HOLD"
                      if breach else "FIELD_GUARD_FIRST_FAILURE_UNATTRIBUTED_HOLD"),
            "first_failure":"GUARD_INTERNAL_CM_TTL_BREACH" if breach else "UNVERIFIED",
            "first_transition":record["first_transition"],
            "limit_ms":round(ttl*1000,6),
            "actual_ms":round(age*1000,6),
            "exceeded_ms":round(max(0,age-ttl)*1000,6),
            "rmw_epoch_step_only_candidate":record.get("cm_rmw_epoch_jump_candidate") is True,
            "cm_publisher_stopped_proven":False,
            "guard_output_zero":True}

def evaluate_release(gate, field_record=None):
    from d06.live.g07_unified_final_owner_gate_v2 import verify_gate
    old=verify_gate(gate)
    if not old["manual_attempt_allowed"]:
        return _blocked("CI_SOURCE_OR_HARD_SAFETY_GATE_HOLD")
    if field_record is not None:
        prior=classify_guard_first_failure(field_record)
        if (field_record.get("source_sha")==gate.get("instructor_source_sha")
                and prior.get("first_failure")=="GUARD_INTERNAL_CM_TTL_BREACH"):
            return _blocked("FIELD_GUARD_TTL_BREACH_OWNER_RELEASE_HOLD",
                            field_first_failure=prior["first_failure"])
    values=[("cm_max_ms",CM_RELEASE_TARGET_MS),
            ("cm_rmw_source_max_ms",CM_RELEASE_TARGET_MS),
            ("guard_max_ms",CM_RELEASE_TARGET_MS),
            ("supervisor_max_ms",CM_RELEASE_TARGET_MS),
            ("scan_max_ms",SENSOR_RELEASE_TARGET_MS),
            ("odom_max_ms",SENSOR_RELEASE_TARGET_MS),
            ("clock_max_ms",SENSOR_RELEASE_TARGET_MS)]
    low=[k for k,target in values if not _number(gate.get(k)) or gate[k]>target]
    common={"ci_l2_scoped_pass":True,"safety_hard_cm_ms":CM_HARD_MS,
            "release_target_cm_ms":CM_RELEASE_TARGET_MS,
            "sensor_hard_ms":SENSOR_HARD_MS,
            "sensor_release_target_ms":SENSOR_RELEASE_TARGET_MS}
    if low:
        return _blocked("CI_L2_PASS_LOW_MARGIN",low_margin_channels=low,**common)
    # CI sample-level headroom is necessary, but WSLg, Guard native,
    # current persistent state and the historical field event still
    # require separate acceptance. This module never enables a Goal.
    return _blocked("CI_MARGIN_OK_FIELD_ENV_AND_NEW_SOURCE_UNVERIFIED",
                    low_margin_channels=[],**common)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--home",type=Path,required=True)
    p.add_argument("--private-sha",required=True)
    p.add_argument("--ci-run",type=int,required=True)
    p.add_argument("--gate",type=Path,required=True)
    p.add_argument("--field-fixture",type=Path)
    args=p.parse_args()
    try:
        if args.gate.is_symlink() or (args.field_fixture is not None and args.field_fixture.is_symlink()):
            raise ValueError("UNTRUSTED_EVIDENCE_SYMLINK")
        gate=json.loads(args.gate.read_text(encoding="utf-8"))
        field=json.loads(args.field_fixture.read_text(encoding="utf-8")) if args.field_fixture else None
        state=inspect_persistent_home(args.home,args.private_sha,args.ci_run)
        release=evaluate_release(gate,field)
        result={"schema":"axia.g07.field_readonly_preflight_v3",
                "state":state,"release":release,
                "status":(state["status"] if state["status"]!="NO_PRIOR_ATTEMPT"
                          else release["status"]),
                "ready_for_owner_one_attempt":False,"no_ros_no_goal":True}
    except (OSError,ValueError,UnicodeError,TypeError,KeyError):
        result={"schema":"axia.g07.field_readonly_preflight_v3",
                "status":"FIELD_PREFLIGHT_EVIDENCE_MISSING_HOLD",
                "ready_for_owner_one_attempt":False,"no_ros_no_goal":True}
    print("AXIA_G07_OWNER_FIELD_READONLY "+json.dumps(result,sort_keys=True))
    return 3

if __name__=="__main__":
    raise SystemExit(main())
