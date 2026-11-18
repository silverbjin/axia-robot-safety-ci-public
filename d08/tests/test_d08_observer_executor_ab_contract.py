"""RED: the read-only observer has short callbacks, default mutually
exclusive callback group and does not gain parallelism from a thread pool.

Use official rclpy SingleThreadedExecutor as ONE A/B hypothesis. This
static L0 contract is not causal proof: actual Gazebo L2 timing is mandatory.
"""
from pathlib import Path
SOURCE=(Path(__file__).resolve().parents[1]/"harness/d08_same_world_replan.py").read_text()

def test_readonly_observer_does_not_schedule_one_group_on_two_pool_workers():
    assert "exe=SingleThreadedExecutor()" in SOURCE
    assert "exe=MultiThreadedExecutor(num_threads=2)" not in SOURCE
    assert "Thread(target=exe.spin" in SOURCE
    assert "independent_executor=SingleThreadedExecutor()" in SOURCE

def test_single_executor_must_not_erase_the_first_500ms_violation():
    assert "first_scan_receive_gap(" in SOURCE
    assert "evaluate_three_phases(rows,gaps)" in SOURCE
    assert "first_scan_timing_boundary" in SOURCE
    assert "D08_FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS" in (
      Path(__file__).resolve().parents[1]/"harness/d08_scan_gap_trace.py"
    ).read_text() or "FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS" in SOURCE
