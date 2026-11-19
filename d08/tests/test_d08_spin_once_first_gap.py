"""RED: prove where a real Scan callback pause sits relative to spin_once.

The observed prior 0.340246s and 0.370251s Observer gaps occurred despite
bounded 50ms polling; bounded polling is not a proven fix. This L0 fixture
does NOT substitute for actual Gazebo L2.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import diagnose_spin_once_during_scan_gap

PAIR={"previous_host_monotonic_sec":100.0,
      "current_host_monotonic_sec":100.34,
      "receive_gap_sec":.34}

def event(kind,start,end,cpu=.002):
    return {"executor":kind,"start_sec":start,"end_sec":end,
            "thread_cpu_sec":cpu}

def test_spin_once_wall_overrun_is_measured_without_claiming_dds_root():
    events=[event("observer",100.02,100.32),
            event("same_process_ros",100.03,100.33)]
    verdict=diagnose_spin_once_during_scan_gap(PAIR,events)
    assert verdict["bracketed"] is True
    assert verdict["max_spin_wall_sec"]["observer"]==.30
    assert verdict["max_spin_wall_sec"]["same_process_ros"]==.30
    assert verdict["candidate"]=="BOTH_EXECUTORS_SPIN_ONCE_OVERRUN"
    assert verdict["root_cause"]=="UNDETERMINED"

def test_50ms_spin_calls_completing_while_scan_stalls_are_not_oversleep():
    events=[]
    for i in range(8):
        for executor in ("observer","same_process_ros"):
            events.append(event(executor,100.0+i*.04,100.0+i*.04+.035))
    verdict=diagnose_spin_once_during_scan_gap(PAIR,events)
    assert verdict["bracketed"] is True
    assert verdict["candidate"]=="SPIN_PROGRESS_BUT_SCAN_CALLBACK_DELAYED"
    assert verdict["root_cause"]=="UNDETERMINED"

def test_missing_executor_evidence_remains_hold():
    verdict=diagnose_spin_once_during_scan_gap(PAIR,[event("observer",100.10,100.12)])
    assert verdict["bracketed"] is False
    assert verdict["candidate"]=="INSUFFICIENT_SPIN_TRACE"

def test_spin_once_instrumentation_keeps_existing_safety_fail_closed():
    src=(Path(__file__).resolve().parents[1]/
         "harness/d08_same_world_replan.py").read_text()
    assert "time.thread_time()" in src
    assert "spin_once_events=new_spin_once_event_buffer()" in src
    assert "diagnose_spin_once_during_scan_gap(" in src
    assert "executor_spin_once_worst_gap" in src
    assert "first_scan_receive_gap(" in src
    assert "evaluate_three_phases(rows,gaps)" in src
