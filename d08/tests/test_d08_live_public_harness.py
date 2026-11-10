"""Public D08 L0 fixture: source-identical non-secret Gazebo world/probe contract."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_live_world import build_overlay
from d08_live_readonly_probe import select_pair

WORLD='''<sdf version="1.9"><world name="default">
<plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>
<model name="axia_p2_g07_obstacle"><pose>-0.58 -0.5 0.24 0 0 0</pose>
  <static>true</static><link name="obstacle_link">
  <collision name="obstacle_collision"><geometry><cylinder>
    <radius>0.07</radius><length>0.48</length></cylinder></geometry></collision>
  <visual name="obstacle_visual"><geometry><cylinder>
    <radius>0.07</radius><length>0.48</length></cylinder></geometry></visual>
  <sensor name="axia_contact" type="contact">
    <contact><collision>obstacle_collision</collision></contact></sensor>
  </link></model>
</world></sdf>'''
ROBOT='''<sdf version="1.9"><model name="turtlebot3_waffle">
<link name="camera_link"><sensor name="depth" type="depth_camera"/></link>
<plugin filename="upstream_wheel" name="drive"/>
</model></sdf>'''

def inputs(tmp):
    w=tmp/'world.sdf.xacro';w.write_text(WORLD)
    r=tmp/'robot.sdf.xacro';r.write_text(ROBOT)
    a=tmp/'human.dae';a.write_bytes(b'world test only')
    return w,r,a

def test_world_adds_rgbd_visual_person_and_preserves_physical_fixture(tmp_path):
    w,r,a=inputs(tmp_path)
    before=(w.read_bytes(),r.read_bytes())
    m=build_overlay(w,r,a,tmp_path/'out')
    robot=ET.parse(m['robot_sdf']).getroot()
    world=ET.parse(m['world']).getroot()
    sensor=robot.find(".//sensor[@name='axia_d08_registered_rgbd']")
    assert sensor is not None and sensor.get('type')=='rgbd_camera'
    assert sensor.findtext('topic')=='axia/d08/rgbd'
    assert robot.find(".//plugin[@name='drive']") is not None
    assert world.find(".//model[@name='axia_p2_g07_obstacle']") is not None
    assert world.find(".//actor[@name='axia_d08_visual_person']") is None
    assert world.find(".//visual[@name='axia_d08_human_mesh']") is not None
    assert (w.read_bytes(),r.read_bytes())==before
    assert m['visual_person_same_as_physical_obstacle'] is True
    assert m['human_visual_attached_to_physical_model'] is True
    assert m['actor_physics_collision'] is False
    assert m['robot_drive_model_modified'] is False
    assert m['goal_sent'] is False
    assert m['certified_estop'] is False

def test_missing_real_physical_fixture_fails_closed(tmp_path):
    w,r,a=inputs(tmp_path)
    w.write_text(WORLD.replace('axia_p2_g07_obstacle','wrong_name'))
    with pytest.raises(ValueError,match='PHYSICAL_OBSTACLE'):
        build_overlay(w,r,a,tmp_path/'out')

def test_missing_contact_plugin_fails_closed(tmp_path):
    w,r,a=inputs(tmp_path)
    w.write_text(WORLD.replace('gz::sim::systems::Contact','wrong'))
    with pytest.raises(ValueError,match='CONTACT_WORLD'):
        build_overlay(w,r,a,tmp_path/'out')

def test_no_duplicate_rgbd(tmp_path):
    w,r,a=inputs(tmp_path)
    r.write_text(ROBOT.replace('</link>','<sensor name="axia_d08_registered_rgbd"/></link>'))
    with pytest.raises(ValueError,match='DUPLICATE'):
        build_overlay(w,r,a,tmp_path/'out')

def test_no_overwrite_or_non_dae_or_missing_asset(tmp_path):
    w,r,a=inputs(tmp_path)
    out=tmp_path/'out';out.mkdir()
    with pytest.raises(ValueError,match='OUTPUT_EXISTS'):
        build_overlay(w,r,a,out)
    out.rmdir()
    fake=tmp_path/'human.txt';fake.write_text('no')
    with pytest.raises(ValueError,match='DAE'):
        build_overlay(w,r,fake,out)
    a.unlink()
    with pytest.raises(ValueError,match='ASSET_MISSING'):
        build_overlay(w,r,a,out)

def test_registered_rgbd_pair_requires_real_timing_frame_type():
    rgb={'frame':'axia_d08_rgbd_optical','stamp_ns':1000000000,
         'width':640,'height':480,'encoding':'rgb8'}
    depth={**rgb,'encoding':'32FC1'}
    assert select_pair([rgb],[depth])['stamp_skew_ms']==0.0
    assert select_pair([rgb],[{**depth,'frame':'wrong'}]) is None
    assert select_pair([rgb],[{**depth,'stamp_ns':1200000000}]) is None
    assert select_pair([rgb],[{**depth,'encoding':'rgb8'}]) is None

def test_no_actuator_or_fake_ros_success_in_public_harness():
    code='\n'.join((ROOT/'d08/harness'/x).read_text()
        for x in ('d08_live_world.py','d08_live_readonly_probe.py'))
    for prohibited in ('create_publisher(', 'NavigateToPose(', 'FollowPath(', 'cmd_vel_out_topic'):
        assert prohibited not in code
    assert "'gazebo_actual':False" in code or "'gazebo_actual':False," in code

def test_real_l2_does_not_use_standalone_gz_sdf_parser_for_model_uri(tmp_path):
    # gz sdf -p has no Gazebo resource find callback for official model:// URIs.
    # Validate xacro XML, then let real gz sim load the model + camera.
    source=(ROOT/'d08/scripts/d08_public_gazebo_l2.py').read_text()
    assert "['gz','sdf','-p'" not in source
    assert 'ET.parse(dest)' in source
    assert "gz','sim'" in source
