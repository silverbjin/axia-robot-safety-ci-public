"""RED: join RMW /scan subscription handle to the actual ROS node name.

The previously observed 543.278ms RMW source→take pair belongs to a PID,
not yet a verified named D08 read-only observer or CM. Do NOT infer safety TTL.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from d08_rcl_trace_summary import parse_events

def test_longest_rmw_source_pair_names_actual_receiver_node():
    rows=[
        '[12:00:00.000000] host ros2:rcl_node_init: { vpid = 14 }, { node_handle = 0x100, rmw_handle = 0x200, node_name = "axia_d08_readonly_observer", namespace = "/" }',
        '[12:00:00.000010] host ros2:rcl_publisher_init: { vpid = 12 }, { publisher_handle = 0xa, rmw_publisher_handle = 0xB, topic_name = "/scan" }',
        '[12:00:00.000020] host ros2:rcl_subscription_init: { vpid = 14 }, { subscription_handle = 0xc, node_handle = 0x100, rmw_subscription_handle = 0xD, topic_name = "/scan" }',
        '[12:00:00.100000] host ros2:rmw_publish: { vpid = 12 }, { rmw_publisher_handle = 0xB, timestamp = 1710000000000000100 }',
        '[12:00:00.450000] host ros2:rmw_take: { vpid = 14 }, { rmw_subscription_handle = 0xD, source_timestamp = 1710000000000000100, taken = 1 }',
        '[12:00:00.500000] host ros2:rmw_publish: { vpid = 12 }, { rmw_publisher_handle = 0xB, timestamp = 1710000000000000200 }',
        '[12:00:01.050000] host ros2:rmw_take: { vpid = 14 }, { rmw_subscription_handle = 0xD, source_timestamp = 1710000000000000200, taken = 1 }']
    r=parse_events(rows)
    worst=r["rmw_scan_source_stamp_join"]["max_pair"]
    assert worst["receiver_node"]=="axia_d08_readonly_observer"
    assert worst["receiver_subscription_rmw_handle"]=="0xD"
    assert worst["receiver_node_identified"] is True
    assert r["rmw_scan_source_stamp_join"]["max_publish_to_take_sec"]==.55

def test_missing_node_init_keeps_receiver_identity_unverified():
    rows=[
        '[12:00:00.000000] host ros2:rcl_subscription_init: { vpid = 4 }, { subscription_handle = 0xc, node_handle = 0xABC, rmw_subscription_handle = 0xD, topic_name = "/scan" }',
        '[12:00:00.000000] host ros2:rcl_publisher_init: { vpid = 2 }, { publisher_handle = 0xa, rmw_publisher_handle = 0xB, topic_name = "/scan" }',
        '[12:00:00.100000] host ros2:rmw_publish: { vpid = 2 }, { rmw_publisher_handle = 0xB, timestamp = 1710000000000000100 }',
        '[12:00:00.200000] host ros2:rmw_take: { vpid = 4 }, { rmw_subscription_handle = 0xD, source_timestamp = 1710000000000000100, taken = 1 }']
    r=parse_events(rows)
    assert r["rmw_scan_source_stamp_join"]["max_pair"]["receiver_node"] is None
    assert r["rmw_scan_source_stamp_join"]["max_pair"]["receiver_node_identified"] is False

def test_real_trace_enables_official_rcl_node_init_without_new_ros_node():
    src=(Path(__file__).resolve().parents[1]/"scripts/d08_ros_trace_live_ci.sh").read_text()
    assert "ros2:rcl_node_init" in src
    assert "500ms/CM/Guard criterion UNCHANGED" in src
