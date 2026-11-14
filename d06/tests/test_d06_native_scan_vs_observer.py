"""G07 real Owner/CI - independent Safety Supervisor scan TTL vs read-only Observer.
Sanitized field replay: third independent Gazebo cold-start #43596963732/attempt3.
"""
from d06.live.d06_native_scan_vs_observer import inspect_safety_scan

def state(t,count,maxgap,age,*,fsm="NORMAL",code=None):
    return {"kind":"supervisor","t":t,"data":{
        "state":fsm,
        "scan_fault_code":code,
        "health_diagnostics":{
            "scan_ok":code is None,
            "scan_callback_gaps_over_timeout":count,
            "scan_callback_max_gap_sec":maxgap,
            "scan_age_sec":age}}}

def test_observer_scan_30284ms_without_native_supervisor_breach_is_not_native_ttl_fail():
    events=[state(.9,0,.19,.04),
            {"kind":"owner_goal_published","t":1.0},
            {"kind":"scan","t":1.1},
            {"kind":"scan","t":1.402840},
            state(1.2,0,.199,.02),state(1.5,0,.2,.05)]
    x=inspect_safety_scan(events)
    assert x["observer_scan_first_gap_ms"]==302.84
    assert x["native_scan_callback_gaps_added_since_goal"]==0
    assert x["status"]=="OBSERVER_SCAN_GAP_NO_NATIVE_SCAN_TTL_BREACH_OBSERVED"
    assert x["native_scan_300ms_breach_proven"] is False
    assert x["safety_pass"] is False
    assert x["owner_l3_accepted"] is False

def test_native_supervisor_scan_gap_is_true_safety_breach_even_without_observer_lag():
    events=[state(.9,2,.28,.02),
            {"kind":"owner_goal_published","t":1.0},
            {"kind":"scan","t":1.1},{"kind":"scan","t":1.2},
            state(1.32,3,.364642,.31,code="SCAN_TIMEOUT")]
    out=inspect_safety_scan(events)
    assert out["status"]=="HOLD_NATIVE_SUPERVISOR_SCAN_TTL_BREACH"
    assert out["native_scan_300ms_breach_proven"] is True
    assert out["native_scan_callback_gaps_added_since_goal"]==1
    assert out["safety_pass"] is False

def test_no_pregoal_baseline_or_no_postgoal_state_remains_unverified():
    only=[{"kind":"owner_goal_published","t":1.0},state(1.1,0,.2,.02)]
    assert inspect_safety_scan(only)["status"]=="NATIVE_SUPERVISOR_SCAN_TIMING_UNVERIFIED"
    only=[state(.9,0,.1,.02),{"kind":"owner_goal_published","t":1.0}]
    assert inspect_safety_scan(only)["status"]=="NATIVE_SUPERVISOR_SCAN_TIMING_UNVERIFIED"

def test_bad_or_absent_scan_diagnostics_never_proves_safety():
    input=[state(.9,0,.1,.02),{"kind":"owner_goal_published","t":1.0},
           {"kind":"supervisor","t":1.2,"data":{"state":"NORMAL"}}]
    r=inspect_safety_scan(input)
    assert r["status"]=="NATIVE_SUPERVISOR_SCAN_TIMING_UNVERIFIED"
    assert r["safety_pass"] is False

def test_odom_observer_gap_does_not_certify_native_odom_receipt():
    events=[state(.9,0,.1,.02),
            {"kind":"owner_goal_published","t":1.0},
            {"kind":"odom","t":1.1},{"kind":"odom","t":1.409208203},
            state(1.2,0,.2,.02)]
    r=inspect_safety_scan(events)
    assert r["observer_odom_first_gap_ms"]==309.208
    assert r["native_odom_receipt_ttl_proven"] is False
    assert r["owner_l3_accepted"] is False
