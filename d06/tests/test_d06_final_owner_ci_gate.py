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
    assert value["last_real_gazebo_ci_run_id"]==43592074676
    assert value["current_ci_instructor_candidate_sha"]=="97f2044404a8b90e9c8f4b3010c0796eef87feff"
    assert value["first_failure_kind"]=="CM_RMW_PUBLICATION_GAP_AND_GUARD_STALE_150MS"
    assert value["cm_source_gap_ms"]>150
    assert value["cm_observer_callback_gap_ms"]>150
    assert value["guard_cm_age_ms"]>150
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
