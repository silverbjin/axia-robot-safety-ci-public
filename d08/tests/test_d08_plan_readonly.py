"""Original P2-G07 constrained physical cylinder must not trigger a blind Goal."""
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))
from d08_nav2_path_preflight import assess_path

def pose(x,y):
    return SimpleNamespace(pose=SimpleNamespace(
       position=SimpleNamespace(x=x,y=y)))

def test_nonempty_live_plan_to_fixed_corridor_is_only_a_candidate():
    result=assess_path([pose(-2,-.5),pose(-1.8,-.47),pose(-1.6,-.5)])
    assert result["path_points"]==3
    assert result["path_length_m"]>=.4
    assert result["goal_xy"]==[-1.6,-.5]
    assert result["end_xy"]==[-1.6,-.5]

@pytest.mark.parametrize('points',[
 [pose(-2,-.5)],
 [pose(-2,-.5),pose(0,0)],
 [pose(-2,-.5),pose(float('nan'),-.5)]
])
def test_short_goal_mismatch_or_nan_plan_fails_closed(points):
    with pytest.raises(ValueError):
        assess_path(points)

def test_compute_path_only_does_not_publish_control_or_claim_clearance():
    code=(ROOT/"d08/harness/d08_nav2_path_preflight.py").read_text()
    assert "ComputePathToPose" in code
    assert "'/compute_path_to_pose'" in code
    assert "NavigateToPose" not in code
    assert "create_publisher(" not in code
    assert "'collision_free_verified':False" in code
    assert "'navigate_goal_sent':False" in code
