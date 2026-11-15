"""New GUI-load actual L2 evidence must re-admit exactly one manual Owner L3.
Preserves both older G85 Owner failure and headless 3/3 historical successes.
No ROS, Goal, raw bag, or WSLg claim in this source-only regression.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
GATE=json.loads((ROOT/"d06/acceptance/d06_g07_final_owner_ci_gate.json").read_text())
WRAPPER=(ROOT/"d06/scripts/d06_gazebo_rviz_owner_wsl2_once.sh").read_text()

def test_actual_new_gui_load_full_l2_is_required_before_owner_readmission():
    assert GATE["status"]=="ADMITTED_FINAL_OWNER_ONLY"
    assert GATE["allow_one_final_wsl2_owner"] is True
    assert GATE["allowed_final_owner_attempts"]==1
    assert GATE["whole_concurrent_gui_l2_pass"] is True
    assert GATE["last_actual_concurrent_gui_l2_pass"] is True
    assert GATE["last_actual_concurrent_gui_l2_run_id"]==43667573251
    assert GATE["last_actual_concurrent_gui_l2_workflow_sha"]=="8eeb69c442a60be434d8c4fc1a153788aebed7e3"
    assert GATE["private_instructor_sha"]=="3593125fdfe489aead3e892daf39563df0c0d4a0"
    assert GATE["private_instructor_tree"]=="3ebf3efa35340dabab75a18418788c53ae54f308"
    assert GATE["p4_release_sha"]=="f443fb4d6b246db2024dff225c7b77c97d7f50a9"
    assert GATE["owner_l3_accepted"] is False
    assert GATE["actual_wslg_simultaneous_gazebo_rviz_verified"] is False
    assert GATE["certified_estop"] is False

def test_historical_failures_and_no_gui_headless_success_still_anchored():
    assert GATE["attempt_results"]==["PASS","PASS","PASS"]
    assert GATE["last_real_gazebo_ci_run_id"]==43609296371
    assert GATE["last_owner_failure_class"]=="GUARD_CM_TTL_AFTER_RMW_SOURCE_AND_OBSERVER_GAPS"
    assert GATE["previous_failed_concurrent_gui_l2_run_id"]==43664497257
    assert GATE["historical_failures_are_not_erased"] is True
    assert GATE["last_owner_raw_capture_complete"] is False

def test_owner_source_pins_and_ci_no_tty_goal_never_auto_approves():
    for sha in ("3593125fdfe489aead3e892daf39563df0c0d4a0",
                "3ebf3efa35340dabab75a18418788c53ae54f308",
                "f443fb4d6b246db2024dff225c7b77c97d7f50a9"):
        assert sha in WRAPPER
    assert "D06_BLOCKED_REAL_OWNER_INTERACTIVE_TTY_REQUIRED" in WRAPPER
    assert 'value.get("whole_concurrent_gui_l2_pass") is True' in WRAPPER
    assert "AXIA_G07_CI_SIM_GOAL_ALLOWED=1" not in WRAPPER
