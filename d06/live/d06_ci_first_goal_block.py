#!/usr/bin/env python3
"""Sanitize the first G07 moving-Goal BLOCKED stage for public CI.

Input: private, locally held ci_moving_goal_result.json; output: allowlisted
classification only. Never copy raw reason, UUIDs, bag paths or message bodies.
Independent native Guard and original safety/STOP/shutdown oracles always win.
No ROS, Goal, controller, or safety policy mutation.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "axia.d06.first_g07_blocked_goal_phase_v1"
PHASE = r"(HEALTH|DISCOVERY|GRAPH|ACTION|CLEAR|SLOW|STOP)"
GUARD_REASON_CODES = frozenset(("UPSTREAM_STALE_AFTER_MOTION",))


def classify_first_goal_block(report):
    result = {
        "schema": SCHEMA,
        "status": "HOLD_G07_RESULT_UNVERIFIED",
        "failure_class": "UNVERIFIED",
        "first_failed_phase": None,
        "first_native_transition": None,
        "native_guard_latch_observed": False,
        "safety_pass": False,
        "owner_l3_accepted": False,
        "certified_estop": False,
    }
    if not isinstance(report, dict) or report.get("status") != "BLOCKED":
        return result
    if report.get("goal_sent") is not True:
        result["status"] = "HOLD_G07_NO_MOVING_GOAL_CONFIRMED"
        return result

    # First native safety state overrides a later terminal exception or timeout.
    latch = report.get("first_guard_latch")
    if isinstance(latch, dict) and latch:
        result.update(status="HOLD_G07_FIRST_NATIVE_GUARD_LATCH",
                      failure_class="NATIVE_GUARD_FIRST",
                      native_guard_latch_observed=True)
        code = latch.get("reason")
        result["first_native_transition"] = (
            code if code in GUARD_REASON_CODES else "OTHER_NATIVE_GUARD_LATCH")
        return result

    # An actual initial timing violation cannot be hidden by the last error.
    first = report.get("first_timing_violation")
    if isinstance(first, dict) and first:
        result.update(status="HOLD_G07_FIRST_TIMING_VIOLATION",
                      failure_class="TIMING_FIRST",
                      first_failed_phase="TIMING")
        return result

    reason = report.get("reason")
    if not isinstance(reason, str):
        result["status"] = "HOLD_G07_BLOCK_REASON_UNVERIFIED"
        return result
    for prefix, classification in (
        (r"^RuntimeError:CI_MOVING_GOAL_TIMEOUT_", "PHASE_TIMEOUT"),
        (r"^RuntimeError:GOAL_TERMINATED_DURING_", "GOAL_TERMINATED"),
        (r"^RuntimeError:GUARD_LATCH_DURING_", "NATIVE_GUARD_FIRST"),
    ):
        match = re.match(prefix + PHASE + r"(?=\\W|$)", reason)
        if match:
            if classification == "NATIVE_GUARD_FIRST":
                result.update(status="HOLD_G07_FIRST_NATIVE_GUARD_LATCH",
                              failure_class=classification,
                              native_guard_latch_observed=True)
            else:
                result.update(status="HOLD_G07_FIRST_GOAL_PHASE_BLOCK",
                              failure_class=classification,
                              first_failed_phase=match.group(1))
            return result
    if reason.startswith("RuntimeError:ACTUAL_MOVING_GOAL_CI_ORACLE_"):
        result.update(status="HOLD_G07_FIRST_GOAL_PHASE_BLOCK",
                      failure_class="ORIGINAL_ORACLE_REJECTION",
                      first_failed_phase="ORACLE")
        return result
    result["status"] = "HOLD_G07_BLOCK_REASON_UNVERIFIED"
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args()
    try:
        if args.report.is_symlink():
            raise ValueError("SYMLINK_REFUSED")
        raw = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, TypeError):
        raw = None
    result = classify_first_goal_block(raw)
    print("D06_G07_FIRST_BLOCKED_GOAL_PHASE " +
          json.dumps(result, sort_keys=True), flush=True)
    # Diagnostic can never turn the private original oracle into accepted L2.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
