"""Sanitized D08 G07 Owner L3 time-domain failure replay.

Source: actual AxvMA7TI host-monotonic event order, sanitized for public CI.
No simulated ROS messages and NO runtime safety logic. A protective stop on
scan timeout is correct behavior; this module NEVER approves a moving Goal.
"""
import math


def _number(v):
    return type(v) in (int, float) and math.isfinite(v)


def estimated_wall_gap_sec(*, sim_rate_hz, rtf):
    """Physics estimate only: (1/sim_rate_hz)/RTF, NOT live wall-time proof."""
    if not (_number(sim_rate_hz) and sim_rate_hz>0
            and _number(rtf) and 0<rtf<=1.0):
        raise ValueError('INVALID_RATE_OR_RTF')
    return 1.0/(sim_rate_hz*rtf)


def meets_watchdog_budget(*, sim_rate_hz, rtf, watchdog_timeout_sec):
    if not _number(watchdog_timeout_sec) or watchdog_timeout_sec<=0:
        raise ValueError('INVALID_WATCHDOG')
    return estimated_wall_gap_sec(sim_rate_hz=sim_rate_hz,rtf=rtf)<watchdog_timeout_sec


def assess_owner_trace(trace):
    """Reproduce original failure; NEVER interpret cancel as formal G07 stop."""
    fail={'status':'INCOMPLETE_TRACE',
          'supervisor_protective_stop_expected':False,
          'goal_canceled_before_set_pose_ack':False,
          'normal_g07_stop_zone_verified':False,
          'certified_estop':False}
    if not isinstance(trace,dict):
        return fail
    scan=trace.get('scan_rx_mono')
    if not isinstance(scan,list) or len(scan)<2 or not all(_number(t) for t in scan):
        return fail
    gaps=[end-start for start,end in zip(scan,scan[1:])]
    if any(g<=0 for g in gaps):
        return fail
    timestamps=[trace.get(k) for k in
                ('action_executing_mono','slow_zone_mono','scan_timeout_mono',
                 'protective_stop_mono','canceling_mono','canceled_mono',
                 'gazebo_set_pose_ack_mono')]
    timeout=trace.get('watchdog_timeout_sec')
    if not all(_number(t) for t in timestamps) or not _number(timeout) or timeout<=0:
        return fail
    executing,slow,scan_timeout,stop,canceling,canceled,ack=timestamps
    ordered=executing<=slow<scan_timeout<=stop<=canceling<canceled<ack
    if not ordered:
        return dict(fail,status='UNEXPECTED_TRACE_ORDER')
    max_gap=max(gaps)
    if (max_gap<=timeout
            or trace.get('goal_result')!='MVP_GOAL_TERMINATED_DURING_STOP_MOVE'
            or trace.get('stop_reason')!='FAULT:scan_stale'):
        return dict(fail,status='NO_MATCHING_WATCHDOG_FAILURE')
    return {
      'status':'REPRODUCED_G07_SCAN_TIMEOUT_BEFORE_POSE_ACK',
      'observed_max_rx_gap_sec':round(max_gap,6),
      'watchdog_timeout_sec':timeout,
      'goal_canceled_before_set_pose_ack':True,
      'supervisor_protective_stop_expected':True,
      'normal_g07_stop_zone_verified':False,
      'certified_estop':False,
    }
