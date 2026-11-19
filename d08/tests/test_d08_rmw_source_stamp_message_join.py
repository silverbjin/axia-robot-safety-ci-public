"""RED: exact RMW source timestamps, not event gaps, must join /scan streams.

Synthetic L0 fixtures are only for parser correctness; real Jazzy/Gazebo
trace data is the sole basis for any actual matching verdict.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from d08_rcl_trace_summary import parse_events

def _init():
    return [
        '[12:00:00.000000] host ros2:rcl_publisher_init: { vpid = 12, procname = "parameter_bridg" }, { publisher_handle = 0xa, rmw_publisher_handle = 0xB, topic_name = "/scan" }',
        '[12:00:00.000000] host ros2:rcl_subscription_init: { vpid = 24, procname = "python3" }, { subscription_handle = 0xc, rmw_subscription_handle = 0xD, topic_name = "/scan" }']

def test_exact_source_timestamp_links_publish_to_take_no_dds_claim():
    x=parse_events(_init()+[
        '[12:00:00.100000] host ros2:rmw_publish: { vpid = 12 }, { rmw_publisher_handle = 0xB, timestamp = 1710000000000000100 }',
        '[12:00:00.131000] host ros2:rmw_take: { vpid = 24 }, { rmw_subscription_handle = 0xD, source_timestamp = 1710000000000000100, taken = 1 }',
        '[12:00:00.200000] host ros2:rmw_publish: { vpid = 12 }, { rmw_publisher_handle = 0xB, timestamp = 1710000000000000200 }',
        '[12:00:00.231000] host ros2:rmw_take: { vpid = 24 }, { rmw_subscription_handle = 0xD, source_timestamp = 1710000000000000200, taken = 1 }'])
    j=x["rmw_scan_source_stamp_join"]
    assert j["matched_unique_pairs"]==2
    assert j["max_publish_to_take_sec"]==0.031
    assert j["state"]=="SOURCE_TIMESTAMP_JOIN_ONLY"
    assert x["publisher_rmw_cadence_measured"] is False
    assert x["rcl_publish_to_rcl_take_same_message_join_verified"] is False
    assert x["cm_internal_receiver_ttl_verified"] is False

def test_duplicate_publisher_timestamp_cannot_be_claimed_unique():
    stamp="1710000000000000100"
    x=parse_events(_init()+[
        f'[12:00:00.100000] host ros2:rmw_publish: {{ vpid = 12 }}, {{ rmw_publisher_handle = 0xB, timestamp = {stamp} }}',
        f'[12:00:00.101000] host ros2:rmw_publish: {{ vpid = 12 }}, {{ rmw_publisher_handle = 0xB, timestamp = {stamp} }}',
        f'[12:00:00.131000] host ros2:rmw_take: {{ vpid = 24 }}, {{ rmw_subscription_handle = 0xD, source_timestamp = {stamp}, taken = 1 }}'])
    j=x["rmw_scan_source_stamp_join"]
    assert j["matched_unique_pairs"]==0
    assert j["duplicate_publisher_source_timestamps"]>=1
    assert j["state"]=="UNDETERMINED"

def test_unmatched_or_zero_source_stamp_fails_closed():
    x=parse_events(_init()+[
        '[12:00:00.100000] host ros2:rmw_publish: { vpid = 12 }, { rmw_publisher_handle = 0xB, timestamp = 1710000000000000100 }',
        '[12:00:00.131000] host ros2:rmw_take: { vpid = 24 }, { rmw_subscription_handle = 0xD, source_timestamp = 1710000000000000900, taken = 1 }',
        '[12:00:00.150000] host ros2:rmw_take: { vpid = 24 }, { rmw_subscription_handle = 0xD, source_timestamp = 0, taken = 1 }'])
    assert x["rmw_scan_source_stamp_join"]["matched_unique_pairs"]==0
    assert x["rmw_scan_source_stamp_join"]["state"]=="UNDETERMINED"
