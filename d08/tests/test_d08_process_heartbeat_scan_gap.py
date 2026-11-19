"""RED: process-local heartbeat vs real worst Scan callback gap.

A normal heartbeat with delayed ROS subscribers => executor/wait-set layer.
A stalled heartbeat plus delayed callbacks => Python-process GIL/scheduler
candidate; process_time ratio is context, not proof of an OS-level cause.
No synthetic Scan publish, Goal, Velocity, or TTL relaxation.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import analyze_process_heartbeat_gap

PAIR={"previous_host_monotonic_sec":100.0,"current_host_monotonic_sec":100.45}

def make_events(timestamps, cpu_times=None):
    cpu_times=cpu_times or [i*0.001 for i in range(len(timestamps))]
    return [{"host_monotonic_sec":t, "process_cpu_sec":c}
            for t,c in zip(timestamps,cpu_times)]

def test_stalled_process_heartbeat_favors_gil_or_scheduler_not_executor_only():
    v=analyze_process_heartbeat_gap(PAIR,make_events([
        99.96,99.98,100.0,100.02,100.41,100.43,100.45,100.47]))
    assert v["bracketed"] is True
    assert v["max_heartbeat_gap_sec"]==.39
    assert v["candidate"]=="PROCESS_THREAD_OR_GIL_SCHEDULING_STALL"
    assert v["root_cause"]=="UNDETERMINED"

def test_normal_process_heartbeat_with_450ms_ros_gap_is_executor_side():
    timestamps=[99.96+i*.02 for i in range(28)]
    v=analyze_process_heartbeat_gap(PAIR,make_events(timestamps))
    assert v["bracketed"] is True
    assert v["max_heartbeat_gap_sec"]<=.021
    assert v["candidate"]=="ROS_EXECUTOR_DISPATCH_OR_RMW_DELAY"
    assert v["root_cause"]=="UNDETERMINED"

def test_incomplete_first_gap_window_is_not_promoted():
    v=analyze_process_heartbeat_gap(PAIR,make_events([100.2,100.3,100.4]))
    assert v["bracketed"] is False
    assert v["max_heartbeat_gap_sec"] is None
    assert v["candidate"]=="HEARTBEAT_WINDOW_UNBRACKETED"

def test_source_code_arms_heartbeat_before_observer_and_keeps_bounded_history():
    s=(Path(__file__).resolve().parents[1]/
       "harness/d08_same_world_replan.py").read_text()
    assert "process_heartbeat_thread.start()" in s
    assert s.index("process_heartbeat_thread.start()") < s.index("thread.start()")
    assert "process_heartbeat_samples=deque(maxlen=2048)" in s
    assert "analyze_process_heartbeat_gap(" in s
