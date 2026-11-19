"""RED: independent Python process must resolve ROS vs same-process GIL gap.

Uses literal sanitized first Owner 518.394ms boundary and controlled
timestamps as an L0 logic contract, NOT actual Gazebo L2 evidence.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import compare_isolated_ros_first_gap

PROBE=Path(__file__).resolve().parents[1]/"harness/d08_ros_isolated_scan_probe.py"
FIRST={"receive_gap_sec":.518394,
       "previous_host_monotonic_sec":1550.021209,
       "current_host_monotonic_sec":1550.539603,
       "previous_ros_stamp_ns":48_501_000_000,
       "current_ros_stamp_ns":48_600_000_000}

def independent_gap(dt):
    return [{"host_monotonic_sec":1550.000, "source_stamp_ns":48_501_000_000},
            {"host_monotonic_sec":1550.000+dt,
             "source_stamp_ns":48_600_000_000}]

def native_gap(dt):
    return [{"host_monotonic_sec":1549.999,"source_stamp_ns":48_501_000_000},
            {"host_monotonic_sec":1549.999+dt,
             "source_stamp_ns":48_600_000_000}]

def test_isolated_probe_must_be_separate_readonly_python_process():
    assert PROBE.is_file(),"D08_ISOLATED_ROS_SCAN_PROBE_MISSING_RED"
    s=PROBE.read_text()
    assert "rclpy" in s and "qos_profile_sensor_data" in s
    assert "time.monotonic()" in s
    assert "LaserScan" in s and "/scan" in s
    assert "create_publisher(" not in s
    assert "cmd_vel" not in s
    assert "--out" in s

def test_only_parent_pauses_while_isolated_ros_and_native_continue():
    v=compare_isolated_ros_first_gap(FIRST,independent_gap(.190),native_gap(.180))
    assert v["candidate"]=="LOCAL_ROS_PROCESS_DISPATCH_OR_GIL"
    assert v["cause"]=="UNDETERMINED"
    assert v["first_scan_violation_retained"] is True
    assert v["isolation_proven"] is True

def test_both_ros_processes_pause_native_continues():
    v=compare_isolated_ros_first_gap(FIRST,independent_gap(.512),native_gap(.190))
    assert v["candidate"]=="ROS_BRIDGE_DDS_OR_HOST_SCHEDULER"
    assert v["cause"]=="UNDETERMINED"

def test_no_timestamp_match_must_hold_unknown():
    v=compare_isolated_ros_first_gap(FIRST,
       [{"host_monotonic_sec":1550.0,"source_stamp_ns":47_501_000_000},
        {"host_monotonic_sec":1550.19,"source_stamp_ns":47_600_000_000}],
       native_gap(.190))
    assert v["candidate"]=="ROS_PROCESS_TIMESTAMP_PAIR_MISSING"
    assert v["isolation_proven"] is False

def test_no_real_first_gap_never_reports_root():
    v=compare_isolated_ros_first_gap(None,independent_gap(.512),native_gap(.190))
    assert v["cause"]=="UNDETERMINED"
    assert v["first_scan_violation_retained"] is False
