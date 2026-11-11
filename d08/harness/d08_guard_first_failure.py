"""Public, non-controller D08/G07 first-failure time classifier.

Inputs are sanitized Owner Observer host-monotonic *receipt* times. This is
NOT the private Guard policy or a synthetic ROS/Gazebo acceptance result.
"""
from math import isfinite


def classify_first_failure(*, cm_receipts, supervisor_receipts,
                           guard_latch_at, action_canceling_at,
                           action_canceled_at, scan_timeout_at,
                           set_pose_ack_at, cm_ttl_sec=.15,
                           supervisor_ttl_sec=.5):
    def gaps(times):
        if not isinstance(times,(list,tuple)) or len(times)<2 or not all(
            type(x) in (int,float) and isfinite(x) for x in times
        ) or not all(b>a for a,b in zip(times,times[1:])):
            raise ValueError('INVALID_HOST_RECEIPT_TIMES')
        return [b-a for a,b in zip(times,times[1:])]
    cg=gaps(cm_receipts)
    sg=gaps(supervisor_receipts)
    if not all(type(v) in (int,float) and isfinite(v) for v in
               (guard_latch_at,action_canceling_at,action_canceled_at,
                scan_timeout_at,set_pose_ack_at)):
        raise ValueError('INVALID_EVENT_TIME')
    if not (0<cm_ttl_sec<=supervisor_ttl_sec
            and guard_latch_at<=action_canceling_at<action_canceled_at
            <scan_timeout_at<set_pose_ack_at):
        raise ValueError('INVALID_EVENT_ORDER')
    # Owner Observer is an independent subscriber, not Guard's callback.
    # Therefore the CM gap proves exposure to the deadline, NOT the
    # exact channel responsible for the internal Guard latch.
    marker=('CM_OBSERVER_GAP_EXCEEDS_GUARD_BUDGET'
            if max(cg)>cm_ttl_sec else 'NO_CM_OBSERVER_DEADLINE_VIOLATION')
    return dict(
        status='FIELD_1C0V_GUARD_FIRST_FAILURE_REPRODUCED',
        first_latched_component='base_command_guard',
        observed_cm_gap_exceeds_budget=max(cg)>cm_ttl_sec,
        observed_supervisor_gap_exceeds_budget=max(sg)>supervisor_ttl_sec,
        observed_cm_max_gap_sec=round(max(cg),9),
        observed_supervisor_max_gap_sec=round(max(sg),9),
        suspected_channel='CM_OR_GUARD_SCHEDULING_UNRESOLVED',
        guard_internal_callback_ages_verified=False,
        marker=marker,
        cancel_before_scan_timeout=True,
        pose_ack_after_goal_cancel=True,
        normal_g07_accepted=False,
        certified_estop=False,
    )
