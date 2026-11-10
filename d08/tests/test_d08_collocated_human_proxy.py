"""RED field regression: D08 human shape and P2 G07 proxy MUST be one entity.

Original owner visual actor at (-0.38,-0.32) stayed behind cylinder, so
YOLO saw a different object from CM. No safety thresholds altered here.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_live_world import build_overlay

WORLD='''<sdf version="1.9"><world name="default">
  <plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>
  <model name="axia_p2_g07_obstacle">
    <pose>-0.58 -0.5 0.24 0 0 0</pose><static>true</static>
    <link name="obstacle_link">
      <collision name="obstacle_collision"><geometry><cylinder>
        <radius>0.07</radius><length>0.48</length>
      </cylinder></geometry></collision>
      <visual name="obstacle_visual"><geometry><cylinder>
        <radius>0.07</radius><length>0.48</length>
      </cylinder></geometry></visual>
      <sensor name="axia_contact" type="contact"><always_on>true</always_on>
        <contact><collision>obstacle_collision</collision></contact>
      </sensor>
    </link>
  </model>
</world></sdf>'''
ROBOT='''<sdf version="1.9"><model name="turtlebot3_waffle">
<link name="camera_link"/><plugin name="drive" filename="drive"/></model>
</sdf>'''

def inputs(t):
    w=t/'source_world.sdf.xacro';w.write_text(WORLD)
    r=t/'source_waffle.sdf.xacro';r.write_text(ROBOT)
    mesh=t/'walk.dae';mesh.write_text('placeholder')
    return w,r,mesh

def test_human_mesh_is_attached_to_the_same_movable_contact_model(tmp_path):
    w,r,mesh=inputs(tmp_path)
    old_world=w.read_bytes()
    result=build_overlay(w,r,mesh,tmp_path/'out')
    tree=ET.parse(result['world']).getroot()
    model=tree.find(".//model[@name='axia_p2_g07_obstacle']")
    assert model is not None
    assert len(tree.findall('.//actor'))==0
    assert len(tree.findall(".//model[@name='axia_p2_g07_obstacle']"))==1
    link=model.find("./link[@name='obstacle_link']")
    human=link.find("./visual[@name='axia_d08_human_mesh']")
    assert human is not None
    assert human.findtext("./geometry/mesh/uri")==str(mesh.resolve())
    assert human.findtext("./geometry/mesh/scale")=='0.75 0.75 0.75'
    assert link.find("./visual[@name='obstacle_visual']") is None
    collision=link.find("./collision[@name='obstacle_collision']")
    assert collision.findtext('./geometry/cylinder/radius')=='0.07'
    assert collision.findtext('./geometry/cylinder/length')=='0.48'
    assert link.find("./sensor[@name='axia_contact']/contact/collision").text=='obstacle_collision'
    assert model.findtext('./pose')=='-0.58 -0.5 0.24 0 0 0'
    assert model.findtext('./static')=='true'
    assert result['human_visual_attached_to_physical_model'] is True
    assert result['visual_person_same_as_physical_obstacle'] is True
    assert result['separate_actor_removed'] is True
    assert result['human_visual_animated'] is False
    assert result['goal_sent'] is False
    assert result['certified_estop'] is False
    assert w.read_bytes()==old_world

def test_missing_contact_or_collision_fails_closed(tmp_path):
    w,r,mesh=inputs(tmp_path)
    w.write_text(WORLD.replace('<contact><collision>obstacle_collision</collision></contact>',''))
    with pytest.raises(ValueError,match='CONTACT'):
        build_overlay(w,r,mesh,tmp_path/'out')
    w.write_text(WORLD.replace('<radius>0.07</radius>','<radius>0.01</radius>'))
    with pytest.raises(ValueError,match='COLLISION_GEOMETRY'):
        build_overlay(w,r,mesh,tmp_path/'out')

def test_no_overlay_can_claim_collision_free_from_empty_contact_stream(tmp_path):
    w,r,mesh=inputs(tmp_path)
    result=build_overlay(w,r,mesh,tmp_path/'out')
    assert result['collision_ground_truth_verified'] is False
    assert result['physical_obstacle_static_gap_not_certified'] is True
