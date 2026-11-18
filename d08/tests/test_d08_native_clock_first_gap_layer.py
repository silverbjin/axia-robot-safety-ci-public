"""RED: slow native Gazebo /clock vs LaserScan under a FIRST real ROS gap.

Synthetic samples here only test the math, not a simulated L2 success.
A historical 518ms ROS-only failure cannot prove native simulation slowdown.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import diagnose_native_clock_during_first_gap

FIRST={"kind":"ROS_LASERSCAN_FIRST_RECEIVE_GAP",
       "sample_index":2,"receive_gap_sec":.518394,
       "previous_host_monotonic_sec":1550.021209,
       "current_host_monotonic_sec":1550.539603,
       "previous_ros_stamp_ns":48_501_000_000,
       "current_ros_stamp_ns":48_600_000_000}

def scan_pair(gap):
    return [{"source_stamp_ns":48_501_000_000,"host_monotonic_sec":1550.010},
            {"source_stamp_ns":48_600_000_000,"host_monotonic_sec":1550.010+gap}]

def clock_trace(host_span,sim_span,segments=10):
    return [{"host_monotonic_sec":1550.010+host_span*i/segments,
             "sim_stamp_ns":int((48.501+sim_span*i/segments)*1e9)}
            for i in range(segments+1)]

def test_native_clock_slow_progress_is_source_layer_timing_evidence():
    v=diagnose_native_clock_during_first_gap(FIRST,scan_pair(.510),
                                            clock_trace(.510,.100))
    assert v["native_pair_matched"] is True
    assert v["clock_window_bracketed"] is True
    assert v["effective_rtf"] < .25
    assert v["timing_layer"]=="SIMULATION_PROGRESS_SLOW"
    assert v["root_resource_cause"]=="UNDETERMINED"
    assert v["first_scan_violation_retained"] is True

def test_normal_clock_with_slow_native_lidar_is_not_simulation_slow():
    v=diagnose_native_clock_during_first_gap(FIRST,scan_pair(.510),
                                            clock_trace(.510,.510))
    assert v["timing_layer"]=="NATIVE_SENSOR_OR_TRANSPORT_DELAY"
    assert v["root_resource_cause"]=="UNDETERMINED"

def test_normal_native_scan_with_518ms_ros_gap_is_after_native():
    v=diagnose_native_clock_during_first_gap(FIRST,scan_pair(.310),
                                            clock_trace(.310,.310))
    assert v["timing_layer"]=="AFTER_NATIVE_TRANSPORT_RX"
    assert v["root_resource_cause"]=="UNDETERMINED"

def test_missing_native_clock_cannot_claim_gazebo_slowdown():
    v=diagnose_native_clock_during_first_gap(FIRST,scan_pair(.510),[])
    assert v["timing_layer"]=="INSUFFICIENT_NATIVE_CLOCK"
    assert v["effective_rtf"] is None
    assert v["root_resource_cause"]=="UNDETERMINED"

def test_historical_gap_without_live_pair_is_unknown():
    v=diagnose_native_clock_during_first_gap(FIRST,[],clock_trace(.510,.1))
    assert v["timing_layer"]=="INSUFFICIENT_NATIVE_SCAN_PAIR"
    assert v["root_resource_cause"]=="UNDETERMINED"

def test_healthy_ros_observer_cannot_be_promoted_to_causal_proof():
    v=diagnose_native_clock_during_first_gap(None,scan_pair(.510),clock_trace(.510,.1))
    assert v["timing_layer"]=="NO_REAL_FIRST_ROS_GAP"
    assert v["root_resource_cause"]=="UNDETERMINED"
