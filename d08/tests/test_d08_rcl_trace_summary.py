"""Bounded user-space trace analysis does NOT invent a sensor/RMW pass."""
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from d08_rcl_trace_summary import parse_events

def test_scan_publish_gap_vs_take_source_not_overclaimed():
    lines=[
      '[12:00:00.000000] host ros2:rcl_publisher_init: { vpid = 123, procname = "parameter_bridge" }, { publisher_handle = 0xABC, topic_name = "/scan" }',
      '[12:00:00.000000] host ros2:rcl_subscription_init: { vpid = 456, procname = "python3" }, { subscription_handle = 0xDEF, topic_name = "/scan" }',
      '[12:00:00.100000] host ros2:rcl_publish: { vpid = 123, procname = "parameter_bridge" }, { publisher_handle = 0xABC }',
      '[12:00:00.200000] host ros2:rcl_publish: { vpid = 123 }, { publisher_handle = 0xABC }',
      '[12:00:00.900000] host ros2:rcl_take: { vpid = 456 }, { message = 0x1 }',
      '[12:00:01.400000] host ros2:rcl_take: { vpid = 456 }, { subscription_handle = 0xDEF }'
    ]
    data=parse_events(lines)
    assert len(data['scan_topic_streams']) == 1
    pub=next(x for x in data['scan_topic_streams'] if x['direction']=='publish')
    assert pub['max_consecutive_rcl_event_gap_sec'] == 0.1
    assert not any(x['direction']=='take' for x in data['scan_topic_streams'])
    assert data['status']=='DIAGNOSTIC_ONLY_CAUSE_UNDETERMINED'
    assert data['rcl_publish_to_rcl_take_same_message_join_verified'] is False

def test_missing_init_or_no_stamps_is_not_fake_positive():
    data=parse_events(['ros2:rcl_publish: { vpid = 111 }, { publisher_handle = 0xa }'])
    assert not data['scan_topic_streams']
    assert data['publisher_rmw_cadence_measured'] is False
