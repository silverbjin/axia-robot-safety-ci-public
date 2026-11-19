#!/usr/bin/env python3
"""Read-only D08/G07 first *actual Guard* TTL breach triage.

Only existing G07 owner raw event-log lines; no ROS, no publisher, no
automatic safety adjustment. Does not prove DDS or CM publisher causality.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

TTL_SEC = .150
TAG_LATCH = "AXIA_G07_PUBLIC_CI_FIRST_GUARD_LATCH_INTERNAL "
TAG_SKEW = "AXIA_G07_PUBLIC_CI_FIRST_CM_GUARD_RECEIPT_SKEW "


def _valid_age(x):
    return type(x) in (float, int) and math.isfinite(x) and 0 <= x < 10


def assess_first_guard_event(latch: dict, skew: dict) -> dict:
    if (not isinstance(latch, dict) or not isinstance(skew, dict)
            or latch.get("latched") is not True
            or latch.get("reason") != "UPSTREAM_STALE_AFTER_MOTION"):
        raise ValueError("D08_G07_FIRST_STALE_GUARD_TRANSITION_NOT_PROVEN")
    guard_age = latch.get("cm_age_sec")
    observer_age = skew.get("observer_cm_age_at_latch_sec")
    observed_guard = skew.get("guard_cm_age_at_latch_sec")
    if not all(_valid_age(x) for x in (guard_age, observer_age, observed_guard)):
        raise ValueError("D08_G07_FIRST_CM_RECEIPT_TIMES_MISSING")
    if abs(guard_age - observed_guard) > .015:
        raise ValueError("D08_G07_FIRST_CM_GUARD_AGE_WITNESS_DISAGREES")
    tick = latch.get("tick_monotonic")
    cm_rx = latch.get("cm_rx_monotonic")
    if not (_valid_age(tick - cm_rx) if type(tick) in (int,float) and
            type(cm_rx) in (int,float) else False):
        raise ValueError("D08_G07_FIRST_CM_INTERNAL_CLOCK_INVALID")
    if abs((tick - cm_rx) - guard_age) > .005:
        raise ValueError("D08_G07_FIRST_GUARD_MONOTONIC_AGE_INCONSISTENT")
    if guard_age <= TTL_SEC:
        raise ValueError("D08_G07_GUARD_150MS_VIOLATION_NOT_PROVEN")
    # Both independent read-only Observer and native Guard stalled within
    # near-identical timing: Guard-only scheduler lag is not supported.
    if observer_age > TTL_SEC and abs(guard_age - observer_age) <= .025:
        candidate = "COMMON_CM_SOURCE_OR_SHARED_DISPATCH_GAP_CANDIDATE"
    elif observer_age <= TTL_SEC:
        candidate = "GUARD_RMW_RECEIVE_OR_EXECUTOR_LAG_CANDIDATE"
    else:
        candidate = "MIXED_CM_GUARD_TIMING_CANDIDATE"
    return {
        "schema": "axia.d08.g07.first_guard_ttl150_readonly_triage_v1",
        "status": "FIRST_SAFETY_TRANSITION_PROVEN_MOVING_L2_HOLD",
        "reason": latch["reason"],
        "first_guard_tick_monotonic": round(tick, 9),
        "guard_cm_last_receive_monotonic": round(cm_rx, 9),
        "guard_cm_age_ms": round(guard_age * 1000, 3),
        "observer_cm_age_ms": round(observer_age * 1000, 3),
        "age_skew_ms": round((guard_age - observer_age) * 1000, 3),
        "ttl_limit_ms": 150.0,
        "ttl_excess_ms": round((guard_age - TTL_SEC) * 1000, 3),
        "candidate": candidate,
        "cause": "UNDETERMINED",
        "publisher_timestamp_or_lttng_proven": False,
        "cm_guard_150ms_safety_contract_pass": False,
        "moving_l2_accepted": False,
        "owner_wsl2_l3_accepted": False,
        "certified_estop": False,
    }


def first_pair_from_log(raw: str):
    if len(raw) > 12_000_000:
        raise ValueError("D08_G07_FIRST_LATCH_INPUT_OVERSIZED")
    first = {}
    for line in raw.splitlines():
        for key, tag in (("skew", TAG_SKEW), ("latch", TAG_LATCH)):
            if key in first:
                continue
            i = line.find(tag)
            if i < 0:
                continue
            try:
                event = json.loads(line[i+len(tag):])
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(event, dict):
                continue
            first[key] = event
        if len(first) == 2:
            return first["latch"], first["skew"]
    raise ValueError("D08_G07_FIRST_GUARD_LATCH_LOG_PAIR_INCOMPLETE")


def analyze_file(src: Path, out: Path) -> int:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() or out.is_symlink():
        raise ValueError("D08_G07_FIRST_LATCH_OUTPUT_EXISTS")
    result = {
        "schema":"axia.d08.g07.first_guard_ttl150_readonly_triage_v1",
        "status":"EVIDENCE_INCOMPLETE_MOVING_L2_HOLD",
        "cause":"UNDETERMINED",
        "moving_l2_accepted":False,
        "owner_wsl2_l3_accepted":False,
        "certified_estop":False,
    }
    try:
        if src.is_symlink() or not src.is_file() or src.stat().st_size > 12_000_000:
            raise ValueError("D08_G07_FIRST_LATCH_LOG_NOT_ADMISSIBLE")
        latch,skew = first_pair_from_log(src.read_text(errors="replace"))
        result = assess_first_guard_event(latch,skew)
    except (OSError, ValueError) as exc:
        result["first_boundary"] = str(exc)[:180]
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("D08_G07_FIRST_GUARD_CAUSAL_HOLD "+json.dumps({
        "status":result["status"],"candidate":result.get("candidate","UNKNOWN"),
        "cause":"UNDETERMINED",
        "cm_age_ms":result.get("guard_cm_age_ms")}),flush=True)
    return 0 if result["status"]=="FIRST_SAFETY_TRANSITION_PROVEN_MOVING_L2_HOLD" else 2


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--in-log",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    raise SystemExit(analyze_file(a.in_log,a.out))
