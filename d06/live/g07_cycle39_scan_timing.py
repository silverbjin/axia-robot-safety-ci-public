#!/usr/bin/env python3
"""P2 wall-clock scan delivery triage; original 0.4107s observer gap is NOT a Guard event.

Only compare *proven same-clock wall/monotonic period measurements*. Gazebo
sim-time header deltas must not be silently compared with 300ms wall TTL.
No ROS, Goal, cmd_vel, CollisionMonitor or safety-state modification.
"""
from __future__ import annotations
import math


def classify_scan_periods(*, observer_gap_wall_s: float | None,
                          source_gap_wall_s: float | None = None,
                          bridge_gap_wall_s: float | None = None,
                          supervisor_gap_wall_s: float | None = None,
                          comparable_clock: bool = False,
                          scan_ttl_s: float = 0.30) -> dict:
    fields = {"observer": observer_gap_wall_s, "source": source_gap_wall_s,
              "bridge": bridge_gap_wall_s, "supervisor": supervisor_gap_wall_s}
    result = {"status": "OBSERVER_ONLY_UNATTRIBUTED",
              "safety_ttl_breach_proven": False, "safety_stop_tested": False,
              "formal_owner_l3_accepted": False, "scan_ttl_s": scan_ttl_s}
    if scan_ttl_s <= 0:
        return {**result, "status": "INVALID_TTL_CONFIG"}
    for name, val in fields.items():
        if val is not None and (not isinstance(val, (int, float))
                                or not math.isfinite(val) or val < 0):
            return {**result, "status": "INVALID_PERIOD_INPUT", "field": name}
    if any(fields[k] is not None for k in ("source", "bridge", "supervisor")) and not comparable_clock:
        return {**result, "status": "CLOCK_DOMAINS_UNVERIFIED"}
    if fields["supervisor"] is None or fields["bridge"] is None or fields["source"] is None:
        return result
    # Only a measured Supervisor *input delivery* gap is a 300ms TTL
    # candidate. A real Guard transition still needs original safety evidence.
    if fields["source"] > scan_ttl_s:
        return {**result, "status": "SOURCE_DELIVERY_GAP_OVER_300MS",
                "safety_ttl_breach_proven": fields["supervisor"] > scan_ttl_s}
    if fields["bridge"] > scan_ttl_s:
        return {**result, "status": "BRIDGE_DELIVERY_GAP_OVER_300MS",
                "safety_ttl_breach_proven": fields["supervisor"] > scan_ttl_s}
    if fields["supervisor"] > scan_ttl_s:
        return {**result, "status": "SUPERVISOR_DELIVERY_GAP_OVER_300MS",
                "safety_ttl_breach_proven": True}
    return {**result, "status": "ALL_OBSERVED_PERIODS_WITHIN_300MS",
            "safety_ttl_breach_proven": False}


if __name__ == "__main__":
    raise SystemExit("Offline timing triage only. No real G07 safety TTL is certified.")
