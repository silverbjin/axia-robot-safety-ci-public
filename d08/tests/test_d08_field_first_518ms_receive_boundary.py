"""Field VG0B5q first-Scan >500ms regression; NO_GOAL, no fake Gazebo proof.

Only sanitized timing numbers from original Owner ZIP are committed; never
archive raw paths, images, models or private/teacher source.
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from d08_scan_gap_trace import (
    first_scan_receive_gap, diagnose_first_receive_boundary,
)
from d08_same_world_replan import evaluate_three_phases


FIELD_SCAN = (
    (1549.934764, 48_402_000_000),
    (1550.021209, 48_501_000_000),
    (1550.539603, 48_600_000_000),
    (1550.541846, 48_699_000_000),
    (1550.549511, 48_798_000_000),
)
# In original JSON: previous=1550.021209, current=1550.539602,
# rounded gap=0.518394. Float rounding is contextual, not a new datum.


def actual_field_boundary():
    # Keep the captured JSON timing exactly rather than recomputing it from
    # six-decimal rounded host timestamps.
    return {
        "kind": "ROS_LASERSCAN_FIRST_RECEIVE_GAP",
        "sample_index": 2,
        "receive_gap_sec": 0.518394,
        "header_sim_gap_sec": 0.099,
        "previous_host_monotonic_sec": 1550.021209,
        "current_host_monotonic_sec": 1550.539602,
        "previous_ros_stamp_ns": 48_501_000_000,
        "current_ros_stamp_ns": 48_600_000_000,
        "limit_sec": 0.5,
        "publisher_rmw_gap_measured": False,
        "clock_receive_gap_measured": False,
        "not_proven_source_vs_transport": True,
    }


def safe_phases():
    return [
        {"stage": stage, "source": "official_compute_path_to_pose",
         "frame": "map", "goal_sent": False, "gazebo_native_ack": True,
         "poses": [[-2, -.5], [-1.99, -.2], [-1.9, .2]],
         "scan_stamp": stamp, "costmap_stamp": stamp,
         "lethal_near": lethal,
         "path_distance_from_obstacle_m": distance}
        for stage, stamp, lethal, distance in (
            ("before", 1.0, 0, .03),
            ("intrusion", 2.0, 66, .31),
            ("restored", 3.0, 0, .035))
    ]


def test_field_518394ms_stays_first_failure_after_recovered_callbacks():
    boundary = first_scan_receive_gap(FIELD_SCAN)
    assert boundary["sample_index"] == 2
    assert abs(boundary["receive_gap_sec"] - 0.518394) < 0.000003
    assert boundary["header_sim_gap_sec"] == .099
    with pytest.raises(ValueError, match="D08_FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS"):
        evaluate_three_phases(safe_phases(), [.086445, .518394, .002243, .007665])
    assert evaluate_three_phases(safe_phases(), [.086445, .438203, .002243, .007665])[
        "status"].endswith("_PASS_NO_GOAL")


def test_no_independent_clock_and_source_cannot_claim_causality():
    verdict = diagnose_first_receive_boundary(actual_field_boundary(), {})
    assert verdict["cause"] == "UNDETERMINED"
    assert verdict["first_scan_violation_retained"] is True
    assert verdict["independent_scan_window_bracketed"] is False
    assert verdict["publisher_rmw_gap_measured"] is False
    assert verdict["sim_native_gap_measured"] is False


def test_independent_scan_timely_means_local_observer_candidate_not_proven_cause():
    boundary = actual_field_boundary()
    stream = [1549.98, 1550.08, 1550.18, 1550.28,
              1550.38, 1550.48, 1550.58]
    verdict = diagnose_first_receive_boundary(boundary, {
        "scan": stream,
        "clock": stream,
        "odom": stream,
    }, observer_first_callback={"previous_entry_sec": 1550.021209,
                                "current_entry_sec": 1550.539602})
    assert verdict["cause"] == "UNDETERMINED"
    assert verdict["candidate"] == "OBSERVER_DISPATCH_OR_QOS"
    assert verdict["independent_scan_window_bracketed"] is True
    assert verdict["independent_scan_max_gap_sec"] <= .5
    assert verdict["native_source_gap_not_measured"] is True


def test_shared_ros_receive_delay_is_not_attributed_to_gazebo_or_bridge():
    verdict = diagnose_first_receive_boundary(actual_field_boundary(), {
        "scan": [1549.9, 1550.0, 1550.54, 1550.64],
        "clock": [1549.9, 1550.0, 1550.54, 1550.64],
        "odom": [1549.9, 1550.0, 1550.54, 1550.64],
    })
    assert verdict["cause"] == "UNDETERMINED"
    assert verdict["candidate"] == "SHARED_ROS_RECEIVE_DELAY"
    assert verdict["independent_scan_max_gap_sec"] > .5
    assert verdict["clock_receive_gap_measured"] is True
    assert verdict["publisher_rmw_gap_measured"] is False


def test_post_processing_gap_cannot_be_hidden_by_earlier_callback_entry():
    verdict = diagnose_first_receive_boundary(actual_field_boundary(), {
        "scan": [1549.98, 1550.08, 1550.18, 1550.28, 1550.38, 1550.48, 1550.58],
    }, observer_first_callback={"previous_entry_sec": 1550.021209,
                                "current_entry_sec": 1550.421209})
    assert verdict["cause"] == "UNDETERMINED"
    assert verdict["candidate"] == "OBSERVER_PROCESSING_OR_LOCK"
    assert verdict["first_scan_violation_retained"] is True
