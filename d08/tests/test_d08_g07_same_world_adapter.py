"""D08 D04-D07 single-session RED contract: reuse G07 world, never a 2nd simulator.

Public L0 only: synthetic XML fixtures are *not* real Gazebo/ROS acceptance.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))
sys.path.insert(0,str(ROOT/"d08/tests"))
from test_d08_collocated_human_proxy import WORLD, ROBOT
from d08_g07_same_world_adapter import build_g07_d08_camera_world

TEST_SHA="efff0fb8bf941de74572336d1988dfb0005e11f7"

def sources(tmp_path, rate="10"):
    w=tmp_path/"g07_world.sdf.xacro"
    # G07 contact fixture and read-only native witness must stay untouched.
    w.write_text(WORLD.replace(
        '</world>',
        '<plugin filename="libaxia_g07_s02_ecm_witness.so" name="axia::G07S02Witness"/></world>'))
    r=tmp_path/"g07_demo_waffle.sdf.xacro"
    r.write_text(ROBOT.replace(
        '<link name="camera_link"/>',
        '<link name="camera_link"/>'
        '<link name="base_scan">'
        '<sensor name="hls_lfcd_lds" type="gpu_lidar">'
        f'<update_rate>{rate}</update_rate><visualize>false</visualize>'
        '</sensor></link>'
    ))
    mesh=tmp_path/"walk.dae"
    mesh.write_text("fixture-dae")
    return w,r,mesh

def test_g07_10hz_world_and_d08_registered_camera_are_one_preserved_session(tmp_path):
    w,r,mesh=sources(tmp_path)
    src_world=w.read_bytes()
    src_robot=r.read_bytes()
    manifest=build_g07_d08_camera_world(w,r,mesh,tmp_path/"out",student_sha=TEST_SHA)
    world=ET.parse(manifest["world"]).getroot()
    robot=ET.parse(manifest["robot_sdf"]).getroot()
    assert len(world.findall("./world"))==1
    assert len(world.findall(".//model[@name='axia_p2_g07_obstacle']"))==1
    assert len(world.findall(".//plugin[@name='gz::sim::systems::Contact']"))==1
    assert len(world.findall(".//plugin[@name='axia::G07S02Witness']"))==1
    assert len(world.findall(".//actor"))==0
    assert len(world.findall(".//visual[@name='axia_d08_human_mesh']"))==1
    assert len(world.findall(".//collision[@name='obstacle_collision']"))==1
    assert len(robot.findall(".//sensor[@name='axia_d08_registered_rgbd']"))==1
    assert robot.findtext(".//sensor[@name='axia_d08_registered_rgbd']/always_on")=="false"
    assert manifest["rgbd_on_demand_configured"] is True
    assert manifest["rgbd_actual_subscriber_render_suspension_verified"] is False
    assert robot.find(".//sensor[@name='hls_lfcd_lds']/update_rate").text=="10"
    assert manifest["upstream_g07_lidar_10hz_preserved"] is True
    assert manifest["g07_student_source_sha"]==TEST_SHA
    assert manifest["single_world_runtime_claimed"] is False
    assert manifest["moving_goal_verified"] is False
    assert manifest["d06_cm_guard_ttl_verified"] is False
    assert manifest["yolo_person_valid_verified"] is False
    assert w.read_bytes()==src_world
    assert r.read_bytes()==src_robot

@pytest.mark.parametrize("rate",["5","8","12"])
def test_g07_bad_lidar_profile_is_never_silently_corrected(tmp_path,rate):
    w,r,mesh=sources(tmp_path,rate)
    with pytest.raises(ValueError,match="G07_10HZ"):
        build_g07_d08_camera_world(w,r,mesh,tmp_path/"out",student_sha=TEST_SHA)
    assert not (tmp_path/"out").exists()

def test_g07_source_custody_and_single_collision_are_fail_closed(tmp_path):
    w,r,mesh=sources(tmp_path)
    with pytest.raises(ValueError,match="G07_STUDENT_SHA"):
        build_g07_d08_camera_world(w,r,mesh,tmp_path/"out",student_sha="latest")
    w.write_text(w.read_text().replace('name="obstacle_collision"','name="wrong_collision"'))
    with pytest.raises(ValueError,match="COLLISION"):
        build_g07_d08_camera_world(w,r,mesh,tmp_path/"out",student_sha=TEST_SHA)
    assert not (tmp_path/"out").exists()
