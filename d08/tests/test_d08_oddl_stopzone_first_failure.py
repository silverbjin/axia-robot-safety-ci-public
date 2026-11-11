"""ODDlcnNN actual Owner G07 StopZone failure (sanitized raw timing only).

The real ACK is not proof of a STOP: LiDAR post-ACK min=.4604721665m.
Separate later 150ms Guard fail-closed from independent geometry miss.
No instructor solution or private ROS log exposed in public repository.
"""
OWNER={
 'goal_executing_at':236.681158959,
 'moving_slow_at':237.179114232,
 'gz_set_pose_ack_at':237.929285588,
 'gz_set_pose_ack_duration_sec':.741770583999994,
 'first_post_ack_scan_at':238.073457,
 'cm_guard_latch_at':237.969951,
 'guard_cm_internal_age_sec':.184845,
 'guard_cm_ttl_sec':.15,
 'action_canceling_at':237.970833782,
 'action_canceled_at':237.993966401,
 'stop_dispatch_m':.43,
 'post_ack_front_min_m':.4604721665382385,
 'stop_zone_limit_m':.4,
 'slow_front_m':.5564350485801697,
 'slow_vin':.0868561640381813,
 'slow_vout':.02543463259935379,
}

def test_red_owner_actual_stop_zone_threshold_not_reached():
    t=OWNER
    assert t['goal_executing_at']<t['moving_slow_at']<t['gz_set_pose_ack_at']
    assert .4<t['slow_front_m']<.75
    assert t['slow_vout']<=t['slow_vin']*.3+.01
    assert t['gz_set_pose_ack_duration_sec']<1
    # Intentionally fails from the ACTUAL field scan, not a synthetic substitute:
    assert .14<=t['post_ack_front_min_m']<t['stop_zone_limit_m'], (
        'ODDLCNNN_ACTUAL_LIDAR_STOPZONE_NOT_REACHED_FRONT_0_460472_GT_0_4'
    )

def test_owner_guard_first_failure_is_correct_and_separate():
    t=OWNER
    assert t['gz_set_pose_ack_at']<t['cm_guard_latch_at']
    assert t['cm_guard_latch_at']<t['action_canceling_at']<t['action_canceled_at']
    assert t['guard_cm_internal_age_sec']>t['guard_cm_ttl_sec']
    assert t['first_post_ack_scan_at']>t['action_canceled_at']
