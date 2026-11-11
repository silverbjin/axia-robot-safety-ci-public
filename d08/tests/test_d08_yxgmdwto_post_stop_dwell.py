"""Owner YXgmdWTo: original *real* post-STOP odometry evidence.

Sanitized recorded host-monotonic stamps/velocity only. The old Owner
recent_stop_dwell() allowed |odom vx|<.03 even though the robot was
still moving after the Collision Monitor stop command, and it counted
pre-Goal stationary time toward a reported 9.2700864s dwell.

This source deliberately REDs on the actual post-stop duration. Never
claim that an upstream CM Twist zero proves the robot odom stopped.
"""
FIELD={
 'source_sha':'52b00334ed5f6d5b6a955a68cdcbad995ad8b36e',
 'owner_status':'L3_NUMERICAL_CANDIDATES_RAW_REVIEW_HOLD',
 'goal_sent_t':10937.2319743,
 'moving_slowzone_t':10937.612281889,
 'stop_output_observed_t':10938.437205711,
 'last_odom_t':10938.443544041,
 'last_odom_vx_mps':0.027341802281957067,
 'claimed_dwell_sec':9.270086399999855,
 'stop_cm_vout_mps':0.0,
 'dwell_required_sec':1.0,
 'certified_estop':False,
 'collision_ground_truth_verified':False,
}

def test_real_owner_claim_must_be_preserved_as_false_dwell_negative_regression():
    x=FIELD
    assert x['goal_sent_t'] < x['moving_slowzone_t'] < x['stop_output_observed_t']
    assert x['stop_cm_vout_mps']==0.0
    assert x['claimed_dwell_sec']>9.0
    assert x['last_odom_vx_mps']>0.02
    # Actual public RED #42985521116 failed on exactly this difference
    # (1 failed, 46 passed). A zero CM output is NOT stationary odometry.
    assert 0 < x['last_odom_t']-x['stop_output_observed_t'] < .01
    assert not (x['last_odom_t']-x['stop_output_observed_t']
                >= x['dwell_required_sec'])
    print('YXGMDWTO_FALSE_9_270S_ODOM_DWELL_REPRODUCED_NOT_ACCEPTED')

def test_actual_owner_is_not_formally_accepted():
    x=FIELD
    assert x['owner_status']=='L3_NUMERICAL_CANDIDATES_RAW_REVIEW_HOLD'
    assert x['certified_estop'] is False
    assert x['collision_ground_truth_verified'] is False
