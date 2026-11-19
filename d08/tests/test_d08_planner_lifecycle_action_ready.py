"""RED regression for real #44459386016: Action server exists but planner is INACTIVE.

Read-only D08 ComputePathToPose may be requested only AFTER official
/planner_server/get_state reports ACTIVE. NO NavigateToPose / cmd_vel / TTL edit.
"""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))
from d08_nav2_path_preflight import assess_planner_lifecycle_observation

def test_action_server_visible_is_not_planner_active():
    with pytest.raises(RuntimeError,match="D08_PLANNER_LIFECYCLE_NOT_ACTIVE"):
        assess_planner_lifecycle_observation(["unconfigured","inactive"])
    result=assess_planner_lifecycle_observation(["unconfigured","inactive","active"])
    assert result["official_planner_active"] is True
    assert result["observed_states"][-1]=="active"

def test_real_action_sent_only_after_active_get_state():
    src=(ROOT/"d08/harness/d08_nav2_path_preflight.py").read_text()
    assert "lifecycle_msgs.srv import GetState" in src
    assert "wait_for_planner_active(node" in src
    assert "verdict['planner_lifecycle']=" in src
    assert src.index("verdict['planner_lifecycle']=")<src.index("accepted=client.send_goal_async(goal)")
    assert "D08_PLANNER_LIFECYCLE_NOT_ACTIVE" in src

def test_existing_nogoal_and_amcl_guards_remain():
    src=(ROOT/"d08/harness/d08_nav2_path_preflight.py").read_text()
    assert "from d08_amcl_initial_pose import admit_actual_amcl" in src
    assert "navigate_goal_sent':False" in src
    assert "control_published':False" in src
    assert "rclpy.spin_until_future_complete(node,future,timeout_sec=timeout_s)" in src
