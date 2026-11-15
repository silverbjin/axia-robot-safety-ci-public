"""D06 public gate: only one exact-source real L2-proven Owner WSL2 final signoff."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WRAPPER=(ROOT/"d06/scripts/d06_gazebo_rviz_owner_wsl2_once.sh").read_text()

def test_old_headless_three_passes_and_new_gui_l2_allow_one_manual_l3():
    value=json.loads((ROOT/"d06/acceptance/d06_g07_final_owner_ci_gate.json").read_text())
    assert value["schema"]=="axia.d06.final_owner_ci_gate_v1"
    assert value["status"]=="ADMITTED_FINAL_OWNER_ONLY"
    assert value["allow_one_final_wsl2_owner"] is True
    assert value["allowed_final_owner_attempts"] == 1
    assert value["whole_ci_l2_pass"] is True
    assert value["whole_concurrent_gui_l2_pass"] is True
    assert value["last_actual_concurrent_gui_l2_run_id"] == 43667573251
    assert value["previous_failed_concurrent_gui_l2_run_id"]==43664497257
    assert value["last_real_gazebo_ci_run_id"]==43609296371
    assert value["last_owner_failure_class"]=="GUARD_CM_TTL_AFTER_RMW_SOURCE_AND_OBSERVER_GAPS"
    assert value["last_real_gazebo_ci_attempt"]==3
    assert value["last_real_gazebo_ci_job_id"]==132492476795
    assert value["current_ci_instructor_candidate_sha"]=="3593125fdfe489aead3e892daf39563df0c0d4a0"
    assert value["private_instructor_sha"]=="3593125fdfe489aead3e892daf39563df0c0d4a0"
    assert value["p4_release_sha"]=="f443fb4d6b246db2024dff225c7b77c97d7f50a9"
    assert value["attempt_results"]==["PASS","PASS","PASS"]
    assert value["actual_wslg_simultaneous_gazebo_rviz_verified"] is False
    assert value["certified_estop"] is False
    assert value["owner_l3_accepted"] is False

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

def test_admitted_owner_wrapper_requires_exact_ci_pinned_release_and_tree():
    assert "f443fb4d6b246db2024dff225c7b77c97d7f50a9" in WRAPPER
    assert "3593125fdfe489aead3e892daf39563df0c0d4a0" in WRAPPER
    assert "3ebf3efa35340dabab75a18418788c53ae54f308" in WRAPPER
    assert "d1769b8675c85e7ee564966637cef9113435904a" not in WRAPPER
    assert "afe4e9ae3f6542ef7b2bd3097ce5c15ae5a5ddcc" not in WRAPPER
