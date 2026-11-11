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

def test_normal_owner_demo_must_keep_cm_delivery_within_guard_ttl_RED():
    max_gap=max(gaps(CM_RX))
    print('FIELD_1C0V_CM_WALL_GAP_SEC',round(max_gap,6),
          'GUARD_CM_TTL_SEC',CM_TTL_SEC,
          'OWNER_FIRST_BLOCK',GUARD_LATCH_AT)
    assert max(gaps(SUP_RX)) < SUP_TTL_SEC
    # This MUST FAIL on actual field evidence (not ImportError):
    assert max_gap < CM_TTL_SEC, (
        f'FIELD_REPRODUCED_CM_GAP={max_gap:.6f}s > GUARD_TTL={CM_TTL_SEC:.3f}s')

def test_field_order_is_guard_first_not_later_scan_timeout():
    assert ACTION_EXECUTING_AT < GUARD_LATCH_AT < ACTION_CANCELING_AT
    assert ACTION_CANCELING_AT < ACTION_CANCELED_AT < SUPERVISOR_SCAN_TIMEOUT_AT
    assert ACTION_CANCELED_AT < POSE_ACK_AT
