"""Owner G85: fail-first regression, independent of raw/private source.

These sanitized, goal-relative timings reproduce the first safety boundary.
This L0 check never runs ROS, Gazebo, a moving Goal or an Owner retry.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "d06/tests/fixtures/g07_owner_20261115_first_boundary_sanitized.json"
GATE = ROOT / "d06/acceptance/d06_g07_final_owner_ci_gate.json"


def test_owner_first_guard_and_scan_boundaries_are_not_lost_under_nested_diagnostics():
    from d06.live.d06_g07_field_triage import classify_owner_field
    source = json.loads(FIXTURE.read_text())
    assert "first_timing_violation" not in source  # Original Owner layout.
    result = classify_owner_field(source)
    assert result["first_channel"] == "guard"
    assert abs(result["first_interval_sec"] - 0.162774195) < 1e-8
    assert result["first_channel_limit_sec"] == 0.15
    assert abs(result["first_observer_scan_gap_sec"] - 0.333397997) < 1e-8
    assert abs(result["first_cm_rmw_source_gap_sec"] - 0.15287898) < 1e-8
    assert result["guard_latch_cm_age_sec"] > 0.15
    assert result["scan_caused_guard_latch_proven"] is False
    assert result["cm_callback_processing_delay_proven"] is False
    assert result["physical_stop_dwell_verified"] is False
    assert result["safety_pass"] is False
    assert result["owner_l3_accepted"] is False


def test_old_owner_failure_is_preserved_after_new_independent_ci_l2_readmission():
    receipt = json.loads(GATE.read_text())
    # Original G85 failure remains, while later exact-source GUI-load L2 allows
    # a NEW single manual final WSL2 check; old admission is never replayed.
    assert receipt["status"] == "HOLD_OWNER_L3_FIRST_CM_SOURCE_TTL_GAP"
    assert receipt["allow_one_final_wsl2_owner"] is False
    assert receipt["allowed_final_owner_attempts"] == 0
    assert receipt["previous_failed_concurrent_gui_l2_run_id"] == 43664497257
    assert receipt["last_actual_concurrent_gui_l2_run_id"] == 43667573251
    assert receipt["owner_l3_accepted"] is False
    assert receipt["attempt_results"] == ["PASS", "PASS", "PASS"]
    assert receipt["last_real_gazebo_ci_run_id"] == 43609296371
    assert receipt["last_owner_failure_class"] == "GUARD_CM_TTL_AFTER_RMW_SOURCE_AND_OBSERVER_GAPS"
    assert receipt["actual_wslg_simultaneous_gazebo_rviz_verified"] is False
    assert receipt["certified_estop"] is False


def test_public_fixture_contains_no_original_owner_identifiers_or_private_ros():
    raw = FIXTURE.read_text()
    for forbidden in ("c3c8b122", "/home/", "rosbag2_0.db3", "session.env", "G85prCn1",
                      "AXIA_CLOUD_CI", "YES-P2-G07-GOAL"):
        assert forbidden not in raw
