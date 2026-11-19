"""RED: preserve early 439ms Scan stall even with rapid spin_once returns.

Real L2 #44436779871: 4096 raw spin_once events saturated before the
source-matched 439.101ms gap (native 128.120ms, isolated ROS 130.976ms).
Sampling RECORDS, not rclpy execution, must preserve relevant evidence.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_same_world_replan import new_spin_once_event_buffer, append_sampled_spin_event
from d08_scan_gap_trace import diagnose_spin_once_during_scan_gap

def record(kind,start,end):
    return {"executor":kind,"start_sec":start,"end_sec":end,
            "thread_cpu_sec":.0002}

def test_twenty_thousand_fast_spins_do_not_evict_first_gaps():
    trace=new_spin_once_event_buffer()
    last={}
    for i in range(20000):
        at=i*.003
        label="observer" if i%2 else "same_process_ros"
        append_sampled_spin_event(trace,last,record(label,at,at+.001))
    assert 400 <=len(trace)<4096
    assert trace[0]["start_sec"]<.1
    assert trace[-1]["end_sec"]>59
    pair={"previous_host_monotonic_sec":10.0,
          "current_host_monotonic_sec":10.4,"receive_gap_sec":.4}
    diag=diagnose_spin_once_during_scan_gap(pair,list(trace))
    assert diag["bracketed"] is True
    assert diag["candidate"]=="SPIN_PROGRESS_BUT_SCAN_CALLBACK_DELAYED"

def test_long_spin_once_is_captured_even_inside_sampling_interval():
    trace=new_spin_once_event_buffer()
    last={}
    append_sampled_spin_event(trace,last,record("observer",1.0,1.001))
    append_sampled_spin_event(trace,last,record("observer",1.002,1.10))
    assert len(trace)==2
    assert trace[-1]["end_sec"]==1.10

def test_no_ros_or_safety_parameters_changed_by_sampling():
    s=(Path(__file__).resolve().parents[1]/"harness/d08_same_world_replan.py").read_text()
    assert "executor.spin_once(timeout_sec=.05)" in s
    assert "append_sampled_spin_event(" in s
    assert "first_scan_receive_gap(" in s
