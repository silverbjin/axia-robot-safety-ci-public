"""RED: RMW event-gap must carry a bracketed host time window.

An unlocated 700.302 ms RMW take gap might be startup/teardown or live
cycle_0000; never compare it to callback 505.365 ms by number alone.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from d08_rcl_trace_summary import parse_events

def test_scan_rmw_take_gap_has_clock_anchored_monotonic_window():
    anchor={"wall_ns":1_700_000_000_000_000_000,
            "monotonic_ns":1_000_000_000_000,
            "local_seconds_of_day":43200.0}
    lines=[
      '[12:00:00.000000] host ros2:rcl_subscription_init: { vpid = 456 }, { rmw_subscription_handle = 0xABC, subscription_handle = 0x123, topic_name = "/scan" }',
      '[12:00:00.100000] host ros2:rmw_take: { vpid = 456 }, { rmw_subscription_handle = 0xABC, source_timestamp = 100000000, taken = 1 }',
      '[12:00:00.800000] host ros2:rmw_take: { vpid = 456 }, { rmw_subscription_handle = 0xABC, source_timestamp = 200000000, taken = 1 }'
    ]
    x=parse_events(lines,clock_anchor=anchor)
    recv=next(s for s in x["scan_topic_streams"] if s["direction"]=="take")
    gap=recv["max_gap_window"]
    assert gap["gap_sec"]==.7
    assert abs(gap["start_host_monotonic_sec"]-1000.1)<.000001
    assert abs(gap["end_host_monotonic_sec"]-1000.8)<.000001
    assert gap["matched_same_laserscan_header_stamp"] is False
    assert x["rcl_publish_to_rcl_take_same_message_join_verified"] is False

def test_missing_clock_anchor_reports_unknown_not_invented_time():
    x=parse_events([
      '[12:00:00.000000] host ros2:rcl_subscription_init: { vpid = 2 }, { rmw_subscription_handle = 0xf, topic_name = "/scan" }',
      '[12:00:00.100000] host ros2:rmw_take: { vpid = 2 }, { rmw_subscription_handle = 0xf, source_timestamp = 123, taken = 1 }',
      '[12:00:00.900000] host ros2:rmw_take: { vpid = 2 }, { rmw_subscription_handle = 0xf, source_timestamp = 456, taken = 1 }'])
    gap=next(s for s in x["scan_topic_streams"] if s["direction"]=="take")["max_gap_window"]
    assert gap["start_host_monotonic_sec"] is None
    assert gap["end_host_monotonic_sec"] is None
