"""D08/G07 no-fake, read-only pregoal stage scope. L0 only."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from d08_g07_readonly_pregoal import verify_readonly_results,validate_sources

GOOD_PERSON={
    "status":"D08_REAL_LIVE_PERSON_RANGE_2VALID_UNKNOWN_L2_PASS_NO_GOAL",
    "goal_sent":False,"cmd_vel_published":False
}
GOOD_PATH={
    "status":"D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL",
    "robot_moving_goal_sent":False,"actual_cm_safety_ttl_proven":False
}

def test_strict_both_readonly_actual_results_must_pass_before_goal():
    result=verify_readonly_results(dict(GOOD_PERSON),dict(GOOD_PATH))
    assert result["moving_goal_sent"] is False
    assert result["cm_guard_150ms_verified"] is False
    assert result["status"]=="D08_G07_REAL_READONLY_D04_D05_D07_PREGOAL_PASS_NOT_MOVING"

@pytest.mark.parametrize("overrides",[
    {"status":"HOLD"},
    {"goal_sent":True},
    {"cmd_vel_published":True},
])
def test_person_missing_or_control_written_never_admitted(overrides):
    with pytest.raises(ValueError,match="D04_D05"):
        verify_readonly_results({**GOOD_PERSON,**overrides},GOOD_PATH)

@pytest.mark.parametrize("overrides",[
    {"status":"HOLD"},
    {"robot_moving_goal_sent":True},
    {"actual_cm_safety_ttl_proven":True},
])
def test_planner_missing_or_claiming_moving_and_ttl_never_admitted(overrides):
    with pytest.raises(ValueError,match="D07"):
        verify_readonly_results(GOOD_PERSON,{**GOOD_PATH,**overrides})

def test_unknown_source_sha_fails_before_any_ros_or_gazebo(tmp_path):
    with pytest.raises(ValueError,match="SHA"):
        validate_sources(tmp_path/"world",tmp_path/"robot","NOT_SHA","WRONG_SHA")

def test_stage_never_launched_second_world_or_goal():
    source=(Path(__file__).resolve().parents[1]/"scripts"/"d08_g07_readonly_pregoal.py").read_text()
    assert "from d08_live_person_range_session import run_session" in source
    assert "from d08_same_world_replan import run as path_run" in source
    assert "from d08_public_gazebo_l2 import observe_real_front_scan" in source
    assert "ros2 launch " not in source
    assert "NavigateToPose" in source  # mentioned only as a forbidden operation
    assert "cmd_vel" not in [s.strip() for s in source.splitlines() if s.strip().startswith("node.create_publisher(")]
