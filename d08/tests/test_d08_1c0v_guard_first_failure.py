"""RED: field 1C0vNYRe REAL CM timing violates 150ms Guard deadline.

Sanitized numeric *observer receipt* stamps only, no private teacher code.
The first test INTENTIONALLY expects healthy motion and must fail on the raw
event. The later GREEN revision will retain this field incident as negative
regression and independently require real successful workload evidence.
"""
from statistics import median

# Actual Owner actual_ros_events.jsonl observer host monotonic receipts.
CM_RX = [4223.803651443, 4223.982629269, 4224.101661995,
         4224.149982234, 4224.41772451, 4224.420519096]
SUP_RX = [4223.840394772,4223.869086103,4223.982896856,
          4223.986508782,4224.026814603,4224.101851029,
          4224.150155157,4224.230644758,4224.233579844,
          4224.343617945,4224.417878119,4224.434518745,
          4224.436851002]
CM_TTL_SEC = .15
SUP_TTL_SEC = .5
GUARD_LATCH_AT = 4224.418024
ACTION_EXECUTING_AT = 4221.539533
ACTION_CANCELING_AT = 4224.418425
ACTION_CANCELED_AT = 4224.435267
SUPERVISOR_SCAN_TIMEOUT_AT = 4225.329913
POSE_ACK_AT = 4226.381276

def gaps(values):
    return [b-a for a,b in zip(values,values[1:])]

def test_actual_field_normal_demo_failed_and_guard_was_first():
    # RED baseline was 1 failed, 32 passed:
    # FIELD_REPRODUCED_CM_GAP=0.267742s > GUARD_TTL=0.150s
    from d08.harness.d08_guard_first_failure import classify_first_failure
    out=classify_first_failure(
        cm_receipts=CM_RX,supervisor_receipts=SUP_RX,
        guard_latch_at=GUARD_LATCH_AT,action_canceling_at=ACTION_CANCELING_AT,
        action_canceled_at=ACTION_CANCELED_AT,
        scan_timeout_at=SUPERVISOR_SCAN_TIMEOUT_AT,set_pose_ack_at=POSE_ACK_AT,
        cm_ttl_sec=CM_TTL_SEC,supervisor_ttl_sec=SUP_TTL_SEC)
    print('FIELD_1C0V_GUARD_FIRST_FAILURE_REPRODUCED',out)
    assert round(out['observed_cm_max_gap_sec'],6)==.267742
    assert out['observed_cm_gap_exceeds_budget'] is True
    assert out['observed_supervisor_gap_exceeds_budget'] is False
    assert out['guard_internal_callback_ages_verified'] is False
    assert out['normal_g07_accepted'] is False
    assert out['cancel_before_scan_timeout'] is True
    assert out['certified_estop'] is False

def test_healthy_diagnostic_input_is_not_mislabeled_as_field_failure():
    from d08.harness.d08_guard_first_failure import classify_first_failure
    out=classify_first_failure(
        cm_receipts=[10.0,10.07,10.14,10.21],
        supervisor_receipts=[10.0,10.05,10.10,10.15],
        guard_latch_at=11.,action_canceling_at=11.01,
        action_canceled_at=11.02,scan_timeout_at=11.03,set_pose_ack_at=11.5)
    assert out['observed_cm_gap_exceeds_budget'] is False
    assert out['marker']=='NO_CM_OBSERVER_DEADLINE_VIOLATION'

def test_invalid_or_order_reversed_record_cannot_claim_success():
    import pytest
    from d08.harness.d08_guard_first_failure import classify_first_failure
    common=dict(cm_receipts=CM_RX,supervisor_receipts=SUP_RX,
        guard_latch_at=GUARD_LATCH_AT,action_canceling_at=ACTION_CANCELING_AT,
        action_canceled_at=ACTION_CANCELED_AT,
        scan_timeout_at=SUPERVISOR_SCAN_TIMEOUT_AT,set_pose_ack_at=POSE_ACK_AT)
    with pytest.raises(ValueError):
        classify_first_failure(**dict(common,cm_receipts=[10.0,9.9]))
    with pytest.raises(ValueError):
        classify_first_failure(**dict(common,scan_timeout_at=4224.3))

def test_field_order_is_guard_first_not_later_scan_timeout():
    assert ACTION_EXECUTING_AT < GUARD_LATCH_AT < ACTION_CANCELING_AT
    assert ACTION_CANCELING_AT < ACTION_CANCELED_AT < SUPERVISOR_SCAN_TIMEOUT_AT
    assert ACTION_CANCELED_AT < POSE_ACK_AT
