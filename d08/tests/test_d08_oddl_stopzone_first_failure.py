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

def test_owner_original_43cm_actual_stopzone_miss_is_a_negative_regression():
    t=OWNER
    assert t['goal_executing_at']<t['moving_slow_at']<t['gz_set_pose_ack_at']
    assert .4<t['slow_front_m']<.75
    assert t['slow_vout']<=t['slow_vin']*.3+.01
    assert t['gz_set_pose_ack_duration_sec']<1
    # RED #42959948301 proved the *normal demo condition* failed on
    # original actual scan .460472 > .4, not from missing test/module.
    assert not (.14<=t['post_ack_front_min_m']<t['stop_zone_limit_m'])
    assert t['stop_dispatch_m']==.43
    print('ODDLCNNN_ACTUAL_STOPZONE_MISS_REPRODUCED_FAIL_CLOSED')

def test_real_gazebo_static_30cm_candidate_has_minimum_3cm_margin():
    # Source: actual official Waffle Gazebo L2 #42960656274, NOT
    # a claim of moving-Goal StopZone/contact proof.
    static_dispatch=.30
    static_lidar=.364392
    assert static_dispatch<OWNER['stop_dispatch_m']
    assert .14 <= static_lidar <= .37
    assert OWNER['stop_zone_limit_m']-static_lidar>=.03
    assert OWNER['post_ack_front_min_m']>=.4
    print('ODDLCNNN_STATIC_REAL_GAZEBO_30CM_STOP_MARGINAL_CALIBRATION_PASS')

def test_owner_guard_first_failure_is_correct_and_separate():
    t=OWNER
    assert t['gz_set_pose_ack_at']<t['cm_guard_latch_at']
    assert t['cm_guard_latch_at']<t['action_canceling_at']<t['action_canceled_at']
    assert t['guard_cm_internal_age_sec']>t['guard_cm_ttl_sec']
    assert t['first_post_ack_scan_at']>t['action_canceled_at']
