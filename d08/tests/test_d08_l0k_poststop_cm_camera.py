"""Owner l0KClvT6 RED: CM zero output expires after StopZone; D08 RGB crops head.

Sanitized facts extracted independently from actual rosbag2 CDR:
Supervisor /cmd_vel_supervised publishes 20 Hz 0 twists beyond t=6155.493,
but official CM /cmd_vel_pre_guard last output t=6103.801975. Guard
first UPSTREAM_STALE_AFTER_MOTION at t=6103.953508 (age .151668s > .15).
The actual screenshot displays legs only and bench 0.150, NOT a
person bounding box. Do not treat a safe Guard latch as an E-Stop failure.
"""
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_live_world import build_overlay

FIELD={
 'first_cm_stop_wall':1794386100.834358,
 'last_cm_zero_output_wall':1794386103.801975,
 'first_guard_latch_wall':1794386103.953508,
 'guard_cm_input_age_sec':.151668,
 'cm_ttl_sec':.15,
 'last_supervisor_zero_wall':1794386155.493,
 'last_nav_smoothed_wall':1794386105.469,
 'goal_canceling_wall':1794386103.960770,
 'goal_canceled_wall':1794386104.004629,
 'post_stop_dwell_sec':1.04402010999911,
 'original_debug_class':'bench',
 'original_debug_confidence':.150,
}

WORLD='''<sdf version="1.9"><world name="default">
<plugin name="gz::sim::systems::Contact" filename="gz-sim-contact-system"/>
<model name="axia_p2_g07_obstacle"><link name="obstacle_link">
<collision name="obstacle_collision"><geometry><cylinder>
<radius>0.07</radius><length>0.48</length></cylinder></geometry></collision>
<visual name="obstacle_visual"/><sensor name="axia_contact" type="contact">
<contact><collision>obstacle_collision</collision></contact></sensor>
</link></model></world></sdf>'''
ROBOT='<sdf version="1.9"><model name="turtlebot3_waffle"><link name="camera_link"/></model></sdf>'

def test_RED_owner_healthy_cm_zero_stream_5s_after_stop():
    x=FIELD
    assert x['post_stop_dwell_sec']>=1.0
    assert x['last_supervisor_zero_wall']>x['first_guard_latch_wall']+50
    assert x['guard_cm_input_age_sec']>x['cm_ttl_sec']
    assert x['first_guard_latch_wall']<x['goal_canceling_wall']<x['goal_canceled_wall']
    # Actual field gap, reproduces missing CI coverage (not ImportError).
    assert x['last_cm_zero_output_wall']-x['first_cm_stop_wall']>=5.0, (
        'L0KCLVT6_CM_ZERO_OUTPUT_STOPPED_BEFORE_5S_THEN_GUARD_TTL_151668US'
    )

def test_RED_d08_stopzone_camera_has_full_human_in_frame(tmp_path):
    w=tmp_path/'w.sdf.xacro';w.write_text(WORLD)
    r=tmp_path/'r.sdf.xacro';r.write_text(ROBOT)
    a=tmp_path/'walk.dae';a.write_text('reference')
    m=build_overlay(w,r,a,tmp_path/'out')
    camera=ET.parse(m['robot_sdf']).getroot().find(
        ".//sensor[@name='axia_d08_registered_rgbd']")
    pose=[float(x) for x in camera.findtext('pose').split()]
    look_up=-pose[4]
    hfov=float(camera.findtext('camera/horizontal_fov'))
    vfov=2*math.atan(math.tan(hfov/2)*.75)
    cam_z=.127+pose[2] # installed Waffle local camera .107 + spawn .02m
    # Renderer mesh top/bottom relative to same G07 physical model, NOT
    # a new actor; at actual STOP LaserScan ~.347m.
    head=m['human_geometry_max_z_m']*.75+.24+m['human_local_pose_z_m']
    foot=m['human_expected_foot_world_z_m']
    top_angle=math.atan((head-cam_z)/.35)
    bottom_angle=math.atan((foot-cam_z)/.35)
    assert look_up+vfov/2>=top_angle+.09, (
      'L0KCLVT6_YOLO_IMAGE_CROPS_HEAD_AT_REAL_STOP_DISTANCE')
    assert look_up-vfov/2<=bottom_angle-.09
    assert m['goal_sent'] is False and m['certified_estop'] is False
