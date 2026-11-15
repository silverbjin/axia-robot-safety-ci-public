"""RED evidence replay: Owner EEUOfVQL had 50 /safety/scan samples 2.02-2.07m
despite successful set_pose ACK. Human mesh is rendered at z~1m while
GPU LiDAR scans the ankle/cylinder band. Preserve original collision but
give the LiDAR an unobtrusive leg-coloured VISUAL (not a second person).
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))
from d08_live_world import build_overlay

WORLD='''<sdf version="1.9"><world name="default">
<plugin name="gz::sim::systems::Contact" filename="gz-sim-contact-system"/>
<model name="axia_p2_g07_obstacle"><static>true</static>
<pose>-0.58 -0.5 0.24 0 0 0</pose><link name="obstacle_link">
<collision name="obstacle_collision"><geometry><cylinder>
<radius>0.07</radius><length>0.48</length></cylinder></geometry></collision>
<visual name="obstacle_visual"><geometry><cylinder>
<radius>0.07</radius><length>0.48</length></cylinder></geometry></visual>
<sensor name="axia_contact" type="contact"><contact>
<collision>obstacle_collision</collision></contact></sensor>
</link></model></world></sdf>'''
ROBOT='<sdf version="1.9"><model name="turtlebot3_waffle"><link name="camera_link"/></model></sdf>'

def test_grounded_human_visual_preserves_contact_collision_without_pole(tmp_path):
    w=tmp_path/'w';w.write_text(WORLD)
    r=tmp_path/'r';r.write_text(ROBOT)
    a=tmp_path/'walk.dae';a.write_bytes(b'asset placeholder')
    m=build_overlay(w,r,a,tmp_path/'output')
    root=ET.parse(m['world']).getroot()
    fixture=root.find(".//model[@name='axia_p2_g07_obstacle']")
    link=fixture.find("./link[@name='obstacle_link']")
    visuals={v.get('name'):v for v in link.findall('./visual')}
    # The mesh is now grounded (original feet floated 0.356m);
    # do not draw a separate black rendered cylinder inside the person.
    assert set(visuals)=={'axia_d08_human_mesh'}
    assert m['human_grounded_expected'] is True
    assert m['rendered_visual_count']==1
    assert m['gpu_lidar_leg_surface'] is False
    assert link.findtext("./collision[@name='obstacle_collision']/geometry/cylinder/radius")=='0.07'
    assert link.find("./sensor[@name='axia_contact']") is not None
    assert root.find('.//actor') is None
    assert m['human_visual_attached_to_physical_model'] is True
    assert m['collision_ground_truth_verified'] is False
    assert m['gpu_lidar_leg_surface'] is False
    # Must never recreate orange obstacle_visual or duplicate mannequin.
    assert 'obstacle_visual' not in visuals
    assert not any(k.startswith('axia_d08_human_leg_') for k in visuals)
