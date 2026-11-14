"""CM real-RMW 170.929ms gap scheduler attribution, sanitized public CI RED.
No ROS, Goal, private bag or official Nav2 modifications.
"""
import json
from pathlib import Path
from d06.live.d06_cm_proc_sched_probe import analyze_gap, read_schedstat

def ev(kind,t,src,seq):
    return {"kind":kind,"t":t,"rmw_source_ns":round(src*1e9),
            "rmw_publication_seq":seq}

def test_actual_cm_source_gap_170929ms_vs_sched_runqueue_wait_is_not_pass():
    events=[{"kind":"owner_goal_published","t":100.0},
            ev("pre_guard",101.0,1_700_000_000.0,91),
            ev("supervised",101.02,1_700_000_000.02,11),
            ev("supervised",101.07,1_700_000_000.07,12),
            ev("supervised",101.12,1_700_000_000.12,13),
            ev("pre_guard",101.171,1_700_000_000.170929231,92)]
    sample=[
        {"t":100.99,"runtime_ns":100_000_000,"wait_ns":30_000_000,"timeslices":15},
        {"t":101.185,"runtime_ns":120_000_000,"wait_ns":160_000_000,"timeslices":19},
    ]
    r=analyze_gap(events,sample,schedstat_enabled=True)
    assert r["status"]=="HOLD_CM_RMW_PUBLISH_GAP_OVER_150MS"
    assert abs(r["first_cm_source_gap_ms"]-170.929231)<.005
    assert r["upstream_publications_inside_gap"]==3
    assert r["scheduler_wait_growth_ms"]==130.0
    assert r["scheduler_wait_overlaps_gap_candidate"] is True
    assert r["cm_callback_processing_delay_proven"] is False
    assert r["owner_l3_accepted"] is False
    assert r["safety_pass"] is False

def test_schedstat_unavailable_cannot_explain_or_accept_cm_gap():
    events=[{"kind":"owner_goal_published","t":100.0},
            ev("pre_guard",101.0,1000.0,1),
            ev("pre_guard",101.171,1000.170929,2)]
    r=analyze_gap(events,[],schedstat_enabled=False)
    assert r["status"]=="HOLD_CM_RMW_PUBLISH_GAP_OVER_150MS"
    assert r["scheduler_status"]=="SCHEDSTAT_UNAVAILABLE"
    assert r["scheduler_wait_overlaps_gap_candidate"] is False
    assert r["safety_pass"] is False

def test_schedstat_validated_only_for_three_nonnegative_integer_counters(tmp_path):
    f=tmp_path/"schedstat"
    f.write_text("10000000 25000000 99\n")
    assert read_schedstat(f)==(10000000,25000000,99)
    f.write_text("0 0 -1\n")
    assert read_schedstat(f) is None
    f.write_text("private secret or broken\n")
    assert read_schedstat(f) is None

def test_no_actual_goal_or_no_gap_never_promotes_safety():
    events=[ev("pre_guard",1.0,1000.0,1),ev("pre_guard",1.08,1000.08,2)]
    r=analyze_gap(events,[],schedstat_enabled=True)
    assert r["status"]=="NO_ACTUAL_GOAL_OR_CM_RMW_PROOF"
    assert r["safety_pass"] is False
