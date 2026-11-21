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



def classify_rmw_first_pair(events, first_pair):
    """Join first *exact* CM Observer callback pair to same-session RMW info.

    Publication/received nanoseconds come from the Jazzy rclpy MessageInfo
    system-clock domain; callback times use Linux host monotonic. Only compare
    intervals *within* one domain. Missing/dropped publication sequences or
    unmatched callback rows cannot prove the first origin.
    """
    out=_hold("RMW_FIRST_PAIR_UNVERIFIED",
              callback_gap_ms=None,
              rmw_source_gap_ms=None, rmw_received_gap_ms=None,
              rmw_publication_seq_gap=None, publisher_stall_proven=False,
              rmw_transport_root_proven=False,
              first_guard_latch_cause_proven=False)
    if (not isinstance(events,list) or not isinstance(first_pair,dict)
            or first_pair.get("channel")!="pre_guard"):
        return out
    start,end=(first_pair.get("previous_rx_monotonic"),
               first_pair.get("current_rx_monotonic"))
    if (not _finite(start) or not _finite(end) or start<0 or end<=start):
        return out
    found=[]
    for t in (start,end):
        matches=[x for x in events if isinstance(x,dict)
                 and x.get("kind")=="pre_guard"
                 and _finite(x.get("t"))
                 and abs(x["t"]-t)<0.0000005]
        if len(matches)!=1:
            return out
        found.append(matches[0])
    a,b=found
    def value(row,name):
        v=row.get(name)
        return v if type(v) is int and v>=0 else None
    src=[value(x,"rmw_source_ns") for x in found]
    rx=[value(x,"rmw_received_ns") for x in found]
    seq=[value(x,"rmw_publication_seq") for x in found]
    if (any(x is None for x in src+rx+seq)
            or min(src)<=0 or any(t<source for t,source in zip(rx,src))):
        return out
    sg=seq[1]-seq[0]
    source_ns=src[1]-src[0]
    received_ns=rx[1]-rx[0]
    if source_ns<=0 or received_ns<=0 or sg<=0:
        return {**out,"status":"RMW_TIMEBASE_REGRESSION_HOLD"}
    if sg!=1:
        return {**out,"status":"RMW_SEQUENCE_DISCONTINUITY_HOLD",
                "rmw_publication_seq_gap":sg}
    cb_gap_ms=round((end-start)*1000,6)
    source_ms=round(source_ns/1e6,6)
    receive_ms=round(received_ns/1e6,6)
    out.update(callback_gap_ms=cb_gap_ms,
               rmw_source_gap_ms=source_ms,
               rmw_received_gap_ms=receive_ms,
               rmw_publication_seq_gap=sg,
               same_publisher_consecutive_seq=True)
    limit_ms=120.
    if source_ms>=limit_ms:
        out["status"]="RMW_SOURCE_PERIOD_GAP_CANDIDATE"
    elif receive_ms>=limit_ms:
        out["status"]="RMW_RECEIPT_GAP_CANDIDATE"
    elif cb_gap_ms>=limit_ms:
        out["status"]="OBSERVER_CALLBACK_GAP_CANDIDATE"
    else:
        out["status"]="RMW_OBSERVED_PAIR_WITHIN_BOUND_UNPROVEN"
    return out



