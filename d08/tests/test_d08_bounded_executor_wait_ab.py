"""RED: rclpy executor indefinite wait-set vs bounded polling A/B contract.

Only D08 read-only Observer executor wait; NO sensor/safety TTL change,
no new Goal/Twist, no official Nav2 or G07 safety publisher changes.
"""
from pathlib import Path
SRC=(Path(__file__).resolve().parents[1]/
     "harness/d08_same_world_replan.py").read_text()

def test_both_in_process_ros_executors_have_bounded_wait():
    assert "def bounded_spin(executor):" in SRC
    assert "executor.spin_once(timeout_sec=.05)" in SRC
    assert "bounded_spin(exe)" in SRC
    assert "bounded_spin(independent_executor)" in SRC
    assert "thread.start()" in SRC
    assert "independent_thread.start()" in SRC

def test_original_first_scan_fail_closed_and_native_witness_unchanged():
    assert "first_scan_receive_gap(" in SRC
    assert "evaluate_three_phases(rows,gaps)" in SRC
    assert '"first_scan_timing_boundary"' in SRC
    assert "compare_worst_scan_pair_receivers(" in SRC
    assert "process_heartbeat_thread.start()" in SRC
    assert "executor_stall_stack_samples" in SRC
    assert "AXIA_D08_NATIVE_RX_PROBE" in SRC
