"""D06 G07 direct Guard subscriber 150ms timing vs read-only Observer.

Guard-only telemetry is emitted on existing /axia/p2/base_guard, not new topic.
Sanitized miniature fixture from #43601466787 Observer 368ms CM callback but
RMW receive 30ms, and separate CM source 171ms. No native Guard attribution
without this independent original status evidence. No ROS, Goal or raw upload.
"""
from d06.live.d06_native_guard_vs_observer import inspect_native_guard

def guard(t, cm_count, sup_count, *, cm_max=0.08, sup_max=0.05, latched=False, cm_age=None):
    return {
        "kind":"guard","t":t,
        "data":{"latched":latched,
                "reason":"UPSTREAM_STALE_AFTER_MOTION" if latched else "FORWARDING_MONITORED_CM",
                "native_input_timing":{
                   "schema":"axia.g07.guard_native_callback_intervals_v1",
                   "cm_callback_count":100,
                   "cm_callback_gaps_over_150ms":cm_count,
                   "cm_callback_max_gap_sec":cm_max,
                   "cm_last_receive_age_sec":cm_age,
                   "supervisor_callback_count":100,
                   "supervisor_callback_gaps_over_150ms":sup_count,
                   "supervisor_callback_max_gap_sec":sup_max,
                }}
    }

def test_original_observer_cm_gap_368ms_without_native_guard_breach_cannot_claim_guard_failure():
    events=[guard(9.9,2,1),
            {"kind":"owner_goal_published","t":10.0},
            {"kind":"pre_guard","t":10.05},
            {"kind":"pre_guard","t":10.418869},
            guard(10.45,2,1)]
    r=inspect_native_guard(events)
    assert r["status"]=="NATIVE_GUARD_INPUT_GAPS_NOT_OBSERVED"
    assert r["native_cm_gap_count_added_since_goal"]==0
    assert r["native_supervisor_gap_count_added_since_goal"]==0
    assert r["observer_cm_gap_proves_guard_delay"] is False
    assert r["safety_pass"] is False

def test_native_cm_subscriber_actual_150ms_breach_distinct_from_observer():
    events=[guard(9.9,0,0),{"kind":"owner_goal_published","t":10.0},
            guard(10.45,1,0,cm_max=.171215)]
    r=inspect_native_guard(events)
    assert r["status"]=="HOLD_NATIVE_GUARD_CM_INPUT_GAP_150MS"
    assert r["native_cm_gap_count_added_since_goal"]==1
    assert r["native_cm_callback_max_gap_ms"]==171.215
    assert r["safety_pass"] is False

def test_supervisor_receipt_breach_reports_independently():
    events=[guard(9.9,0,1),{"kind":"owner_goal_published","t":10.0},
            guard(10.45,0,2,sup_max=.180)]
    r=inspect_native_guard(events)
    assert r["status"]=="HOLD_NATIVE_GUARD_SUPERVISOR_INPUT_GAP_150MS"
    assert r["native_supervisor_gap_count_added_since_goal"]==1

def test_native_guard_latch_wins_over_any_healthy_counter():
    events=[guard(9.9,2,0),{"kind":"owner_goal_published","t":10.0},
            guard(10.45,2,0,latched=True)]
    r=inspect_native_guard(events)
    assert r["status"]=="HOLD_NATIVE_GUARD_FIRST_LATCH"
    assert r["native_guard_latch_observed"] is True
    assert r["owner_l3_accepted"] is False
    assert r["native_cm_gap_count_added_since_goal"]==0

def test_no_pre_goal_baseline_or_missing_schema_remains_unverified():
    events=[{"kind":"owner_goal_published","t":10.0},guard(10.3,0,0)]
    assert inspect_native_guard(events)["status"]=="NATIVE_GUARD_RECEIPT_UNVERIFIED"
    events=[guard(9.9,0,0),{"kind":"owner_goal_published","t":10.0},
            {"kind":"guard","t":10.3,"data":{"latched":False}}]
    r=inspect_native_guard(events)
    assert r["status"]=="NATIVE_GUARD_RECEIPT_UNVERIFIED"

def test_counter_regression_cannot_falsely_pass():
    events=[guard(9.9,2,0),{"kind":"owner_goal_published","t":10.0},
            guard(10.3,1,0)]
    r=inspect_native_guard(events)
    assert r["status"]=="NATIVE_GUARD_RECEIPT_UNVERIFIED"
    assert r["native_cm_gap_count_added_since_goal"] is None


def test_first_guard_latch_preserves_native_cm_age_and_callback_counter():
    # Real public Gazebo L2 #43603054244: Guard first CM age=179.652ms,
    # actual CM RMW source gap NOT observed; cause still unverified.
    events=[guard(9.9,0,0,cm_age=.025),
            {"kind":"owner_goal_published","t":10.0},
            guard(10.49,0,0,cm_age=.179652,latched=True)]
    result=inspect_native_guard(events)
    assert result["status"]=="HOLD_NATIVE_GUARD_FIRST_LATCH"
    assert result["native_cm_gap_count_added_since_goal"]==0
    assert result["native_cm_last_receive_age_ms_at_latch"]==179.652
    assert result["observer_cm_gap_proves_guard_delay"] is False
    assert result["safety_pass"] is False


def test_long_cm_gap_after_goal_stop_does_not_poison_active_motion_ttl():
    # Real #43603675174 carried a 22.609s lifetime CM maximum. A cumulative
    # increment after the active Goal's true t1 is NOT evidence of a moving
    # safety violation. The post-Goal period belongs to lifecycle cleanup.
    events=[guard(9.9,0,0),
            {"kind":"owner_goal_published","t":10.0},
            guard(10.2,0,0,cm_max=.08),
            guard(10.35,0,0,cm_max=.09),
            guard(32.96,1,0,cm_max=22.609220)]
    r=inspect_native_guard(events,active_end=10.4)
    assert r["status"]=="NATIVE_GUARD_INPUT_GAPS_NOT_OBSERVED"
    assert r["native_cm_gap_count_added_since_goal"]==0
    assert r["active_goal_window_end_mono"]==10.4
    assert r["native_cm_callback_max_gap_ms"] is None
    assert r["safety_pass"] is False

def test_true_cm_gap_inside_active_goal_still_blocks():
    events=[guard(9.9,0,0),
            {"kind":"owner_goal_published","t":10.0},
            guard(10.2,1,0,cm_max=.171215),
            guard(32.9,2,0,cm_max=22.609220)]
    r=inspect_native_guard(events,active_end=10.4)
    assert r["status"]=="HOLD_NATIVE_GUARD_CM_INPUT_GAP_150MS"
    assert r["native_cm_gap_count_added_since_goal"]==1

def test_invalid_active_end_is_unknown_not_pass():
    events=[guard(9.9,0,0),{"kind":"owner_goal_published","t":10.0},
            guard(10.2,0,0)]
    r=inspect_native_guard(events,active_end=9.0)
    assert r["status"]=="NATIVE_GUARD_RECEIPT_UNVERIFIED"
    assert r["safety_pass"] is False
