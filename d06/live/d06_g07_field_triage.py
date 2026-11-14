#!/usr/bin/env python3
"""D06 read-only G07 Owner first-failure report; never starts ROS or issues Goal.

No safety acceptance is possible from this educational compatibility layer.
P4 G11 sealed Owner raw/RMW report remains the authoritative private diagnosis.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

CM_TTL_S = 0.15  # DIAGNOSTIC CONST; never modifies actual Guard timeout.

def _number(x):
    return type(x) in (float, int) and math.isfinite(x) and x >= 0

def classify_owner_field(record: dict) -> dict:
    """Fail closed; retain first observed pre-Guard interval vs first internal latch.

    Observed callback gap cannot alone attribute CM publisher vs DDS vs executor.
    """
    first = record.get("first_timing_violation")
    guard = record.get("first_guard_latch")
    skew = record.get("cm_guard_receive_skew")
    out = {
        "schema": "axia.d06.g07_field_first_failure_v1",
        "status": "INCONCLUSIVE_OWNER_ORIGINAL_NOT_FULLY_VERIFIED",
        "first_channel": None,
        "first_interval_sec": None,
        "guard_latch_cm_age_sec": None,
        "guard_receive_lag_possible": False,
        "cm_publisher_stopped_proven": False,
        "goal_completion_verified": False,
        "safety_pass": False,
        "owner_l3_accepted": False,
        "certified_estop": False,
        "notice": "Use original P4 RMW source/receive and actual ROS bag for attribution",
    }
    if not isinstance(record, dict):
        return out
    if isinstance(first, dict):
        gap = first.get("first_violation_sec")
        cap = first.get("limit_sec")
        if first.get("channel") == "pre_guard" and _number(gap) and _number(cap):
            out["first_channel"] = "pre_guard"
            out["first_interval_sec"] = gap
    if not isinstance(guard, dict) or not _number(guard.get("cm_age_sec")):
        if record.get("status") == "BLOCKED":
            out["status"] = "HOLD_G07_UNCLASSIFIED_FIRST_FAILURE"
        return out
    age = guard["cm_age_sec"]
    out["guard_latch_cm_age_sec"] = age
    if (guard.get("reason") == "UPSTREAM_STALE_AFTER_MOTION"
            and age > CM_TTL_S):
        out["status"] = "HOLD_G07_GUARD_CM_DELIVERY_TTL"
        if isinstance(skew, dict):
            guard_seen = skew.get("guard_cm_age_at_latch_sec")
            observer_seen = skew.get("observer_cm_age_at_latch_sec")
            newer = skew.get("observer_newer_cm_samples")
            out["guard_receive_lag_possible"] = (
                _number(guard_seen) and _number(observer_seen)
                and type(newer) is int and newer > 0
                and observer_seen < guard_seen
            )
    else:
        out["status"] = "HOLD_G07_OTHER_LATCH_OR_UNVERIFIED"
    return out

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live-result", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        source = args.live_result
        if source.is_symlink() or not source.is_file():
            raise ValueError("original live result missing or symlink")
        report = classify_owner_field(json.loads(source.read_text(encoding="utf-8")))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Never replace an existing report or write to protected Owner archive.
        with args.output.open("x", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print("D06_G07_POSTRUN_TRIAGE "+json.dumps({
            "status": report["status"],
            "first_channel": report["first_channel"],
            "first_interval_sec": report["first_interval_sec"],
            "guard_latch_cm_age_sec": report["guard_latch_cm_age_sec"],
            "safety_pass": False,
        }, sort_keys=True), flush=True)
        return 0 if report["status"].startswith("HOLD_") else 3
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print("D06_G07_POSTRUN_TRIAGE_BLOCKED "+
              type(exc).__name__+":"+str(exc), flush=True)
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
