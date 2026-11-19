"""RED: bounded executor-thread stack snapshots during real Scan Rx pause.

Heartbeats may remain healthy while both ROS callbacks stop. The stack
at the *same first safety boundary* must distinguish wait-set vs heavy
callback paths before choosing a code fix.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import classify_executor_stack_frames

def test_wait_set_stack_is_a_candidate_not_a_confirmed_rmw_bug():
    v=classify_executor_stack_frames([
        {"function":"spin","filename":"executors.py"},
        {"function":"_wait_for_ready_callbacks","filename":"executors.py"},
        {"function":"wait","filename":"executors.py"},
    ])
    assert v["candidate"]=="RCLPY_WAITSET_OR_EVENT_WAKE"
    assert v["root_cause"]=="UNDETERMINED"

def test_expensive_callback_stack_is_visible():
    v=classify_executor_stack_frames([
        {"function":"spin","filename":"executors.py"},
        {"function":"on_grid","filename":"d08_same_world_replan.py"},
        {"function":"_lethal_near","filename":"d08_same_world_replan.py"},
    ])
    assert v["candidate"]=="OBSERVER_CALLBACK_WORK"
    assert v["root_cause"]=="UNDETERMINED"

def test_missing_frames_cannot_invent_executor_wait():
    v=classify_executor_stack_frames([])
    assert v["candidate"]=="INSUFFICIENT_STACK_EVIDENCE"

def test_in_process_heartbeat_collects_bounded_first_pause_stacks():
    s=(Path(__file__).resolve().parents[1]/
       "harness/d08_same_world_replan.py").read_text()
    assert "sys._current_frames()" in s
    assert "executor_stall_stack_samples" in s
    assert "len(executor_stall_stack_samples)<4" in s
    assert "classify_executor_stack_frames(" in s
    assert "executor_stack_at_first_gap" in s
