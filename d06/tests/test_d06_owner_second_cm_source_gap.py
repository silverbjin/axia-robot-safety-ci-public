"""New real WSL2 G07 first safety boundary: native Guard latch + CM source gap.
Sanitized reproduction only; no original topic samples/UUID/private paths.
The last CM message was observed before the latch, the next after it.
Do not call that uncompleted pre-latch gap a healthy 150ms interval.
"""
import json
from pathlib import Path
from d06.live.d06_guard_cm_first_latch_join import analyze_first_latch
ROOT=Path(__file__).resolve().parents[2]
DATA=json.loads((ROOT/"d06/tests/fixtures/g07_owner_20261115_second_cm_publication_gap_sanitized.json").read_text())
GATE=json.loads((ROOT/"d06/acceptance/d06_g07_final_owner_ci_gate.json").read_text())

def test_guard_first_threshold_crossed_before_post_latch_cm_callback():
    got=analyze_first_latch(DATA)
    assert got["status"]=="HOLD_CM_SOURCE_GAP_WITH_FIRST_GUARD_LATCH"
    assert got["first_safety_transition"]=="UPSTREAM_STALE_AFTER_MOTION"
    assert got["first_boundary"]=="guard_internal_cm"
    assert got["cm_age_at_latch_ms"]==169.168036
    assert got["earliest_native_threshold_crossing_ms_before_latch"]==19.168036
    assert got["limit_ms"]==150
    assert got["cm_source_gap_ms"]==184.414666
    assert got["cm_receive_gap_ms"]==184.358695
    assert got["observer_gap_ms"]==223.656034
    assert got["sequence_increment"]==1
    assert got["supervisor_publications_inside_cm_gap"]==4
    assert got["cm_upstream_cmd_vel_smoothed_messages_in_source_gap"]==3
    assert DATA["post_latch_joined_pair"]["confirmed_cmd_vel_smoothed_nonzero_mps"]>0
    assert got["upstream_max_gap_ms"]==89.04962
    assert got["cm_publisher_interval_gap_confirmed_post_latch"] is True
    assert got["cm_callback_processing_delay_proven"] is False
    assert got["guard_latch_caused_by_missing_cm_input"] is True
    assert got["actual_root_cause_sched_or_cm_execution_proven"] is False
    assert got["owner_l3_accepted"] is False

def test_right_censoring_not_misclassified_as_no_first_timing_breach():
    got=analyze_first_latch(DATA)
    assert DATA["observation_window"]["first_pre_latch_observer_violation"] is None
    assert got["pre_latch_cm_observer_evidence_right_censored"] is True
    assert got["status"]!="NO_FIRST_DELIVERY_VIOLATION_OBSERVED_NOT_ACCEPTED"
    assert got["safety_pass"] is False

def test_noncausal_receive_only_delay_keeps_native_guard_receipt_unverified():
    import copy
    x=copy.deepcopy(DATA)
    x["first_guard_latch"]=None
    x["post_latch_joined_pair"]["rmw_source_gap_ms"]=70.0
    x["post_latch_joined_pair"]["rmw_received_gap_ms"]=380.0
    got=analyze_first_latch(x)
    assert got["status"]=="HOLD_CM_RMW_RECEIVE_GAP_NATIVE_GUARD_UNVERIFIED"
    assert got["guard_latch_caused_by_missing_cm_input"] is False
    assert got["safety_pass"] is False

def test_real_owner_attempt_revokes_previous_gui_l2_admission_before_goal():
    assert GATE["status"]=="HOLD_OWNER_L3_FIRST_CM_SOURCE_TTL_GAP"
    assert GATE["allow_one_final_wsl2_owner"] is False
    assert GATE["allowed_final_owner_attempts"]==0
    assert GATE["last_actual_concurrent_gui_l2_run_id"]==43667573251
    assert GATE["whole_concurrent_gui_l2_pass"] is True
    assert GATE["new_owner_l3_cm_rmw_source_gap_ms"]==184.414666
    assert GATE["new_owner_l3_first_guard_cm_age_ms"]==169.168036
    assert GATE["owner_l3_accepted"] is False

def test_sanitized_fixture_never_contains_private_identifiers_or_real_messages():
    s=(ROOT/"d06/tests/fixtures/g07_owner_20261115_second_cm_publication_gap_sanitized.json").read_text()
    for forbidden in ("/home/","G07/live","p2-l3-owner-","cWIDYQe3",
                      "00d6dd6e","rosbag2_0.db3","AXIA_CLOUD_CI",
                      "YES-P2-G07-GOAL","base_scan"):
        assert forbidden not in s
