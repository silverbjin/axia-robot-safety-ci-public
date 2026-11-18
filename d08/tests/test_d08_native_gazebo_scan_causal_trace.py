"""RED: actual Gazebo Transport vs ROS Scan first-gap boundary, read-only.

This is a sanitized first-boundary regression, NOT proof that an earlier
WSL2/Gazebo source delay had a known root cause.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import compare_native_scan_first_gap

SCRIPT=Path(__file__).resolve().parents[1]/"harness/d08_gz_native_scan_probe.py"
BEFORE=48_501_000_000
AFTER=48_600_000_000
FIRST={
 "kind":"ROS_LASERSCAN_FIRST_RECEIVE_GAP",
 "sample_index":2,
 "receive_gap_sec":0.518394,
 "header_sim_gap_sec":0.099,
 "previous_host_monotonic_sec":1550.021209,
 "current_host_monotonic_sec":1550.539602,
 "previous_ros_stamp_ns":BEFORE,
 "current_ros_stamp_ns":AFTER,
 "limit_sec":0.5,
 "publisher_rmw_gap_measured":False,
}

def native(left,right):
    return [
      {"host_monotonic_sec":left,"source_stamp_ns":BEFORE},
      {"host_monotonic_sec":right,"source_stamp_ns":AFTER},
    ]

def test_readonly_native_trace_script_must_exist_and_not_publish():
    assert SCRIPT.is_file()
    s=SCRIPT.read_text()
    assert "gz.msgs10.laserscan_pb2" in s
    assert "gz.transport13" in s
    assert "node.subscribe(" in s
    assert "host_monotonic_sec" in s
    assert "source_stamp_ns" in s
    assert "node.advertise(" not in s
    assert "create_publisher" not in s
    assert "cmd_vel" not in s

def test_518ms_ros_gap_native_490ms_proves_only_after_native_candidate():
    v=compare_native_scan_first_gap(FIRST,native(1550.010,1550.500))
    assert v["native_pair_matched"] is True
    assert v["native_receive_gap_sec"]==0.49
    assert v["candidate"]=="AFTER_NATIVE_TRANSPORT_RX"
    assert v["cause"]=="UNDETERMINED"
    assert v["bridge_dds_send_measured"] is False
    assert v["first_scan_violation_retained"] is True

def test_native_515ms_gap_is_not_misreported_as_ros_only_executor():
    v=compare_native_scan_first_gap(FIRST,native(1550.010,1550.525))
    assert v["native_pair_matched"] is True
    assert v["native_receive_gap_sec"]==.515
    assert v["candidate"]=="AT_OR_BEFORE_NATIVE_TRANSPORT_RX"
    assert v["cause"]=="UNDETERMINED"
    assert v["first_scan_violation_retained"] is True

def test_no_source_stamp_pair_cannot_invent_cause():
    v=compare_native_scan_first_gap(FIRST,[
      {"host_monotonic_sec":1550.010,"source_stamp_ns":BEFORE},
      {"host_monotonic_sec":1550.500,"source_stamp_ns":AFTER+100_000_000},
    ])
    assert v["native_pair_matched"] is False
    assert v["cause"]=="UNDETERMINED"
    assert v["candidate"]=="NATIVE_SOURCE_STAMP_PAIR_UNAVAILABLE"
    assert v["native_receive_gap_sec"] is None

def test_no_ros_violation_is_not_native_safety_proof():
    v=compare_native_scan_first_gap(None,native(1550.010,1550.500))
    assert v["cause"]=="UNDETERMINED"
    assert v["native_pair_matched"] is False
    assert v["first_scan_violation_retained"] is False
