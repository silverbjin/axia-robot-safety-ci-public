"""D08 real Owner screenshot: person too close; narrow visual obstacle gap.

Public checks only non-secret one-world SDF geometry. Do not claim a moving
Nav2 path from this XML-only test; the private Owner checks ComputePathToPose.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import math
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_live_world import build_overlay

WORLD='''<sdf version="1.9"><world name="default">
<plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>
<model name="axia_p2_g07_obstacle"><link name="fixture"/></model>
</world></sdf>'''
ROBOT='''<sdf version="1.9"><model name="turtlebot3_waffle">
<link name="camera_link"/>
<plugin name="upstream_drive" filename="upstream"/></model></sdf>'''

def test_field_layout_visual_farther_and_p2_physics_unchanged(tmp_path):
    w=tmp_path/'world.sdf.xacro';w.write_text(WORLD)
    r=tmp_path/'waffle.sdf.xacro';r.write_text(ROBOT)
    actor=tmp_path/'person.dae';actor.write_bytes(b'dummy')
    m=build_overlay(w,r,actor,tmp_path/'out')
    world=ET.parse(m['world']).getroot()
    robot=ET.parse(m['robot_sdf']).getroot()
    person=world.find(".//actor[@name='axia_d08_visual_person']")
    assert person is not None
    poses=[tuple(float(n) for n in p.text.split())
           for p in person.findall('.//trajectory/waypoint/pose')]
    assert len(poses)>=3
    assert all(x>=-0.65 and abs(y+.5)<=.24 for x,y,*_ in poses)
    assert min(x+2.0 for x,y,*_ in poses)>=1.35
    assert float(person.findtext('skin/scale'))<=.85
    assert len(world.findall(".//model[@name='axia_p2_g07_obstacle']"))==1
    s=robot.find(".//sensor[@name='axia_d08_registered_rgbd']")
    assert 1.2<=float(s.findtext('camera/horizontal_fov'))<=1.5
    assert m['rgbd_sensor_pitch_rad']<0
    assert len(robot.findall('.//plugin'))==1
    assert not m['actor_physics_collision']
    assert not m['visual_person_same_as_physical_obstacle']
    assert not m['collision_ground_truth_verified']

def test_visual_actor_is_not_collision_obstacle_pass_claim(tmp_path):
    w=tmp_path/'world.sdf.xacro';w.write_text(WORLD)
    r=tmp_path/'waffle.sdf.xacro';r.write_text(ROBOT)
    actor=tmp_path/'person.dae';actor.write_bytes(b'dummy')
    manifest=build_overlay(w,r,actor,tmp_path/'out')
    assert manifest['physical_obstacle_static_gap_not_certified'] is True
    assert manifest['robot_drive_model_modified'] is False
    assert manifest['goal_sent'] is False
