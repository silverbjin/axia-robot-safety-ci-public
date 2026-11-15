#!/usr/bin/env python3
"""Read-only join of first native Guard CM TTL latch with later RMW CM pair.

The second CM packet can arrive AFTER the first Guard latch. A verifier that
stops collecting at the latch incorrectly calls the first source gap None.
These post-run diagnostics NEVER reverse a safety latch or accept an Owner.
Use native Guard age for TTL truth; RMW publish metadata for CM source gap.
ROS RMW wall-clock source and monotonic Guard tick are NOT subtracted directly.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

def _valid(x):
    return type(x) in (int,float) and math.isfinite(x) and x>=0

def _r(x):
    return round(x,6)

def analyze_first_latch(evidence):
    base={
        "schema":"axia.d06.native_guard_cm_right_censored_postrun_v1",
        "status":"UNVERIFIED_NO_ACCEPTANCE",
        "first_safety_transition":None, "first_boundary":None,
        "cm_age_at_latch_ms":None,
        "earliest_native_threshold_crossing_ms_before_latch":None,
        "cm_source_gap_ms":None, "cm_receive_gap_ms":None,
        "observer_gap_ms":None, "sequence_increment":None,
        "supervisor_publications_inside_cm_gap":None,
        "upstream_max_gap_ms":None,
        "cm_publisher_interval_gap_confirmed_post_latch":False,
        "pre_latch_cm_observer_evidence_right_censored":False,
        "guard_latch_caused_by_missing_cm_input":False,
        "cm_callback_processing_delay_proven":False,
        "actual_root_cause_sched_or_cm_execution_proven":False,
        "safety_pass":False, "owner_l3_accepted":False,
        "certified_estop":False,
    }
    if not isinstance(evidence,dict):
        return base
    first=evidence.get("first_guard_latch")
    pair=evidence.get("post_latch_joined_pair")
    window=evidence.get("observation_window") or {}
    if not isinstance(pair,dict):
        return {**base,"status":"HOLD_MISSING_POST_LATCH_CM_PAIR_UNVERIFIED"}
    keys=("rmw_source_gap_ms","rmw_received_gap_ms","observer_callback_gap_ms")
    if any(not _valid(pair.get(k)) for k in keys):
        return {**base,"status":"HOLD_CM_RMW_METADATA_UNVERIFIED"}
    source=pair["rmw_source_gap_ms"]
    receive=pair["rmw_received_gap_ms"]
    callback=pair["observer_callback_gap_ms"]
    seq=pair.get("publication_sequence_gap")
    valid_seq=type(seq) is int and seq==1
    result={**base,"cm_source_gap_ms":_r(source),
            "cm_receive_gap_ms":_r(receive),
            "observer_gap_ms":_r(callback),
            "sequence_increment":seq,
            "pre_latch_cm_observer_evidence_right_censored":(
                window.get("pre_latch_rmw_pair_complete") is False),
            "supervisor_publications_inside_cm_gap":pair.get(
                "upstream_supervisor_publications_during_window"),
            "upstream_max_gap_ms":pair.get(
                "upstream_supervisor_max_coverage_gap_ms"),
    }
    if first is None:
        if valid_seq and source<=150 and receive>150:
            return {**result,"status":"HOLD_CM_RMW_RECEIVE_GAP_NATIVE_GUARD_UNVERIFIED"}
        return {**result,"status":"NO_GUARD_LATCH_NATIVE_NOT_ACCEPTED"}
    if not isinstance(first,dict):
        return {**result,"status":"HOLD_NATIVE_GUARD_LATCH_MALFORMED"}
    age=first.get("measured_age_ms")
    limit=first.get("limit_ms")
    reason=first.get("reason")
    if not (_valid(age) and _valid(limit) and limit>0):
        return {**result,"status":"HOLD_NATIVE_GUARD_TTL_UNVERIFIED"}
    result.update(
        first_safety_transition=reason, first_boundary="guard_internal_cm",
        cm_age_at_latch_ms=_r(age), limit_ms=_r(limit),
        earliest_native_threshold_crossing_ms_before_latch=_r(max(0,age-limit)),
        guard_latch_caused_by_missing_cm_input=(
            reason=="UPSTREAM_STALE_AFTER_MOTION" and age>limit))
    if age<=limit:
        return {**result,"status":"HOLD_GUARD_LATCH_REASON_NOT_EXPLAINED_BY_CM_TTL"}
    result["cm_publisher_interval_gap_confirmed_post_latch"]=(
        valid_seq and source>limit and
        window.get("joined_second_cm_packet_observed_only_after_guard_latch") is True)
    if result["cm_publisher_interval_gap_confirmed_post_latch"]:
        return {**result,"status":"HOLD_CM_SOURCE_GAP_WITH_FIRST_GUARD_LATCH"}
    if valid_seq and receive>limit and source<=limit:
        return {**result,"status":"HOLD_GUARD_CM_TTL_WITH_RMW_RECEIVE_DELAY_CANDIDATE"}
    return {**result,"status":"HOLD_GUARD_CM_TTL_SOURCE_PROVENANCE_UNVERIFIED"}

def from_original_events(rows, verdict):
    """Construct privacy-safe interval evidence from a private local ledger.

    Never copies data arrays, Goal UUIDs, raw messages, or device addresses.
    The CM pair is joined across native Guard latch in the OBSERVER clock.
    Native Guard clock and RMW source clock are never compared absolutely.
    """
    if not isinstance(verdict,dict) or not isinstance(rows,list):
        return {}
    g=verdict.get("first_guard_latch")
    first=None
    tick=g.get("tick_monotonic") if isinstance(g,dict) else None
    if isinstance(g,dict):
        first={"reason":g.get("reason"),
               "measured_age_ms":_r(1000*g["cm_age_sec"])
                   if _valid(g.get("cm_age_sec")) else None,
               "limit_ms":150,
               "supervisor_fsm":g.get("supervisor_fsm")}
    cm=sorted((e for e in rows if isinstance(e,dict)
               and e.get("kind")=="pre_guard" and _valid(e.get("t"))
               and all(type(e.get(k)) is int for k in
                       ("rmw_source_ns","rmw_received_ns","rmw_publication_seq"))),
              key=lambda x:x["t"])
    if _valid(tick):
        before=[e for e in cm if e["t"]<=tick]
        after=[e for e in cm if e["t"]>tick]
        pair=(before[-1],after[0]) if before and after else None
    else:
        pair=(cm[0],cm[1]) if len(cm)>=2 else None
    if pair is None:
        return {"first_guard_latch":first,"post_latch_joined_pair":None,
                "observation_window":{"pre_latch_rmw_pair_complete":False}}
    a,b=pair
    sup=[e for e in rows if isinstance(e,dict)
         and e.get("kind")=="supervised" and _valid(e.get("t"))
         and a["t"]<e["t"]<b["t"]
         and type(e.get("rmw_source_ns")) is int]
    sup.sort(key=lambda e:e["t"])
    gaps=[(y["rmw_source_ns"]-x["rmw_source_ns"])/1e6
          for x,y in zip(sup,sup[1:])]
    return {
        "first_guard_latch":first,
        "post_latch_joined_pair":{
            "rmw_source_gap_ms":_r((b["rmw_source_ns"]-a["rmw_source_ns"])/1e6),
            "rmw_received_gap_ms":_r((b["rmw_received_ns"]-a["rmw_received_ns"])/1e6),
            "observer_callback_gap_ms":_r((b["t"]-a["t"])*1000),
            "publication_sequence_gap":b["rmw_publication_seq"]-a["rmw_publication_seq"],
            "upstream_supervisor_publications_during_window":len(sup),
            "upstream_supervisor_max_coverage_gap_ms":_r(max(gaps)) if gaps else None},
        "observation_window":{
            "first_pre_latch_observer_violation":None,
            "pre_latch_rmw_pair_complete":False,
            "joined_second_cm_packet_observed_only_after_guard_latch":_valid(tick) and a["t"]<tick<b["t"]}
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixture",type=Path)
    ap.add_argument("--events",type=Path)
    ap.add_argument("--live-result",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    try:
        if args.fixture is not None:
            if args.fixture.is_symlink():raise ValueError("SYMLINK")
            e=json.loads(args.fixture.read_text())
        else:
            if args.events is None or args.live_result is None:raise ValueError("MISSING")
            if args.events.is_symlink() or args.live_result.is_symlink():raise ValueError("SYMLINK")
            rows=[json.loads(z) for z in args.events.read_text().splitlines() if z.strip()]
            verdict=json.loads(args.live_result.read_text())
            e=from_original_events(rows,verdict)
        out=analyze_first_latch(e)
    except (OSError,ValueError,KeyError,TypeError,UnicodeError):
        out=analyze_first_latch({})
    result=json.dumps(out,sort_keys=True)
    if args.output is not None:
        if args.output.is_symlink():return 3
        args.output.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("D06_G07_POSTRUN_JOINED_FIRST_CM_GUARD "+result)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
