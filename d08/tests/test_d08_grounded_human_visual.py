"""RED (Owner jlZsbcmp): human feet float 35.56 cm above ground and
dark render cylinder overlaps the body, YOLO sees TV 86 not PERSON.

No new safety logic. Test the same model visual and original collision.
The Z bounds are from pinned SHA256 D04 public walk.dae, inspected in CI.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_live_world import build_overlay

ORIGINAL='''<sdf version="1.9"><world name="default">
<plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>
<model name="axia_p2_g07_obstacle">
<pose>-0.58 -0.5 0.24 0 0 0</pose><static>true</static>
<link name="obstacle_link">
<collision name="obstacle_collision"><geometry>
<cylinder><radius>0.07</radius><length>0.48</length></cylinder>
</geometry></collision>
<visual name="obstacle_visual"><geometry>
<cylinder><radius>0.07</radius><length>0.48</length></cylinder>
</geometry></visual>
<sensor name="axia_contact" type="contact"><contact>
<collision>obstacle_collision</collision></contact></sensor>
</link></model></world></sdf>'''
ROBOT='<sdf version="1.9"><model name="turtlebot3_waffle"><link name="camera_link"/></model></sdf>'
DAE_MIN_Z=-0.859141
DAE_MAX_Z=0.856892
SCALE=0.75

def test_single_grounded_person_no_visible_support_pole(tmp_path):
    w=tmp_path/'w.xacro';w.write_text(ORIGINAL)
    r=tmp_path/'r.xacro';r.write_text(ROBOT)
    m=tmp_path/'walk.dae';m.write_text('fixture')
    out=build_overlay(w,r,m,tmp_path/'out')
    root=ET.parse(out['world']).getroot()
    model=root.find(".//model[@name='axia_p2_g07_obstacle']")
    assert model is not None
    link=model.find("./link[@name='obstacle_link']")
    visuals=link.findall('./visual')
    assert [v.get('name') for v in visuals]==['axia_d08_human_mesh']
    visual=visuals[0]
    pose=[float(v) for v in visual.findtext('pose').split()]
    world_z=float(model.findtext('pose').split()[2])
    scale=[float(v) for v in visual.findtext('./geometry/mesh/scale').split()]
    foot_world_z=world_z+pose[2]+scale[2]*DAE_MIN_Z
    head_world_z=world_z+pose[2]+scale[2]*DAE_MAX_Z
    # Owner CqYxbyzi: visual-only toe clearance calibration (not physics).
    assert .04 <= foot_world_z <= .08,foot_world_z
    assert out['human_render_tune_lift_m'] == .06
    assert out['human_foot_contact_gui_verified'] is False
    assert 1.20<head_world_z<1.40,head_world_z
    assert abs(pose[0])<.001 and abs(pose[1])<.001
    assert len(root.findall('.//actor'))==0
    assert link.findtext("./collision[@name='obstacle_collision']/geometry/cylinder/radius")=='0.07'
    assert link.findtext("./collision[@name='obstacle_collision']/geometry/cylinder/length")=='0.48'
    assert link.find("./sensor[@name='axia_contact']") is not None
    assert out['human_grounded_expected'] is True
    assert out['gpu_lidar_leg_surface'] is False
    assert out['human_visual_count']==1
    assert out['rendered_visual_count']==1
    assert out['collision_ground_truth_verified'] is False
    assert out['goal_sent'] is False
