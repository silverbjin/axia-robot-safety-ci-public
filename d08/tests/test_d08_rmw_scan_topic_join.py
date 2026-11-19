"""RED: official Jazzy rmw_take carries rmw_subscription_handle; rcl_take does not.

Original actual L2 #44453501145 emitted 1,406,590 generic rcl_take
events but zero topic-joined /scan take streams; do not claim no delay.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from d08_rcl_trace_summary import parse_events

def test_rmw_take_joins_subscription_init_via_rmw_handle():
    lines=[
        '[12:00:00.000000] host ros2:rcl_subscription_init: { vpid = 456, procname = "python3" }, { subscription_handle = 0xa, rmw_subscription_handle = 0xBEF, topic_name = "/scan" }',
        '[12:00:00.100000] host ros2:rmw_take: { vpid = 456 }, { rmw_subscription_handle = 0xBEF, message = 0x1, source_timestamp = 100000000, taken = 1 }',
        '[12:00:00.200000] host ros2:rmw_take: { vpid = 456 }, { rmw_subscription_handle = 0xBEF, message = 0x2, source_timestamp = 200000000, taken = 1 }',
        '[12:00:00.900000] host ros2:rmw_take: { vpid = 456 }, { rmw_subscription_handle = 0xBEF, message = 0x3, source_timestamp = 300000000, taken = 1 }',
        '[12:00:00.950000] host ros2:rmw_take: { vpid = 456 }, { rmw_subscription_handle = 0xBEF, message = 0x3, source_timestamp = 300000000, taken = 0 }'
    ]
    r=parse_events(lines)
    take=[x for x in r["scan_topic_streams"] if x["direction"]=="take"]
    assert len(take)==1, r
    assert take[0]["count"]==3, r
    assert take[0]["max_consecutive_rcl_event_gap_sec"]==.7
    assert r["rcl_publish_to_rcl_take_same_message_join_verified"] is False

def test_rmw_publish_joins_publisher_init_via_rmw_handle():
    lines=[
        '[12:00:00.000000] host ros2:rcl_publisher_init: { vpid = 123, procname = "parameter_bridg" }, { publisher_handle = 0xAAB, rmw_publisher_handle = 0xABC, topic_name = "/scan" }',
        '[12:00:00.100000] host ros2:rmw_publish: { vpid = 123 }, { rmw_publisher_handle = 0xABC, message = 0x1, timestamp = 100000000 }',
        '[12:00:00.200000] host ros2:rmw_publish: { vpid = 123 }, { rmw_publisher_handle = 0xABC, message = 0x2, timestamp = 200000000 }'
    ]
    r=parse_events(lines)
    pubs=[x for x in r["scan_topic_streams"] if x["direction"]=="publish"]
    assert len(pubs)==1, r
    assert pubs[0]["count"]==2

def test_old_rcl_take_without_subscription_handle_is_never_inferred_scan():
    r=parse_events([
        '[12:00:00.100000] host ros2:rcl_take: { vpid = 456 }, { message = 0x2 }'])
    assert r["scan_topic_streams"]==[]
    assert r["rcl_publish_to_rcl_take_same_message_join_verified"] is False
