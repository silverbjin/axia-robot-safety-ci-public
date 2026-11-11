"""AxvMA7TI owner raw evidence replay (sanitized numerical timestamps ONLY).

The original archive remains private. This test reproduces the REAL failure
order and treats protective-stop/cancel as expected safety behavior, NOT a bug.
"""
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[2]
MODULE=ROOT/'d08/harness/d08_owner_l3_timing.py'
spec=importlib.util.spec_from_file_location('axia_d08_timing',MODULE)
timing=importlib.util.module_from_spec(spec)
spec.loader.exec_module(timing)

# Source: owner AxvMA7TI; /safety/scan observer host monotonic timestamps.
# No ROS messages, private path, identity or instructor code stored publicly.
RAW={
    'source':'AxvMA7TI_sanitized_evidence',
    'scan_rx_mono':[1083.655199,1084.185146,1084.714615],
    'scan_sim_period_sec':0.201,
    'configured_lidar_update_hz':5.0,
    'watchdog_timeout_sec':0.5,
    'slow_zone_mono':1082.344330,
    'action_executing_mono':1081.8302,
    'scan_timeout_mono':1084.184800,
    'protective_stop_mono':1084.184800,
    'canceling_mono':1084.1854,
    'canceled_mono':1084.2463,
    'gazebo_set_pose_ack_mono':1085.964505,
    'goal_result':'MVP_GOAL_TERMINATED_DURING_STOP_MOVE',
    'stop_reason':'FAULT:scan_stale',
}

def test_red_existing_owner_l3_fails_with_actual_wallclock_scan_gap():
    out=timing.assess_owner_trace(RAW)
    assert out['status']=='REPRODUCED_G07_SCAN_TIMEOUT_BEFORE_POSE_ACK'
    assert out['observed_max_rx_gap_sec']>RAW['watchdog_timeout_sec']
    assert out['goal_canceled_before_set_pose_ack'] is True
    assert out['supervisor_protective_stop_expected'] is True
    assert out['normal_g07_stop_zone_verified'] is False
    assert out['certified_estop'] is False

def test_stop_must_still_occur_on_injected_scan_loss():
    damaged=dict(RAW,scan_rx_mono=[100.0,100.55,100.7],
                 action_executing_mono=99,slow_zone_mono=100.0,
                 scan_timeout_mono=100.5,protective_stop_mono=100.5,
                 canceling_mono=100.51,canceled_mono=100.53,
                 gazebo_set_pose_ack_mono=101.0)
    out=timing.assess_owner_trace(damaged)
    assert out['status']=='REPRODUCED_G07_SCAN_TIMEOUT_BEFORE_POSE_ACK'
    assert out['supervisor_protective_stop_expected'] is True

def test_d08_only_rate_margin_without_relaxing_safety_watchdog():
    from d08.harness.d08_live_world import GPU_LIDAR_SIM_RATE_HZ
    assert GPU_LIDAR_SIM_RATE_HZ==10
    # Measured interval 0.201 simulation sec / 0.552 wall sec, RTF ~0.364.
    measured_rtf=.201/.552
    old=timing.estimated_wall_gap_sec(sim_rate_hz=5,rtf=measured_rtf)
    new=timing.estimated_wall_gap_sec(sim_rate_hz=GPU_LIDAR_SIM_RATE_HZ,
                                       rtf=measured_rtf)
    assert old>.5
    assert new<.5
    assert timing.meets_watchdog_budget(sim_rate_hz=5,rtf=measured_rtf,
                                          watchdog_timeout_sec=.5) is False
    assert timing.meets_watchdog_budget(sim_rate_hz=10,rtf=measured_rtf,
                                          watchdog_timeout_sec=.5) is True
    # This is only a mathematical estimate, not a claim that WSL2 is fast enough.

def test_missing_or_out_of_order_trace_is_not_claimed_as_safety_pass():
    out=timing.assess_owner_trace(dict(RAW,scan_rx_mono=[1083.65]))
    assert out['status']=='INCOMPLETE_TRACE'
    out=timing.assess_owner_trace(dict(RAW,gazebo_set_pose_ack_mono=1084.15))
    assert out['status']=='UNEXPECTED_TRACE_ORDER'
