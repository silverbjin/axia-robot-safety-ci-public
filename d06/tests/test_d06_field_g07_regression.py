"""D06 field regression from a SANITIZED G07 first-failure boundary, no raw Owner data.

Source: Owner TAR IB7mAJRW; no UUID, names, paths or telemetry arrays uploaded.
This tests detection and fail-closed UX, NOT proof of future GUI/Guard behavior.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W = (ROOT/"d06/scripts/d06_gazebo_rviz_owner_wsl2_once.sh").read_text()
SIDECAR = (ROOT/"d06/scripts/d06_rviz_sidecar.sh").read_text()
RVIZ = (ROOT/"d06/rviz/d06_safety_bubble.rviz").read_text()


def field_boundary():
    return {
        "first_timing_violation": {
            "channel": "pre_guard",
            "first_violation_sec": 0.172738929,
            "limit_sec": 0.15,
        },
        "first_guard_latch": {
            "reason": "UPSTREAM_STALE_AFTER_MOTION",
            "cm_age_sec": 0.1815524,
            "supervisor_age_sec": 0.056140746,
        },
        "cm_guard_receive_skew": {
            "guard_cm_age_at_latch_sec": 0.1815524,
            "observer_cm_age_at_latch_sec": 0.000105422,
            "observer_newer_cm_samples": 2,
        },
        "goal_sent": True,
        "goal_status_at_clear": 2,
        "status": "BLOCKED",
        "gate_accepted": False,
    }


def test_owner_field_first_violation_is_detected_and_not_called_a_g07_pass():
    from d06.live.d06_g07_field_triage import classify_owner_field
    result = classify_owner_field(field_boundary())
    assert result["status"] == "HOLD_G07_GUARD_CM_DELIVERY_TTL"
    assert result["first_channel"] == "pre_guard"
    assert result["first_interval_sec"] == 0.172738929
    assert result["guard_latch_cm_age_sec"] == 0.1815524
    assert result["guard_receive_lag_possible"] is True
    assert result["cm_publisher_stopped_proven"] is False
    assert result["goal_completion_verified"] is False
    assert result["safety_pass"] is False


def test_successful_clear_does_not_hide_subsequent_slowdown_guard_latch():
    from d06.live.d06_g07_field_triage import classify_owner_field
    sample = field_boundary()
    sample["goal_status_at_clear"] = 2
    got = classify_owner_field(sample)
    assert got["status"] != "PASS"
    assert got["goal_completion_verified"] is False


def test_private_source_pin_is_current_released_p4_g07_rmw_diagnostic():
    # The old eb984 Owner source was a real scoped success but lacks P4 first-RMW fields.
    assert "d1769b8675c85e7ee564966637cef9113435904a" in W
    assert "afe4e9ae3f6542ef7b2bd3097ce5c15ae5a5ddcc" in W
    assert "axia_p4_g11_owner_g07_rmw_provenance_once.sh" in W
    assert "eb984b73138e592caa67426eed9c60dde2ca2ebd" not in W
    assert "YES-P2-G07-GOAL" in W
    assert "AXIA_G07_CI_SIM_GOAL_ALLOWED=1" not in W
    assert "D06_GAZEBO_GUI_NOT_YET_VERIFIED" in W


def test_readonly_gui_does_not_compete_at_normal_safety_priority():
    assert "nice -n 15" in SIDECAR
    assert "Frame Rate: 8" in RVIZ
    assert "D06_RVIZ_DIAGNOSTICS" in SIDECAR
    assert "D06_RVIZ_NOT_CONFIRMED" in W
    assert "D06_RVIZ_SIDECAR_EXITED_BEFORE_OWNER_COMPLETION" in W
    assert "D06_GUI_EVIDENCE=" in W
    assert "D06_G07_POSTRUN_TRIAGE" in W
    # Never relax watchdog thresholds to turn field failure green.
    for forbidden in ("AXIA_G07_CI_SIM_GOAL_ALLOWED=1","CM_TTL_SEC=0.25",
                      "AXIA_P2_GUARD_BYPASS","echo YES-P2-G07-GOAL"):
        assert forbidden not in W+SIDECAR


# Sanitized second real WSL2 G07 field case (Nfb3pALe). Values supplied by
# Owner log, no private raw ROS messages, UUID, host paths or solution code.
def field_scan_first_then_guard_cm():
    return {
        "status": "BLOCKED",
        "goal_sent": True,
        "goal_status_at_clear": 2,
        "goal_terminal_statuses_after_latch": [3, 5],
        "first_timing_violation": {
            "channel": "scan",
            "first_violation_from": 11523.987724576,
            "first_violation_at": 11524.352366686,
            "first_violation_sec": 0.3646421100002044,
            "limit_sec": 0.3,
            "first_violation_stage": "UNKNOWN_STOP_TIME",
        },
        "first_guard_latch": {
            "reason": "UPSTREAM_STALE_AFTER_MOTION",
            "tick_monotonic": 11527.048956316,
            "cm_rx_monotonic": 11526.895938226,
            "cm_age_sec": 0.15301809000084177,
            "supervisor_age_sec": 0.09366804000092088,
            "supervisor_authorized_goal": True,
            "supervisor_fsm": "NORMAL",
        },
        "first_cm_supervisor_rmw_window": {
            "status": "NO_CM_SOURCE_GAP_OBSERVED",
            "classification": "UNVERIFIED",
            "cm_source_gap_sec": None,
        },
        "final_command_zero_after_latch": True,
        "odom_post_stop_dwell_proven": False,
        "gate_accepted": False,
    }


def test_new_field_first_scan_300ms_breach_is_not_hidden_by_later_guard_150ms():
    from d06.live.d06_g07_field_triage import classify_owner_field
    r=classify_owner_field(field_scan_first_then_guard_cm())
    assert r["status"]=="HOLD_G07_SCAN_THEN_GUARD_CM_TTL"
    assert r["first_channel"]=="scan"
    assert r["first_interval_sec"]==0.3646421100002044
    assert r["first_channel_limit_sec"]==0.3
    assert r["scan_violated_before_guard_latch"] is True
    assert r["guard_latch_cm_age_sec"]==0.15301809000084177
    assert r["scan_caused_guard_latch_proven"] is False
    assert r["goal_completion_verified"] is False
    assert r["safety_pass"] is False


def test_rmw_no_source_gap_observed_with_unverified_source_timing_is_not_a_pass():
    from d06.live.d06_g07_field_triage import classify_owner_field
    r=classify_owner_field(field_scan_first_then_guard_cm())
    assert r["cm_publisher_stopped_proven"] is False
    assert r["cm_publisher_healthy_proven"] is False
    assert r["rmw_source_attribution"]=="UNVERIFIED"
    assert r["owner_l3_accepted"] is False


def test_goal_terminal_events_and_zero_twist_do_not_substitute_for_stop_odom_dwell():
    from d06.live.d06_g07_field_triage import classify_owner_field
    r=classify_owner_field(field_scan_first_then_guard_cm())
    assert r["final_zero_after_guard_latch_observed"] is True
    assert r["physical_stop_dwell_verified"] is False
    assert r["goal_completion_verified"] is False


def test_public_ci_has_actual_pinned_gazebo_moving_goal_cross_node_ttl_workflow():
    workflow = (ROOT/".github/workflows/d06-g07-real-moving-timing-l2.yml")
    assert workflow.is_file(), "Do not call source-only L0/ROS L1 real Gazebo L2"
    s = workflow.read_text()
    for token in (
        "axia-instructor-sealed",
        "ghcr.io/silverbjin/axia-g07-runtime@sha256:",
        "afe4e9ae3f6542ef7b2bd3097ce5c15ae5a5ddcc",
        "AXIA_G07_CI_SIM_GOAL_ALLOWED",
        "p2_no_goal_smoke_ci.sh",
        "actual_ros_events.jsonl",
        "first_pre_latch_delivery_timing",
        "cm_rmw_provenance",
        "scan",
        "pre_guard",
        "0.3",
        "0.15",
        "odom_stopped_dwell_sec",
        "gate_accepted",
        "NO_WSL2_OWNER_ACCEPTANCE",
        "rm -rf -- instructor",
    ):
        assert token in s, token
    assert "AXIA_P2_GUARD_BYPASS" not in s
    assert "CM_TTL_SEC=0.25" not in s
    assert "YES-P2-G07-GOAL" not in s
