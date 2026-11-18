"""D08 Task02 RED: actual official Nav2 Action aborted because AMCL pose absent.

Validate only a free native /map sample. ROS localization remains L2.
"""
from pathlib import Path
from types import SimpleNamespace as S
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_amcl_initial_pose import inspect_free_map_pose


def grid(value=0,frame="map"):
    # native 10x10, .1m grid, origin -2.5,-1.0, robot spawn -2.0,-0.5
    return S(header=S(frame_id=frame),
       info=S(width=10,height=10,resolution=.1,
       origin=S(position=S(x=-2.5,y=-1.0),
                orientation=S(x=0.,y=0.,z=0.,w=1.))),
       data=[value]*100)

def test_real_map_geometry_contract_free_spawn_only_l0():
    v=inspect_free_map_pose(grid(),-2.0,-.5)
    assert v["map_frame"]=="map"
    assert v["spawn_map_xy"]==[-2.,-.5]
    assert v["free_checked_cells"]>=1
    assert v["localization_verified"] is False
    assert len(v["map_data_sha256"])==64

def test_reject_real_map_unknown_occupied_outside_or_frame_mismatch():
    for value in (-1,50,100):
        with pytest.raises(ValueError,match="MAP_NOT_FREE"):
            inspect_free_map_pose(grid(value),-2.,-.5)
    with pytest.raises(ValueError,match="MAP_OUTSIDE"):
        inspect_free_map_pose(grid(),10.,10.)
    with pytest.raises(ValueError,match="REAL_MAP_INVALID"):
        inspect_free_map_pose(grid(frame="odom"),-2.,-.5)

def test_existing_official_path_no_goal_service_amcl_chain():
    p=Path(__file__).resolve().parents[1]/"harness"/"d08_nav2_path_preflight.py"
    s=p.read_text()
    assert "admit_actual_amcl" in s
    assert "initialize_amcl" in s
    assert "real_amcl_and_tf" in s
    assert "D08_OFFICIAL_NAV2_PLANNER_UNAVAILABLE" in s
    assert "NavigateToPose.Goal(" not in s
    assert "FollowPath.Goal(" not in s
