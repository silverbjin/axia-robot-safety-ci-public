#!/usr/bin/env python3
"""Read-only first-Guard-latch diagnosis for official Jazzy Collision Monitor.

Classifies whether observed continuous CM ZERO output is *compatible* with
Nav2's stop_pub_timeout intentional suppression. Never claims internal
stop_stamp or a DDS/publisher root cause, and never grants safety acceptance.
"""
import argparse
import json
import math
from pathlib import Path


HOLD = "CM_STOP_PUB_FIRST_BOUNDARY_UNVERIFIED"


def _number(x):
    return type(x) in (int, float) and math.isfinite(x)


def _base(status=HOLD):
    return {
        "schema": "axia.g07.cm_stop_pub_first_latch_v1",
        "status": status,
        "root_cause_confirmed": False,
        "cm_internal_stop_stamp_proven": False,
        "cm_publisher_internal_entry_proven": False,
        "guard_latch_overridden": False,
        "safety_ttl_changed": False,
        "certified_estop": False,
        "formal_safety_timing_accepted": False,
        "release": "HOLD",
    }


def _clock_at(clocks, host):
    # /clock is simulated time; callback t is host MONOTONIC. Interpolate
    # locally without subtracting timestamps from different clock domains.
    for before, after in zip(clocks, clocks[1:]):
        if before["t"] <= host <= after["t"]:
            gap = after["t"] - before["t"]
            if not 0 < gap <= .16 or not before["ns"] < after["ns"]:
                return None
            return before["ns"] + (host - before["t"]) / gap * (
                after["ns"] - before["ns"])
    return None


def classify(events, first_latch, *, stop_pub_timeout_sec):
    """Analyze actual CM ZERO suffix and first internal Guard stale latch.

    The matching signature is a candidate, never internal CM proof: official
    stop_stamp_ and the DDS publisher callback were not observed directly.
    """
    out = _base()
    if (not isinstance(events, list) or len(events) > 120000
            or not isinstance(first_latch, dict)
            or not _number(stop_pub_timeout_sec)
            or stop_pub_timeout_sec <= 0):
        return out
    tick = first_latch.get("tick_monotonic")
    cm_rx = first_latch.get("cm_rx_monotonic")
    cm_age = first_latch.get("cm_age_sec")
    if (first_latch.get("latched") is not True
            or first_latch.get("reason") != "UPSTREAM_STALE_AFTER_MOTION"
            or not all(_number(v) for v in (tick, cm_rx, cm_age))
            or not tick > cm_rx > 0
            or abs((tick - cm_rx) - cm_age) > .005
            or cm_age <= .150):
        return out
    out.update(guard_cm_age_ms=round(cm_age * 1000, 6),
               stop_pub_timeout_sec=stop_pub_timeout_sec)
    cm, clocks = [], []
    for item in events:
        if not isinstance(item, dict):
            continue
        t = item.get("t")
        if not _number(t):
            continue
        if item.get("kind") == "pre_guard" and t <= tick:
            vx, wz = item.get("vx"), item.get("wz")
            if _number(vx) and _number(wz):
                cm.append({"t": t,
                           "zero": abs(vx) <= 1e-9 and abs(wz) <= 1e-9})
        elif item.get("kind") == "clock" and _number(item.get("ns")):
            clocks.append({"t": t, "ns": item["ns"]})
    cm.sort(key=lambda x: x["t"])
    clocks.sort(key=lambda x: x["t"])
    if len(cm) < 5 or len(clocks) < 4 or not cm[-1]["zero"]:
        return out
    i = len(cm) - 1
    while i >= 0 and cm[i]["zero"]:
        i -= 1
    if i < 0 or len(cm) - i - 1 < 3:
        return out
    # Require an actual previously observed NONZERO CM output before ZERO.
    first_zero = cm[i + 1]["t"]
    last_zero = cm[-1]["t"]
    if tick <= last_zero or last_zero - first_zero < .05:
        return out
    relevant = [c for c in clocks if first_zero - .16 <= c["t"] <= tick + .16]
    if (len(relevant) < 3 or any(
            b["t"] <= a["t"] or b["ns"] <= a["ns"]
            for a, b in zip(relevant, relevant[1:]))):
        return out
    sim_start = _clock_at(clocks, first_zero)
    sim_last = _clock_at(clocks, last_zero)
    sim_tick = _clock_at(clocks, tick)
    if (sim_start is None or sim_last is None or sim_tick is None
            or not sim_start <= sim_last < sim_tick):
        return out
    elapsed = (sim_tick - sim_start) / 1e9
    last_elapsed = (sim_last - sim_start) / 1e9
    out.update(sim_zero_to_latch_sec=round(elapsed, 6),
               sim_zero_to_last_output_sec=round(last_elapsed, 6),
               observed_continuous_zero_samples=len(cm) - i - 1,
               observer_last_zero_to_latch_ms=round((tick - last_zero)*1000, 6),
               first_zero_host_monotonic_sec=round(first_zero, 6),
               last_zero_host_monotonic_sec=round(last_zero, 6))
    if (elapsed >= stop_pub_timeout_sec
            and last_elapsed <= stop_pub_timeout_sec + .15):
        out["status"] = "CM_STOP_PUB_TIMEOUT_COMPATIBLE_UNPROVEN"
    elif (elapsed + .08 < stop_pub_timeout_sec
          or last_elapsed > stop_pub_timeout_sec + .15):
        out["status"] = "CM_STOP_PUB_TIMEOUT_TIMING_INCOMPATIBLE"
    return out


def _active_timeout(log):
    """Extract active native CM readback from *this* session, not YAML."""
    marker = "AXIA_G07_CM_NATIVE_ACTIVE_PARAMETER_READBACK "
    try:
        for line in Path(log).read_text(errors="replace")[-2_000_000:].splitlines():
            if marker not in line:
                continue
            data = json.loads(line.partition(marker)[2])
            if data.get("status") != "ACTIVE_CM_NATIVE_PARAMETER_READBACK_PASS":
                continue
            val = data.get("actual", {}).get("stop_pub_timeout")
            if _number(val) and 0 < val < 120:
                return val
    except (OSError, ValueError, TypeError):
        pass
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--events", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--readback-log", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    v = _base()
    try:
        rows = [json.loads(line) for line in a.events.read_text().splitlines()]
        report = json.loads(a.report.read_text())
        timeout = _active_timeout(a.readback_log)
        v = classify(rows, report.get("first_guard_latch"),
                     stop_pub_timeout_sec=timeout)
        v["native_cm_stop_pub_timeout_readback_verified"] = timeout is not None
    except (OSError, ValueError, TypeError):
        v["diagnostic_input"] = "MISSING_OR_MALFORMED"
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(v, sort_keys=True, indent=2) + "\n")
    print("AXIA_G07_CM_STOP_PUB_FIRST_LATCH " +
          json.dumps(v, sort_keys=True), flush=True)
    print("G07_CM_GUARD_ROOT_CAUSE=UNDETERMINED RELEASE=HOLD CERTIFIED_ESTOP=false")
    return 0  # Diagnostic tool never grants safety admission.


if __name__ == "__main__":
    raise SystemExit(main())
