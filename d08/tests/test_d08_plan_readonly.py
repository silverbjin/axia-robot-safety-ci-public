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
    import ast
    tree=ast.parse(code)
    imported=[alias.name for node in ast.walk(tree)
              if isinstance(node,ast.ImportFrom)
              for alias in node.names]
    called=[node.func.attr if isinstance(node.func,ast.Attribute)
            else node.func.id if isinstance(node.func,ast.Name) else ""
            for node in ast.walk(tree) if isinstance(node,ast.Call)]
    assert "NavigateToPose" not in imported
    assert "create_publisher" not in called
    assert "send_goal_async" in called  # ComputePathToPose action, not NavigateToPose
    assert "'collision_free_verified':False" in code
    assert "'navigate_goal_sent':False" in code
