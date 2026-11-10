"""Regression for Owner screenshot p2-l3-owner-h14ERUdL.

One SDF model had skinned walk.dae AND head/torso/leg fallback visuals drawn
on top of each other. Keep precisely one visible human representation.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_live_world import build_overlay

WORLD='''<sdf version="1.9"><world name="default">
<plugin name="gz::sim::systems::Contact" filename="gz-sim-contact-system"/>
<model name="axia_p2_g07_obstacle"><pose>-0.58 -0.5 0.24 0 0 0</pose>
<static>true</static><link name="obstacle_link">
<collision name="obstacle_collision"><geometry><cylinder>
<radius>0.07</radius><length>0.48</length>
</cylinder></geometry></collision>
<visual name="obstacle_visual"><geometry><cylinder>
<radius>0.07</radius><length>0.48</length>
</cylinder></geometry></visual>
<sensor name="axia_contact" type="contact"><contact>
<collision>obstacle_collision</collision></contact></sensor>
</link></model></world></sdf>'''
ROBOT='<sdf version="1.9"><model name="turtlebot3_waffle"><link name="camera_link"/></model></sdf>'

def test_only_one_visual_inside_existing_physical_proxy(tmp_path):
    w=tmp_path/'w.xacro';w.write_text(WORLD)
    r=tmp_path/'r.xacro';r.write_text(ROBOT)
    mesh=tmp_path/'walk.dae';mesh.write_text('fixture')
    result=build_overlay(w,r,mesh,tmp_path/'out')
    world=ET.parse(result['world']).getroot()
    model=world.find(".//model[@name='axia_p2_g07_obstacle']")
    link=model.find("./link[@name='obstacle_link']")
    visuals=link.findall('./visual')
    assert len(visuals)==1, [v.get('name') for v in visuals]
    assert visuals[0].get('name')=='axia_d08_human_mesh'
    assert model.findtext('./static')=='true'
    assert link.find('./collision[@name="obstacle_collision"]') is not None
    assert link.find('./sensor[@name="axia_contact"]') is not None
    assert world.find('.//actor') is None
    assert result['human_visual_attached_to_physical_model']
    assert not result['collision_ground_truth_verified']

def test_do_not_weaken_approved_camera_and_CM_geometry(tmp_path):
    w=tmp_path/'w.xacro';w.write_text(WORLD)
    r=tmp_path/'r.xacro';r.write_text(ROBOT)
    a=tmp_path/'a.dae';a.write_text('fixture')
    m=build_overlay(w,r,a,tmp_path/'out')
    tree=ET.parse(m['world']).getroot()
    link=tree.find(".//model[@name='axia_p2_g07_obstacle']/link")
    assert link.findtext("./collision/geometry/cylinder/radius")=="0.07"
    assert link.findtext("./collision/geometry/cylinder/length")=="0.48"
    assert m['rgbd_horizontal_fov_rad']==1.35
    assert m['visual_person_same_as_physical_obstacle']
