"""1XZYehm8: actual Owner Guard-internal TTL evidence, RED on healthy demo.

Only sanitized numeric host-monotonic event timestamps and published status
values appear here, never teacher code or the Owner private archive.

RED intentionally asserts a healthy moving Goal; field evidence proves it
FALSE. GREEN keeps the failure as a negative regression while checking the
specific minimum D08 GPU workload reduction.
"""
from d08.harness.d08_guard_first_failure import classify_first_failure

ACTUAL={
    'action_executing_at':12118.445134276,
    'slowzone_at':12119.166298203,
    'guard_latch_at':12121.692281118,
    'cm_internal_age_sec':.159812,
    'supervisor_internal_age_sec':.095337,
    'cm_ttl_sec':.15,
    'supervisor_ttl_sec':.5,
    'action_canceling_at':12121.692668383,
    'action_canceled_at':12121.781858727,
    'supervisor_scan_timeout_at':12122.32542925,
    'set_pose_ack_at':12123.213028109,
    'set_pose_ack_duration_sec':4.039747093000187,
    'observer_cm_gap_sec':.24721934999979567,
    'observer_scan_gap_sec':.7280004220010596,
}

def test_owner_1xzy_actual_guard_first_protective_latch_is_expected_fail_closed():
    e=ACTUAL
    print('FIELD_1XZY_GUARD_CM_STEADY_TIMEOUT_REPRODUCED')
    assert e['action_executing_at']<e['slowzone_at']<e['guard_latch_at']
    assert e['cm_internal_age_sec'] > e['cm_ttl_sec']
    assert e['supervisor_internal_age_sec'] < e['supervisor_ttl_sec']
    assert e['guard_latch_at']<e['action_canceling_at']<e['action_canceled_at']
    assert e['action_canceled_at']<e['supervisor_scan_timeout_at']<e['set_pose_ack_at']
    assert e['set_pose_ack_duration_sec']>4.0
    assert e['observer_cm_gap_sec']>.15
    assert e['observer_scan_gap_sec']>.5
    # This is a failed *normal* G07 demo but CORRECT fail-closed safety.
    assert e['cm_internal_age_sec']-e['cm_ttl_sec']>.009
    assert e['action_canceled_at']<e['set_pose_ack_at']

def test_d08_overlay_disables_second_unused_depth_renderer_before_owner_goal(tmp_path):
    from pathlib import Path
    import xml.etree.ElementTree as ET
    from d08.harness.d08_live_world import build_overlay
    world='''<sdf version="1.9"><world name="default">
    <plugin name="gz::sim::systems::Contact" filename="gz-sim-contact-system"/>
    <model name="axia_p2_g07_obstacle"><link name="obstacle_link">
    <collision name="obstacle_collision"><geometry><cylinder>
    <radius>0.07</radius><length>0.48</length></cylinder></geometry></collision>
    <visual name="obstacle_visual"/><sensor name="axia_contact" type="contact">
    <contact><collision>obstacle_collision</collision></contact></sensor>
    </link></model></world></sdf>'''
    robot='''<sdf version="1.9"><model name="turtlebot3_waffle">
    <link name="camera_link"><sensor name="intel_realsense_r200_depth" type="depth">
    <always_on>1</always_on><update_rate>5</update_rate></sensor></link>
    <link name="base_scan"><sensor name="hls_lfcd_lds" type="gpu_lidar">
    <visualize>true</visualize><update_rate>5</update_rate>
    </sensor></link></model></sdf>'''
    w=tmp_path/'w.sdf.xacro';w.write_text(world)
    r=tmp_path/'r.sdf.xacro';r.write_text(robot)
    a=tmp_path/'walk.dae';a.write_text('fixture')
    m=build_overlay(w,r,a,tmp_path/'overlay')
    original=ET.parse(r).getroot()
    actual=ET.parse(m['robot_sdf']).getroot()
    assert original.find(".//sensor[@name='intel_realsense_r200_depth']") is not None
    assert actual.find(".//sensor[@name='intel_realsense_r200_depth']") is None
    assert m['d08_unused_upstream_depth_sensor_removed'] is True
    assert len(actual.findall(".//sensor[@type='rgbd_camera']"))==1
    assert actual.find(".//sensor[@name='axia_d08_registered_rgbd']") is not None
    assert actual.find(".//sensor[@name='hls_lfcd_lds']/update_rate").text=='10'
    assert m['d08_scan_watchdog_sec_unchanged']==.5
    assert m['goal_sent'] is False and m['certified_estop'] is False
