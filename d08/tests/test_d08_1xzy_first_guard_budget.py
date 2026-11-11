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

def test_red_actual_normal_owner_d08_goal_requires_fresh_cm_internal_input():
    e=ACTUAL
    print('FIELD_1XZY_GUARD_CM_AGE',e['cm_internal_age_sec'],
          'CM_TTL',e['cm_ttl_sec'],'SUPERVISOR_AGE',
          e['supervisor_internal_age_sec'])
    assert e['action_executing_at']<e['slowzone_at']<e['guard_latch_at']
    assert e['supervisor_internal_age_sec']<e['supervisor_ttl_sec']
    # Real field violation: 159.812ms > 150ms; RED must fail here.
    assert e['cm_internal_age_sec'] <= e['cm_ttl_sec'], (
        'FIELD_1XZY_GUARD_CM_EXPIRED_159812US_GT_150000US')
