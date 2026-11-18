"""Minimal D08 Task02 RED contracts: no fake 3-phase success.

L0 fixtures never prove real ROS/Nav2/Gazebo or actual /scan.
"""
import sys
from pathlib import Path
from types import SimpleNamespace as S
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_same_world_replan import (evaluate_three_phases, _lethal_near,
                                   _path_distance_to_point, CANDIDATE_MAP)

def rows():
    return [
      {"stage":name,"source":"official_compute_path_to_pose","frame":"map",
       "goal_sent":False,"poses":[[-2,-.5],[-1.99,-.2],[-1.9,.2]],
       "scan_stamp":s,"costmap_stamp":s,"gazebo_native_ack":True,
       "lethal_near":n,"path_distance_from_obstacle_m":d}
      for name,s,n,d in (("before",1,0,.03),
                         ("intrusion",2,80,.28),
                         ("restored",3,0,.035))]

def test_3_actual_ros_phases_required_same_epoch_no_goal():
    v=evaluate_three_phases(rows(),[.2,.3,.25,.31])
    assert v["detour_delta_m"]==.25
    assert v["restore_delta_m"]==.005
    assert v["actual_cm_safety_ttl_proven"] is False
    assert not v["robot_moving_goal_sent"]

@pytest.mark.parametrize("edit,match",[
  (lambda a:a.pop(1),"THREE_OFFICIAL"),
  (lambda a:a[1].update(source="set_pose_guessed"),"PROVENANCE"),
  (lambda a:a[1].update(goal_sent=True),"PROVENANCE"),
  (lambda a:a[1].update(scan_stamp=.9),"STALE"),
  (lambda a:a[1].update(costmap_stamp=.9),"STALE"),
  (lambda a:a[1].update(lethal_near=0),"OBSTACLE_NOT_MARKED"),
  (lambda a:a[2].update(lethal_near=50),"OBSTACLE_NOT_CLEARED"),
  (lambda a:a[1].update(path_distance_from_obstacle_m=.10),"DETOUR_NOT_OBSERVED"),
  (lambda a:a[2].update(path_distance_from_obstacle_m=.3),"RESTORATION_NOT_OBSERVED"),
])
def test_3_stage_provenance_fail_closed(edit,match):
    a=rows();edit(a)
    with pytest.raises(ValueError,match=match):
        evaluate_three_phases(a,[.2,.3,.21])

def test_first_real_scan_gap_must_not_relax_500ms():
    with pytest.raises(ValueError,match="FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS"):
        evaluate_three_phases(rows(),[.2,.519095,.18])

def test_native_costmap_lethal_near_uses_map_data_not_pose_guess():
    # 20x20 occupancy grid at -2.5,-.4; candidate -1.97,.17 is inside.
    info=S(width=20,height=20,resolution=.05,
           origin=S(position=S(x=-2.5,y=-.4),
                    orientation=S(x=0.,y=0.,z=0.,w=1.)))
    data=[0]*400
    msg=S(header=S(frame_id="map"),info=info,data=data)
    assert _lethal_near(msg)==0
    ix=int((CANDIDATE_MAP[0]+2.5)/.05)
    iy=int((CANDIDATE_MAP[1]+.4)/.05)
    data[iy*20+ix]=100
    assert _lethal_near(msg)>=1

def test_official_polyline_obstacle_distance_changes():
    before=[[-2,-.5],[-1.97,.17],[-1.7,.7]]
    detour=[[-2,-.5],[-2.45,.17],[-1.7,.7]]
    assert _path_distance_to_point(before,CANDIDATE_MAP)<.03
    assert _path_distance_to_point(detour,CANDIDATE_MAP)>.03