def summarize_rmw_readiness(events):
    """Is Jazzy MessageInfo *present* on both existing Observer subscriptions?

    Counts only, never copies message content or crosses clock domains.
    Consecutive sequence numbers are needed before a first RMW gap can be
    interpreted. A missing sequence is not a healthy transport measurement.
    """
    stats={channel:{"received":0,"valid_metadata":0,"valid_pairs":0}
           for channel in ("pre_guard","supervised")}
    result={"schema":"axia.g07.rmw_readiness.v1",
            "status":"RMW_METADATA_INSUFFICIENT_HOLD",
            "pre_guard_valid_consecutive_pairs":0,
            "supervised_valid_consecutive_pairs":0,
            "missing_or_unusable_samples":0,
            "sequence_discontinuities":0,
            "first_boundary_proven":False,
            "root_cause_proven":False,
            "release":"HOLD"}
    if not isinstance(events,list) or len(events)>120000:
        return result
    previous={"pre_guard":None,"supervised":None}
    for row in events:
        if not isinstance(row,dict) or row.get("kind") not in stats:
            continue
        channel=row["kind"]
        info=stats[channel]
        info["received"]+=1
        t=row.get("t")
        src,rx,seq=(row.get("rmw_source_ns"),
                    row.get("rmw_received_ns"),
                    row.get("rmw_publication_seq"))
        if (not _finite(t) or type(src) is not int or type(rx) is not int
                or type(seq) is not int or src<=0 or rx<src or seq<0):
            result["missing_or_unusable_samples"]+=1
            previous[channel]=None
            continue
        info["valid_metadata"]+=1
        old=previous[channel]
        if old:
            if (seq-old[2]!=1 or src<=old[0] or rx<=old[1]
                    or t<=old[3]):
                result["sequence_discontinuities"]+=1
            else:
                info["valid_pairs"]+=1
        previous[channel]=(src,rx,seq,t)
    for channel in stats:
        result[channel+"_valid_consecutive_pairs"]=stats[channel]["valid_pairs"]
        result[channel+"_messageinfo_count"]=stats[channel]["valid_metadata"]
        result[channel+"_callback_count"]=stats[channel]["received"]
    if all(stats[k]["valid_pairs"]>0 for k in stats):
        result["status"]="RMW_TWO_TOPICS_METADATA_READY"
    return result



def first_observed_safety_transition(events, first_gap):
    """First *observed* Supervisor FSM change and Guard latch, not true root.

    Only same-process host-monotonic intervals are compared. Earlier
    undelivered FSM messages cannot be invented. Never grants safety PASS.
    """
    import re
    out={"schema":"axia.g07.first_observed_safety_transition.v1",
         "status":"FIRST_SAFETY_TRANSITION_NOT_OBSERVED_HOLD",
         "release":"HOLD","root_cause_proven":False,
         "certified_estop":False,"first_observed_state":None,
         "first_observed_transition":None,
         "first_observed_guard_latch_at":None,
         "relative_to_first_gap":"GAP_NOT_VERIFIED"}
    if not isinstance(events,list) or len(events)>120000:
        return out
    observations=[]
    latches=[]
    for row in events:
        if not isinstance(row,dict) or not _finite(row.get("t")):
            continue
        data=row.get("data")
        if not isinstance(data,dict):
            continue
        if row.get("kind")=="supervisor":
            state=data.get("state")
            if (isinstance(state,str)
                and re.fullmatch(r"[A-Z][A-Z0-9_]{0,39}",state)):
                observations.append((row["t"],state))
        elif row.get("kind")=="guard" and data.get("latched") is True:
            latches.append(row["t"])
    if latches:
        out["first_observed_guard_latch_at"]=round(min(latches),9)
    if not observations:
        return out
    observations.sort()
    out["first_observed_state"]=observations[0][1]
    for previous,current in zip(observations,observations[1:]):
        if previous[1]==current[1]:
            continue
        t=current[0]
        out["first_observed_transition"]={
            "at_host_monotonic":round(t,9),
            "from_state":previous[1],"to_state":current[1]}
        out["status"]="FIRST_SUPERVISOR_OBSERVED_TRANSITION_CAPTURED_HOLD"
        if isinstance(first_gap,dict) and _finite(
                first_gap.get("current_rx_monotonic")):
            boundary=first_gap["current_rx_monotonic"]
            out["relative_to_first_gap"]=(
                "BEFORE_OR_AT_FIRST_CALLBACK_BREACH" if t<=boundary
                else "AFTER_FIRST_CALLBACK_BREACH")
        break
    return out


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
            cm_pair=v.get("first_pairs",{}).get("pre_guard")
            v["cm_rmw_first_pair"]=classify_rmw_first_pair(events,cm_pair)

        v["rmw_readiness"]=summarize_rmw_readiness(events)
        v["first_safety_observation"]=first_observed_safety_transition(
            events,v.get("first_violation"))
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
