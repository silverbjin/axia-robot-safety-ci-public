#!/usr/bin/env python3
"""Fail-closed AXIA sync-FIRST policy for one G07 Owner L3 validation candidate.

The attestation is checked against LIVE GitHub Actions run/jobs data, the
owner's PRIVATE WSL2 profile raw SHA256 and the ACTUAL private Git diff.
It never declares moving Goal or formal safety acceptance, nor sends a Goal.
A source changed outside the narrow verified no-Goal L2 scope must repeat
environment-pinned L2 and update the attestation intentionally.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PROFILE_MAX_AGE_DAYS = 7
OWNER_PROFILE_SHA = "dedd807884507222e2361f70e31ed47c8b4be7701b751a35e7f4a796ba4dd7b8"
PARITY_RUN_ID = 42777095584
PARITY_PUBLIC_SHA = "86c0a8ad6f32b32641f42cc3ba87fb742cd594b4"
PARITY_SOURCE_SHA = "167027902234202f7a975333759944b7ddbd8ad7"
TARGET_SOURCE_SHA = "a9a33cc32586e4a30843efcf9172bdaade85d8ea"
SAFE_SOURCE_DIFF = (
    "tests/unit/test_p2_g07_mvp_motion_gate.py",
    "tools/p2_l3_acceptance_contract.py",
    "tools/p2_l3_live_session.py",
)
MUST_PASS = (
    "Install official Jazzy/Harmonic dependencies once; pin exact Owner apt core; compare versions and hashes",
    "Checkout EXACT private P1+P2 source after parity",
    "Actual Gazebo Harmonic physical clear slow stop with P1+P2 startup (NO Goal)",
)


def _utc(v):
    if not isinstance(v, str):
        return None
    try:
        stamp = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return None
        return stamp.astimezone(timezone.utc)
    except ValueError:
        return None


def _hold(reason):
    return {
        "status": "HOLD", "sync_status": "NOT_VERIFIED",
        "reason": reason, "no_goal_l2_proven": False,
        "moving_goal_proven": False,
        "formal_g07_accepted": False,
        "certified_estop": False,
    }


def evaluate(*, owner_profile, run, jobs, provenance, now=None):
    """Only allows Owner L3 trial readiness for a verified, narrow source delta."""
    if not all(isinstance(x, dict) for x in
               (owner_profile, run, jobs, provenance)):
        return _hold("EVIDENCE_SHAPE_INVALID")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        return _hold("INVALID_CLOCK")
    now = now.astimezone(timezone.utc)
    if (owner_profile.get("schema") != "axia_ros_jazzy_harmonic_env_v1" or
            owner_profile.get("profile_kind") != "wsl2_owner" or
            owner_profile.get("wsl2_detected") is not True):
        return _hold("WSL2_PROFILE_INVALID")
    captured = _utc(owner_profile.get("captured_utc"))
    if captured is None or not (0 <= (now - captured).total_seconds() <=
                                PROFILE_MAX_AGE_DAYS * 86400):
        return _hold("OWNER_PROFILE_STALE_RECAPTURE_REQUIRED")
    if (provenance.get("owner_profile_sha256") != OWNER_PROFILE_SHA or
            provenance.get("parity_run_owner_profile_sha256") != OWNER_PROFILE_SHA):
        return _hold("OWNER_PROFILE_SHA_NOT_ATTESTED")
    if (provenance.get("checked_source_sha") != TARGET_SOURCE_SHA or
            provenance.get("attested_source_sha") != PARITY_SOURCE_SHA):
        return _hold("PRIVATE_SOURCE_SHA_MISMATCH")
    changes = provenance.get("actual_source_changes")
    if (not isinstance(changes, list) or
            len(changes) != len(SAFE_SOURCE_DIFF) or
            sorted(changes) != sorted(SAFE_SOURCE_DIFF)):
        return _hold("SOURCE_CHANGE_INVALIDATES_PARITY_L2")
    if any(provenance.get(k) is not False for k in (
            "moving_goal_proven", "formal_g07_accepted", "certified_estop")):
        return _hold("UNSUPPORTED_SAFETY_CLAIM")
    if (provenance.get("parity_run_id") != PARITY_RUN_ID or
            provenance.get("parity_run_head_sha") != PARITY_PUBLIC_SHA or
            run.get("id") != PARITY_RUN_ID or run.get("head_sha") != PARITY_PUBLIC_SHA or
            run.get("status") != "completed" or run.get("conclusion") != "success"):
        return _hold("PARITY_CI_RUN_MISSING_OR_FAILED")
    full_name = (run.get("repository_full_name") or
                 (run.get("repository") or {}).get("full_name"))
    if full_name != "silverbjin/axia-robot-safety-ci-public":
        return _hold("PARITY_RUN_REPO_MISMATCH")
    started = _utc(run.get("created_at"))
    if started is None or started < captured or started > now:
        return _hold("PARITY_RUN_PREDATES_OWNER_PROFILE")
    job = next((j for j in jobs.get("jobs", [])
                if j.get("name") == "owner-userspace-parity"
                and j.get("conclusion") == "success"), None)
    if job is None:
        return _hold("PARITY_JOB_NOT_SUCCESS")
    success_steps = {
        s.get("name") for s in job.get("steps", [])
        if s.get("conclusion") == "success"
    }
    if not all(step in success_steps for step in MUST_PASS):
        return _hold("PINNED_ENV_OR_REAL_NO_GOAL_L2_MISSING")
    return {
        "status": "OWNER_L3_CANDIDATE",
        "sync_status": "VERIFIED",
        "reason": "OWNER_MATCHED_CORE_CI_AND_L2_WITH_SAFE_G07_ONLY_DELTA",
        "no_goal_l2_proven": True,
        "moving_goal_proven": False,
        "formal_g07_accepted": False,
        "certified_estop": False,
    }


def _read_json(path, max_bytes=2_000_000):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > max_bytes:
        raise ValueError("EVIDENCE_MISSING_OR_OVERSIZED")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner", required=True, type=Path)
    p.add_argument("--run", required=True, type=Path)
    p.add_argument("--jobs", required=True, type=Path)
    p.add_argument("--private-checkout", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        owner_bytes = args.owner.read_bytes()
        profile = _read_json(args.owner)
        real_hash = hashlib.sha256(owner_bytes).hexdigest()
        actual = subprocess.run(
            ["git", "-C", str(args.private_checkout), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=8).stdout.strip()
        diff = subprocess.run(
            ["git", "-C", str(args.private_checkout), "diff", "--name-only",
             PARITY_SOURCE_SHA, TARGET_SOURCE_SHA],
            check=True, capture_output=True, text=True, timeout=8).stdout.splitlines()
        if actual != TARGET_SOURCE_SHA:
            raise ValueError("PRIVATE_CHECKOUT_NOT_TARGET")
        prov = {
            "owner_profile_sha256": real_hash,
            "parity_run_owner_profile_sha256": OWNER_PROFILE_SHA,
            "checked_source_sha": actual,
            "attested_source_sha": PARITY_SOURCE_SHA,
            "actual_source_changes": diff,
            "parity_run_id": PARITY_RUN_ID,
            "parity_run_head_sha": PARITY_PUBLIC_SHA,
            "moving_goal_proven": False,
            "formal_g07_accepted": False,
            "certified_estop": False,
        }
        result = evaluate(owner_profile=profile, run=_read_json(args.run),
                          jobs=_read_json(args.jobs), provenance=prov)
    except (ValueError, OSError, json.JSONDecodeError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        result = _hold("EVIDENCE_OR_SOURCE_UNVERIFIABLE")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print("AXIA_CI_SYNC_FIRST=" + result["sync_status"])
    print("AXIA_CI_OWNER_REVIEW_STATUS=" + result["status"])
    print("AXIA_CI_OWNER_REVIEW_REASON=" + result["reason"])
    print("AXIA_CI_NO_GOAL_L2_PROVEN=" + str(result["no_goal_l2_proven"]).lower())
    print("AXIA_CI_MOVING_GOAL_PROVEN=false CERTIFIED_ESTOP=false")
    return 0 if result["status"] == "OWNER_L3_CANDIDATE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
