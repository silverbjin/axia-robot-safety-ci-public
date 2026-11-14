"""Fail-first: never equate separate Observer /safety/scan timing with Supervisor receipt.

Third actual cold-start #43596963732 attempt 3: /odom Observer callback 309.208ms,
RMW receive gap 307.696ms, RMW source 140.388ms, missing intermediate samples;
scan observer max 302.840ms. Native Supervisor publishes its *own*
scan_callback_gaps_over_timeout in /axia/safety/state, read in same session.
Fixtures sanitized; this file does not create a ROS publisher or Goal.
"""
from d06.live.d06_supervisor_scan_vs_observer_first_gap import correlate

def row(kind, t, data=None):
    r={"kind":kind,"t":t}
    if data is not None:r["data"]=data
    return r

def state(gaps, max_gap=0.0, *, latched=False):
    return {"health_diagnostics":{
        "scan_callback_gaps_over_timeout":gaps,
        "scan_callback_max_gap_sec":max_gap,
        "scan_ok":not latched},
        "state":"SW_STOP_LATCHED" if latched else "NORMAL"}

def basic():
    return [row("owner_goal_published",10.0),
            row("scan",10.50), row("scan",10.803),
            row("odom",10.50), row("odom",10.809208)]

def test_actual_supervisor_scan_counter_growth_corroborates_native_breach():
    events=basic()+[
        row("supervisor",10.47,state(0,0.115)),
        row("supervisor",10.835,state(1,0.335))]
    result=correlate(events)
    assert result["observer_scan_first_gap_ms"]==303.0
    assert result["supervisor_scan_status"]=="NATIVE_SUPERVISOR_SCAN_GAP_CORROBORATED"
    assert result["native_gap_counter_delta"]==1
    assert result["native_max_scan_gap_ms"]==335.0
    assert result["safety_pass"] is False
    assert result["owner_l3_accepted"] is False

def test_supervisor_fresh_with_stable_counter_does_not_prove_safety_stop():
    events=basic()+[
        row("supervisor",10.47,state(0,0.108)),
        row("supervisor",10.835,state(0,0.118)),
        row("guard",10.82,{"latched":False,"reason":"FORWARDING_MONITORED_CM"})]
    result=correlate(events)
    assert result["supervisor_scan_status"]=="OBSERVER_SCAN_GAP_NOT_REPRODUCED_IN_SUPERVISOR"
    assert result["native_gap_counter_delta"]==0
    assert result["guard_latch_observed"] is False
    assert result["observer_odom_first_gap_ms"]==309.208
    assert result["actual_guard_receive_delay_proven"] is False
    # Even an observer-only candidate must NOT pass the strict CI 300ms oracle.
    assert result["safety_pass"] is False

def test_missing_native_snapshot_in_window_is_unknown_not_pass():
    events=basic()+[row("supervisor",9.0,state(0,0.12))]
    result=correlate(events)
    assert result["supervisor_scan_status"]=="NO_MATCHING_NATIVE_SUPERVISOR_WINDOW"
    assert result["native_gap_counter_delta"] is None
    assert result["actual_guard_receive_delay_proven"] is False

def test_native_guard_latch_takes_priority_over_observer_only_candidate():
    events=basic()+[
        row("supervisor",10.47,state(0,0.1)),
        row("supervisor",10.835,state(0,0.11)),
        row("guard",10.79,{"latched":True,"reason":"UPSTREAM_STALE_AFTER_MOTION"})]
    result=correlate(events)
    assert result["status"]=="HOLD_NATIVE_GUARD_LATCH_OBSERVED"
    assert result["guard_latch_observed"] is True
    assert result["supervisor_scan_status"]=="OBSERVER_SCAN_GAP_NOT_REPRODUCED_IN_SUPERVISOR"
    assert result["safety_pass"] is False

def test_native_counter_cannot_be_matched_to_other_goal_or_old_sample():
    events=basic()+[
        row("supervisor",9.99,state(9,.9)),
        row("supervisor",12.0,state(10,1.0))]
    result=correlate(events)
    assert result["supervisor_scan_status"]=="NO_MATCHING_NATIVE_SUPERVISOR_WINDOW"
    assert result["native_gap_counter_delta"] is None

def test_missing_or_reordered_goal_never_claims_correlated_safety_evidence():
    events=basic()[1:]+[row("supervisor",10.5,state(5,.4))]
    result=correlate(events)
    assert result["status"]=="NO_EXACTLY_ONE_ACTUAL_GOAL"
    assert result["supervisor_scan_status"]=="NOT_EVALUATED"
    assert result["safety_pass"] is False
