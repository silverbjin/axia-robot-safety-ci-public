"""RED: prevent first three-phase spin_once timeline evidence eviction.

Public real Gazebo #44434770157 first three-phase cycle had a 365.171ms
Observer gap (native 138.206ms / isolated ROS 138.025ms) but the
1024-event deque discarded both relevant executor samples. Diagnostic
custody only; does not relax any safety deadline.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_same_world_replan import new_spin_once_event_buffer

def test_first_three_phase_gap_survives_2600_normal_50ms_spin_calls():
    events=new_spin_once_event_buffer()
    for i in range(2600):
        events.append({"executor":"observer" if i%2 else "same_process_ros",
                       "start_sec":i*.025, "end_sec":i*.025+.02,
                       "thread_cpu_sec":.00001})
    assert len(events)==2600
    assert events[0]["start_sec"]==0
    assert events[-1]["start_sec"]>64
    assert 2600<=events.maxlen<=4096

def test_memory_stays_bounded_after_large_run():
    events=new_spin_once_event_buffer()
    for i in range(6500):
        events.append({"executor":"observer","start_sec":i})
    assert len(events)==events.maxlen
    assert events.maxlen<=4096
