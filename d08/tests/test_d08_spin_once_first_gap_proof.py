"""RED: a bounded spin log may evict unrelated history, not exact first-gap proof.

Public L2 #44435647053 recorded an exact 287ms source-stamp pair with
both spin traces, yet rejected it solely because 4096 unrelated prior
spin calls had already filled the bounded deque.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import spin_trace_window_proof

MATCH={"previous_ros_stamp_ns":15_402_000_000,
       "current_ros_stamp_ns":15_501_000_000}
SPIN={"bracketed":True,"root_cause":"UNDETERMINED",
      "spin_calls_in_gap":{"observer":13,"same_process_ros":11}}

def test_later_normal_worst_pair_is_proven_even_if_older_history_truncated():
    v=spin_trace_window_proof(None,MATCH,SPIN,history_complete=False,
                              source_pair_matched=True)
    assert v["proven"] is True
    assert v["history_complete"] is False
    assert v["scope"]=="MATCHED_CURRENT_SOURCE_PAIR_ONLY"

def test_real_first_safety_gap_exact_source_stamps_required():
    first={**MATCH,"receive_gap_sec":.518394}
    v=spin_trace_window_proof(first,MATCH,SPIN,history_complete=False,
                              source_pair_matched=True)
    assert v["proven"] is True
    bad=spin_trace_window_proof(first,{**MATCH,"current_ros_stamp_ns":16_0_000_000},
                               SPIN,history_complete=False,
                               source_pair_matched=True)
    assert bad["proven"] is False
    assert bad["scope"]=="FIRST_SAFETY_GAP_SOURCE_MISMATCH"

def test_no_matching_spin_window_must_remain_hold():
    v=spin_trace_window_proof(None,MATCH,{"bracketed":False},
                              history_complete=False,
                              source_pair_matched=True)
    assert v["proven"] is False
    assert v["scope"]=="SPIN_WINDOW_UNBRACKETED"

def test_no_native_isolated_source_pair_must_remain_hold():
    v=spin_trace_window_proof(None,MATCH,SPIN,history_complete=True,
                              source_pair_matched=False)
    assert v["proven"] is False
    assert v["scope"]=="SOURCE_PAIR_NOT_MATCHED"
