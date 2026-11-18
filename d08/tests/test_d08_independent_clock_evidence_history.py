"""Regression: 512-sample /clock deque missed early 8-cycle timing evidence.

This is bounded read-only history, not a TTL relaxation and not ROS L2 proof.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_same_world_replan import new_independent_rx_buffers
from d08_scan_gap_trace import diagnose_first_receive_boundary


def test_250hz_clock_does_not_evict_9_second_first_gap_window():
    buffers=new_independent_rx_buffers()
    for i in range(2400):
        buffers["clock"].append({"at":i*.004,"stamp_ns":i*4_000_000})
    assert len(buffers["clock"])==2400
    assert buffers["clock"][0]["at"]==0.0
    assert buffers["clock"][-1]["at"]>=9.5
    assert 2400 <= buffers["clock"].maxlen <= 4096


def test_history_bounded_but_first_gap_still_classifiable():
    buffers=new_independent_rx_buffers()
    assert set(buffers)=={"scan","odom","clock","tf"}
    for i in range(2400):
        buffers["clock"].append({"at":i*.004,"stamp_ns":i*4_000_000})
    first={"previous_host_monotonic_sec":.2,
           "current_host_monotonic_sec":.75,
           "receive_gap_sec":.55}
    clock=[v["at"] for v in buffers["clock"]]
    witness=diagnose_first_receive_boundary(first,{
        "scan":[.16,.26,.36,.46,.56,.66,.76],
        "clock":clock,
    })
    assert witness["clock_receive_gap_measured"] is True
    assert witness["independent_scan_window_bracketed"] is True
    assert witness["first_scan_violation_retained"] is True
    for i in range(2400,5800):
        buffers["clock"].append({"at":i*.004,"stamp_ns":i*4_000_000})
    assert len(buffers["clock"])==buffers["clock"].maxlen
    assert len(buffers["clock"]) <=4096
