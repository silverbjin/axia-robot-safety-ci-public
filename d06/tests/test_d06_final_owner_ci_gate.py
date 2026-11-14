"""D06 public release gate: no repeated Owner runs while real L2 is HOLD."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WRAPPER=(ROOT/"d06/scripts/d06_gazebo_rviz_owner_wsl2_once.sh").read_text()

def test_current_real_l2_failure_blocks_instructor_goal_owner_before_private_checkout():
    gate=ROOT/"d06/acceptance/d06_g07_final_owner_ci_gate.json"
    assert gate.is_file()
    value=json.loads(gate.read_text())
    assert value["status"]=="HOLD_CI_REAL_G07_L2"
    assert value["allow_one_final_wsl2_owner"] is False
    assert value["last_real_gazebo_ci_run_id"]==43596963732
    assert value["last_real_gazebo_ci_attempt"]==3
    assert value["last_real_gazebo_ci_job_id"]==132455451421
    assert value["current_ci_instructor_candidate_sha"]=="8fd137d656ef226940ca38d65ea0a5e473b8ac55"
    assert value["first_failure_kind"]=="ODOM_OBSERVER_RMW_RECEIVE_GAP_AND_SCAN_300MS"
    assert value["odom_callback_gap_ms"]>300
    assert value["odom_rmw_received_gap_ms"]>300
    assert value["odom_rmw_source_gap_ms"]<300
    assert value["scan_max_gap_ms"]>300
    assert value["guard_latched"] is False
    assert value["attempt_results"]==["PASS","PASS","FAIL"]
    assert value["whole_ci_l2_pass"] is False
    assert value["certified_estop"] is False

def test_WSL2_wrapper_requires_ci_admission_prior_to_any_goal_or_private_source():
    needle="D06_FINAL_OWNER_BLOCKED_CI_L2_HOLD"
    assert needle in WRAPPER
    assert "d06_g07_final_owner_ci_gate.json" in WRAPPER
    assert "allow_one_final_wsl2_owner" in WRAPPER
    assert "ADMITTED_FINAL_OWNER_ONLY" in WRAPPER
    assert "D06_FINAL_OWNER_ADMISSION_ACCEPTED" in WRAPPER
    assert WRAPPER.index(needle)<WRAPPER.index("gh auth status")
    assert WRAPPER.index(needle)<WRAPPER.index('bash "$RELEASE"')
    assert 'YES-P2-G07-GOAL' in WRAPPER
    assert 'AXIA_G07_CI_SIM_GOAL_ALLOWED=1' not in WRAPPER

def test_ci_final_gate_is_read_only_and_cannot_be_overridden_by_env_only():
    assert "AXIA_D06_FINAL_OWNER_ADMITTED=1" not in WRAPPER
    assert 'D06_FINAL_OWNER_BLOCKED_CI_L2_HOLD' in WRAPPER
    assert "D06_FINAL_OWNER_GATE_SHA_MISMATCH" in WRAPPER
