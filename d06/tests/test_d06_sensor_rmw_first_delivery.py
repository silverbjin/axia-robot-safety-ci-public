"""Real Jazzy G07 Scan/Odom/Supervisor/CM publish vs receive timing.

Synthetic records, no private raw or Goal; classify but never promote PASS.
"""
from d06.live.d06_sensor_rmw_first_delivery import analyze_delivery

def sample(kind, callback_t, source_s, received_s, seq):
    return {"kind":kind,"t":callback_t,
            "rmw_source_ns":round(source_s*1e9),
            "rmw_received_ns":round(received_s*1e9),
            "rmw_publication_seq":seq}

def test_scan_420ms_observer_gap_can_be_rmw_receive_not_sensor_source():
    records=[{"kind":"owner_goal_published","t":1.0},
        sample("scan",2.0,100.0,100.001,11),
        sample("scan",2.420564,100.1,100.420,12)]
    r=analyze_delivery(records)
    assert r["first_boundary"]["channel"]=="scan"
    assert r["first_boundary"]["classification"]=="RMW_RECEIVE_GAP"
    assert abs(r["first_boundary"]["callback_gap_ms"]-420.564)<.001
    assert abs(r["first_boundary"]["source_gap_ms"]-100.0)<.001
    assert r["guard_received_same_delay_proven"] is False
    assert r["safety_pass"] is False

def test_cm_170929ms_publisher_gap_separate_from_callback_gap():
    records=[{"kind":"owner_goal_published","t":1.0},
        sample("pre_guard",2.0,1000.0,1000.001,101),
        sample("pre_guard",2.168229,1000.170929231,1000.171052,102)]
    r=analyze_delivery(records)
    assert r["first_boundary"]["channel"]=="pre_guard"
    assert r["first_boundary"]["classification"]=="PUBLISH_SOURCE_GAP"
    assert r["first_boundary"]["source_gap_ms"]>170.9
    assert r["safety_pass"] is False

def test_intermediate_unseen_seq_never_called_callback_processing_delay():
    records=[{"kind":"owner_goal_published","t":1.0},
        sample("supervised",2.0,200.0,200.001,1),
        sample("supervised",2.371,200.15,200.36,4)]
    r=analyze_delivery(records)
    assert r["first_boundary"]["classification"]=="INTERMEDIATE_PUBLICATIONS_UNOBSERVED"
    assert r["sensor_source_stalled_proven"] is False
    assert r["safety_pass"] is False

def test_missing_scan_odom_metadata_fails_closed_without_making_pass():
    records=[{"kind":"owner_goal_published","t":1.0},
             {"kind":"scan","t":2.0},
             {"kind":"scan","t":2.42}]
    r=analyze_delivery(records)
    assert r["first_boundary"]["classification"]=="RMW_METADATA_UNVERIFIED"
    assert r["safety_pass"] is False
    assert r["owner_l3_accepted"] is False

def test_no_goal_never_classifies_timing_as_real_simulation():
    r=analyze_delivery([sample("scan",2.0,100.0,100.001,1)])
    assert r["status"]=="NO_ACTUAL_GOAL"
    assert r["first_boundary"] is None
    assert r["safety_pass"] is False
