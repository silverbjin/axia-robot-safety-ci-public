"""Owner jtZ/3VAB person=0 and 86 false TV detections:
real Waffle camera image clipped head/upper torso at x=-1.2 scene fixture.
Use the exact rendered human geometry and real Waffle camera pose; never
relax D05 RGB-D 50ms or change original robot camera/safety components.
"""
import math
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_live_world import build_overlay

WORLD='''<sdf version="1.9"><world name="default">
<plugin name="gz::sim::systems::Contact" filename="gz-sim-contact-system"/>
<model name="axia_p2_g07_obstacle"><pose>-1.2 -0.5 0.24 0 0 0</pose>
<static>true</static><link name="obstacle_link">
<collision name="obstacle_collision"><geometry>
<cylinder><radius>0.07</radius><length>0.48</length></cylinder></geometry></collision>
<visual name="obstacle_visual"><geometry>
<cylinder><radius>0.07</radius><length>0.48</length></cylinder></geometry></visual>
<sensor name="axia_contact" type="contact"><contact>
<collision>obstacle_collision</collision></contact></sensor></link></model></world></sdf>'''
ROBOT='<sdf version="1.9"><model name="turtlebot3_waffle"><link name="camera_link"/></model></sdf>'

def test_real_human_head_and_feet_fit_supplemental_rgbd_camera(tmp_path):
    w=tmp_path/'world.xacro';w.write_text(WORLD)
    r=tmp_path/'robot.xacro';r.write_text(ROBOT)
    a=tmp_path/'walk.dae';a.write_text('fixture')
    m=build_overlay(w,r,a,tmp_path/'out')
    sensor=ET.parse(m['robot_sdf']).find(".//sensor[@name='axia_d08_registered_rgbd']")
    pose=[float(v) for v in sensor.findtext('pose').split()]
    # SDF positive-Y pitch rotates +X toward -Z: negative pitch looks UP.
    look_up=-pose[4]
    hfov=float(sensor.findtext('camera/horizontal_fov'))
    vfov=2*math.atan(math.tan(hfov/2)*480/640)
    # Official Waffle camera_link local height 0.107m; robot spawned at
    # -2,-0.5,+0.02m; fixture starts -1.2,-0.5; range ≈0.8m.
    cam_z=0.107+0.02+pose[2]
    h=m['human_geometry_max_z_m']*.75 +0.24+m['human_local_pose_z_m']
    foot=m['human_expected_foot_world_z_m']
    distance=.8
    head=math.atan((h-cam_z)/distance)
    feet=math.atan((foot-cam_z)/distance)
    assert look_up + vfov/2 >= head+0.025, (look_up,vfov,head)
    assert look_up - vfov/2 <= feet-0.025, (look_up,vfov,feet)
    # Supplementary D08 RGBD only. Native Waffle lidar/safety unchanged.
    assert 1.35<=hfov<=2.0
    assert 0.20<=look_up<=0.55
    assert not m['robot_drive_model_modified']
    assert m['goal_sent'] is False
