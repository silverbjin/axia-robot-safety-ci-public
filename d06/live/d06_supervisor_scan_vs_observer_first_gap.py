#!/usr/bin/env python3
"""D06 first Observer sensor-gap versus native Supervisor watchdog audit.

Reads ONLY existing original G07 event ledger. Supervisor publishes its OWN
scan_callback_gaps_over_timeout in /axia/safety/state. Do not equate Observer
callback gaps to native safety-node callback gaps. Do not infer causal delivery
path to Guard. No ROS, DDS, Goal, timeout changes or private raw publication.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCAN_LIMIT_S = .30
ODOM_LIMIT_S = .30
NATIVE_WINDOW_S = .40


def _number(x):
    return type(x) in (int, float) and math.isfinite(x)


def _nonnegative_int(x):
    return type(x) is int and x >= 0


def _first_gap(rows, kind, goal_at, limit):
    candidates = sorted(
        (r for r in rows if isinstance(r, dict)
         and r.get("kind") == kind
         and _number(r.get("t")) and r["t"] >= goal_at),
        key=lambda r:r["t"])
    for prev, curr in zip(candidates, candidates[1:]):
        gap = curr["t"] - prev["t"]
        if gap > limit:
            return prev["t"], curr["t"], gap
    return None


def _native_snapshot(row):
    if not isinstance(row, dict):
        return None
    data = row.get("data")
    if not isinstance(data, dict):
        return None
    health = data.get("health_diagnostics")
    if not isinstance(health, dict):
        return None
    count = health.get("scan_callback_gaps_over_timeout")
    if not _nonnegative_int(count):
        return None
    return {
        "t":row["t"],
        "gap_count":count,
        "max_scan_gap":health.get("scan_callback_max_gap_sec"),
    }


def correlate(events):
    """Output retains ALL conservative original safety and witness caveats."""
    report = {
        "schema":"axia.d06.native_supervisor_vs_readonly_observer_v1",
        "status":"NO_EXACTLY_ONE_ACTUAL_GOAL",
        "observer_scan_first_gap_ms":None,
        "observer_odom_first_gap_ms":None,
        "supervisor_scan_status":"NOT_EVALUATED",
        "native_gap_counter_delta":None,
        "native_max_scan_gap_ms":None,
        "native_supervisor_before_age_ms":None,
        "native_supervisor_after_age_ms":None,
        "guard_latch_observed":False,
        "actual_guard_receive_delay_proven":False,
        "scan_breach_caused_guard_latch_proven":False,
        "safety_pass":False,
        "owner_l3_accepted":False,
        "certified_estop":False,
    }
    if not isinstance(events, list):
        return report
    goals = [e["t"] for e in events if isinstance(e, dict)
             and e.get("kind") == "owner_goal_published"
             and _number(e.get("t"))]
    if len(goals) != 1:
        return report
    goal = goals[0]
    scan = _first_gap(events, "scan", goal, SCAN_LIMIT_S)
    odom = _first_gap(events, "odom", goal, ODOM_LIMIT_S)
    report["observer_scan_first_gap_ms"] = (
        round(scan[2] * 1000, 6) if scan is not None else None)
    report["observer_odom_first_gap_ms"] = (
        round(odom[2] * 1000, 6) if odom is not None else None)
    report["status"] = "HOLD_FIRST_OBSERVER_BOUNDARY_NOT_NATIVE_ACCEPTANCE"

    guards = [e for e in events if isinstance(e, dict)
              and e.get("kind") == "guard"
              and _number(e.get("t")) and e["t"] >= goal
              and isinstance(e.get("data"), dict)]
    report["guard_latch_observed"] = any(
        row["data"].get("latched") is True for row in guards)
    if report["guard_latch_observed"]:
        report["status"] = "HOLD_NATIVE_GUARD_LATCH_OBSERVED"

    if scan is None:
        report["supervisor_scan_status"] = (
            "NO_OBSERVER_SCAN_DEADLINE_BREACH_IN_GOAL")
        return report

    start, end, _ = scan
    snapshots = sorted(
        (snap for row in events if isinstance(row, dict)
         and row.get("kind") == "supervisor"
         and _number(row.get("t"))
         and (snap := _native_snapshot(row)) is not None),
        key=lambda item:item["t"])
    before = [v for v in snapshots
              if 0 <= start - v["t"] <= NATIVE_WINDOW_S
              and v["t"] >= goal]
    after = [v for v in snapshots
             if 0 <= v["t"] - end <= NATIVE_WINDOW_S]
    if not before or not after:
        report["supervisor_scan_status"] = "NO_MATCHING_NATIVE_SUPERVISOR_WINDOW"
        return report
    x = before[-1]
    y = after[0]
    report["native_supervisor_before_age_ms"] = round((start-x["t"])*1000, 3)
    report["native_supervisor_after_age_ms"] = round((y["t"]-end)*1000, 3)
    delta = y["gap_count"] - x["gap_count"]
    if delta < 0:
        report["supervisor_scan_status"] = "NATIVE_SUPERVISOR_COUNTER_RESET_UNVERIFIED"
        return report
    report["native_gap_counter_delta"] = delta
    max_gap=y["max_scan_gap"]
    if _number(max_gap) and max_gap >= 0:
        report["native_max_scan_gap_ms"] = round(max_gap*1000, 3)
    if delta > 0:
        report["supervisor_scan_status"] = "NATIVE_SUPERVISOR_SCAN_GAP_CORROBORATED"
    else:
        report["supervisor_scan_status"] = (
            "OBSERVER_SCAN_GAP_NOT_REPRODUCED_IN_SUPERVISOR")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.events.is_symlink():
            raise ValueError("SYMLINK")
        rows = [json.loads(line) for line in
                args.events.read_text(encoding="utf-8").splitlines()
                if line.strip()]
    except (OSError, UnicodeError, ValueError, TypeError):
        rows = []
    outcome = correlate(rows)
    print("D06_G07_FIRST_OBSERVER_VS_NATIVE_SUPERVISOR "
          + json.dumps(outcome, sort_keys=True), flush=True)
    # Read-only, never an acceptance decision or bypass of original L2 oracle.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
