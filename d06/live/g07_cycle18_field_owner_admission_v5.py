#!/usr/bin/env python3
"""Exact Owner field prior-Goal/first-Guard fail-closed admission.

Read-only, NO ROS, NO Goal, NO attempt lock writes. CI's Xvfb L2 success
is necessary but not sufficient when a previous Owner Goal exceeded Guard
150ms TTL. Existing locks and all Owner original evidence are immutable.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys

if __package__ in (None,""):
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from d06.live.g07_cycle16_owner_ci_gate_v4 import (
    verify_cycle16_gate,PRIVATE,CI_RUN)

EXPECTED_SCHEMA="axia.g07.field_first_transition_sanitized.v2"

def _num(v):
    return type(v) in (float,int) and math.isfinite(v) and v>=0

def _hold(status, **extra):
    return {"schema":"axia.g07.owner_field_first_failure_admission_v5",
            "status":status,"manual_attempt_allowed":False,
            "owner_l3_accepted":False,"full_demo_accepted":False,
            "certified_estop":False,"no_ros_no_goal":True,
            "field_safety_ttl_repaired_and_verified":False, **extra}

def assess_field_admission(ci_gate, field_evidence, home:Path):
    """Return first true blocker; never let a positive CI-only gate release a Goal."""
    ci=verify_cycle16_gate(ci_gate)
    if ci["manual_attempt_allowed"] is not True:
        return _hold("CI_L2_EVIDENCE_INVALID_HOLD")
    if not isinstance(home,Path) or home.is_symlink() or not home.is_dir():
        return _hold("FIELD_HOME_UNTRUSTED_HOLD")
    root=home/".axia_g07_final_owner_attempts"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        return _hold("FIELD_ATTEMPT_STATE_UNTRUSTED_HOLD")
    attempt=root/f"{PRIVATE}-{CI_RUN}"
    if attempt.is_symlink() or (attempt.exists() and not attempt.is_dir()):
        return _hold("FIELD_ATTEMPT_STATE_UNTRUSTED_HOLD")
    prior=attempt.is_dir()
    if prior:
        state=attempt/"source.txt"
        if state.is_symlink():
            return _hold("FIELD_ATTEMPT_STATE_UNTRUSTED_HOLD")
        if state.is_file():
            try:
                exact={ln.strip() for ln in state.read_text(encoding="utf-8").splitlines()}
            except (OSError,UnicodeError):
                return _hold("FIELD_ATTEMPT_STATE_UNTRUSTED_HOLD")
            if not {f"private_sha={PRIVATE}",f"ci_run={CI_RUN}"}.issubset(exact):
                return _hold("FIELD_ATTEMPT_STATE_UNTRUSTED_HOLD")
    shared={"previous_same_source_attempt_exists":prior,
            "previous_attempt_preserved":True,
            "ci_l2_run_id":CI_RUN,
            "ci_l2_success_not_owner_acceptance":True}
    if type(field_evidence) is not dict:
        return _hold("FIELD_PREVIOUS_ATTEMPT_UNVERIFIED_HOLD"
                     if prior else "FIELD_HISTORY_UNVERIFIED_HOLD",**shared)
    e=field_evidence
    if (e.get("schema")!=EXPECTED_SCHEMA or
            e.get("source_sha")!=PRIVATE or e.get("ci_l2_run_id")!=CI_RUN or
            e.get("first_guard_transition")!="UPSTREAM_STALE_AFTER_MOTION" or
            e.get("previous_goal_observed") is not True or
            e.get("owner_l3_accepted") is not False or
            e.get("previous_attempt_not_safe_to_repeat") is not True or
            not _num(e.get("first_guard_cm_age_ms")) or
            not _num(e.get("guard_cm_hard_ttl_ms")) or
            e["guard_cm_hard_ttl_ms"]!=150.0 or
            not _num(e.get("first_cm_rmw_source_gap_ms")) or
            type(e.get("supervisor_publications_inside_cm_gap")) is not int or
            e["supervisor_publications_inside_cm_gap"]<0):
        return _hold("FIELD_FIRST_FAILURE_EVIDENCE_UNVERIFIED_HOLD",**shared)
    first=e["first_guard_cm_age_ms"]
    gap=e["first_cm_rmw_source_gap_ms"]
    t=e["guard_cm_hard_ttl_ms"]
    if first>t:
        return _hold("FIELD_PREVIOUS_GOAL_CM_TTL_BREACH_HOLD",
                    first_safety_transition=e["first_guard_transition"],
                    first_guard_cm_age_ms=first,guard_hard_ttl_ms=t,
                    first_cm_rmw_source_gap_ms=gap,
                    supervisor_publications_inside_cm_gap=e["supervisor_publications_inside_cm_gap"],
                    **shared)
    return _hold("FIELD_PREVIOUS_GOAL_FIRST_SAFETY_UNATTRIBUTED_HOLD",
                 first_safety_transition=e["first_guard_transition"],
                 first_guard_cm_age_ms=first,guard_hard_ttl_ms=t,
                 first_cm_rmw_source_gap_ms=gap,
                 supervisor_publications_inside_cm_gap=e["supervisor_publications_inside_cm_gap"],
                 **shared)

def _load_safe(p:Path):
    if p.is_symlink() or not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError,OSError,UnicodeError):
        return None

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--home",required=True,type=Path)
    p.add_argument("--ci-gate",required=True,type=Path)
    p.add_argument("--field-evidence",required=True,type=Path)
    args=p.parse_args()
    result=assess_field_admission(
        _load_safe(args.ci_gate),_load_safe(args.field_evidence),args.home)
    print("AXIA_G07_FIELD_OWNER_RELEASE_V5 "+
          json.dumps(result,sort_keys=True),flush=True)
    print("AXIA_G07_FIELD_FIRST_FAILURE_CI_REGRESSION_REQUIRED_OWNER_GOAL_NOT_AUTHORIZED",
          flush=True)
    print("AXIA_MVP_DEMO_ACCEPTED=HOLD",flush=True)
    return 3

if __name__=="__main__":
    raise SystemExit(main())
