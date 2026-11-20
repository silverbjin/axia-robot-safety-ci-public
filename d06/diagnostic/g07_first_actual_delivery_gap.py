#!/usr/bin/env python3
"""Bounded read-only first multi-channel ROS delivery gap around actual Goal.

Only compares host-monotonic callback timestamps collected in the SAME
Observer process. Multi-stream correlation does NOT prove publisher stall,
DDS loss, executor starvation, host CPU scheduling, or first Guard TTL cause.
Nothing here can grant Goal/Owner safety acceptance.
"""
import argparse
import json
import math
from pathlib import Path


LIMITS = {
    "pre_guard": .12, "supervised": .15, "guard": .15,
    "supervisor": .15, "scan": .30, "odom": .30, "clock": .30,
}


def _finite(x):
    return type(x) in (int, float) and math.isfinite(x)


def _hold(status, **fields):
    return dict(schema="axia.g07.first_actual_delivery_gap.v1", status=status,
                root_cause="UNDETERMINED", root_cause_proven=False,
                publisher_delay_proven=False,
                observer_scheduling_delay_proven=False,
                cm_guard_ttl_changed=False, certified_estop=False,
                release="HOLD", **fields)


def classify(events, *, start, end):
    if (not isinstance(events, list) or not 0 < len(events) <= 120000
            or not all(_finite(x) for x in (start, end)) or start >= end):
        return _hold("FIRST_DELIVERY_BOUNDARY_NOT_VERIFIED_HOLD")
    grouped = {name: [] for name in LIMITS}
    for event in events:
        if not isinstance(event, dict) or not _finite(event.get("t")):
            continue
        t, kind = event["t"], event.get("kind")
        if start <= t <= end and kind in grouped:
            grouped[kind].append(t)
    first = {}
    maxima = {}
    for channel, points in grouped.items():
        if len(points) < 2:
            continue
        points.sort()
        gaps = [(a, b) for a, b in zip(points, points[1:]) if b>a]
        if not gaps:
            continue
        maxima[channel] = round(max(b-a for a,b in gaps)*1000, 6)
        for a,b in gaps:
            if b-a > LIMITS[channel]+1e-9:
                first[channel] = {
                    "channel": channel, "previous_rx_monotonic": round(a,9),
                    "current_rx_monotonic": round(b,9),
                    "gap_ms":round((b-a)*1000,6),
                    "limit_ms":round(LIMITS[channel]*1000),
                }
                break
    if not maxima:
        return _hold("FIRST_DELIVERY_BOUNDARY_NOT_VERIFIED_HOLD")
    if not first:
        return _hold("NO_OBSERVED_GAP_CANDIDATE_ONLY",
                     observed_max_gap_ms=maxima, first_violation=None)
    primary = min(first.values(),key=lambda x:(x["current_rx_monotonic"],
                                             list(LIMITS).index(x["channel"])))
    first_at=primary["current_rx_monotonic"]
    correlated=[
        x for x in first.values()
        if abs(x["current_rx_monotonic"]-first_at) <= .05
        and x["previous_rx_monotonic"] < first_at
    ]
    status=("CROSS_STREAM_GAP_CANDIDATE_HOLD" if len(correlated)>=3
            else "SINGLE_STREAM_GAP_HOLD")
    return _hold(status, first_violation=primary,
                 first_pairs=first, observed_max_gap_ms=maxima,
                 cross_stream_breaches=[x["channel"] for x in correlated],
                 source_observer_timing_proven=False,
                 guard_internal_first_latch_cause_proven=False)


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--events",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args(argv)
    try:
        report=json.loads(args.report.read_text())
        events=[json.loads(x) for x in args.events.read_text().splitlines()]
        goals=[x["t"] for x in events if x.get("kind")=="owner_goal_published"
               and _finite(x.get("t"))]
        if len(goals)!=1:
            v=_hold("FIRST_DELIVERY_BOUNDARY_NOT_VERIFIED_HOLD")
        else:
            ends=[x["t"] for x in events if x.get("kind")=="task03_motion_window_end"
                  and _finite(x.get("t")) and x["t"]>goals[0]]
            first=report.get("first_guard_latch")
            latch_t=first.get("tick_monotonic") if isinstance(first,dict) else None
            end=(latch_t if _finite(latch_t) and latch_t>goals[0]
                 else ends[0] if len(ends)==1
                 else max((x.get("t") for x in events
                           if _finite(x.get("t")) and x["t"]>goals[0]),
                          default=None))
            v=classify(events,start=goals[0],end=end)
        v["actual_same_session_event_pairs_read"]=True
    except (OSError,ValueError,TypeError,KeyError):
        v=_hold("FIRST_DELIVERY_BOUNDARY_NOT_VERIFIED_HOLD",
                actual_same_session_event_pairs_read=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
    print("AXIA_G07_FIRST_DELIVERY_ACTUAL_PAIRS "+json.dumps(v,sort_keys=True),flush=True)
    return 0   # Never accept or release a robot by a diagnostic-only command.


if __name__=="__main__":
    raise SystemExit(main())
