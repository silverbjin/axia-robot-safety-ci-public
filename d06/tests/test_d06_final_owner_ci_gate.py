"""D06 public release gate: no repeated Owner runs while real L2 is HOLD."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WRAPPER=(ROOT/"d06/scripts/d06_gazebo_rviz_owner_wsl2_once.sh").read_text()

def test_three_identical_source_real_l2_cold_starts_admit_only_one_final_owner_check():
    value=json.loads((ROOT/"d06/acceptance/d06_g07_final_owner_ci_gate.json").read_text())
    assert value["schema"]=="axia.d06.final_owner_ci_gate_v1"
    assert value["status"]=="ADMITTED_FINAL_OWNER_ONLY"
    assert value["allow_one_final_wsl2_owner"] is True
    assert value["whole_ci_l2_pass"] is True
    assert value["last_real_gazebo_ci_run_id"]==43609296371
    assert value["last_real_gazebo_ci_attempt"]==3
    assert value["last_real_gazebo_ci_job_id"]==132492476795
    assert value["current_ci_instructor_candidate_sha"]=="c44414f8e3bad37a349565f211d554540cccb062"
    assert value["private_instructor_sha"]=="c44414f8e3bad37a349565f211d554540cccb062"
    assert value["p4_release_sha"]=="67b8995cc7fdd506b12f348fc7e5241dcedddc67"
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
    assert "67b8995cc7fdd506b12f348fc7e5241dcedddc67" in WRAPPER
    assert "c44414f8e3bad37a349565f211d554540cccb062" in WRAPPER
    assert "d2e3044689a5873cd61d6bc5f84a40b20a81f84e" in WRAPPER
    assert "d1769b8675c85e7ee564966637cef9113435904a" not in WRAPPER
    assert "afe4e9ae3f6542ef7b2bd3097ce5c15ae5a5ddcc" not in WRAPPER
