"""RED: independent ROS subscriber may receive an older Scan after Observer.

Actual #44442429149 cycle_0007:
  parent 96.900->97.002 sim stamps, host 558.730791->558.969290;
  Gazebo Rx 558.727407->558.966566;
  isolated ROS Rx 558.919806->558.966553.
Both exact source stamps exist; old cross-process ordering assumption
incorrectly called this SOURCE_PAIR_INCOMPLETE. Do not invent causation.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import compare_worst_scan_pair_receivers

A=96_900_000_000; B=97_002_000_000
PAIR={"previous_ros_stamp_ns":A,
      "current_ros_stamp_ns":B,
      "previous_host_monotonic_sec":558.730791,
      "current_host_monotonic_sec":558.969290,
      "receive_gap_sec":.238499}
def rows(a,b,with_topic=False):
    p=({"topic":"scan"} if with_topic else {})
    return [{**p,"source_stamp_ns":A,"host_monotonic_sec":a},
            {**p,"source_stamp_ns":B,"host_monotonic_sec":b}]

def test_real_source_stamps_not_discarded_by_cross_process_arrival_order():
    native=rows(558.727407,558.966566)
    isolated=rows(558.919806,558.966553,with_topic=True)
    same=rows(558.731,558.968)
    v=compare_worst_scan_pair_receivers(PAIR,native,isolated,same)
    assert v["source_pair_matched"] is True
    assert v["native_gap_sec"]==.239159
    assert v["isolated_ros_gap_sec"]==.046747
    assert v["cross_receiver_order_consistent"] is False
    assert v["candidate"]=="CROSS_RECEIVER_ORDER_UNCERTAIN"
    assert v["cause"]=="UNDETERMINED"
    assert v["first_500ms_violation"] is False

def test_normal_order_still_reports_matched_provenance():
    v=compare_worst_scan_pair_receivers(PAIR,
        rows(558.710,558.955),
        rows(558.715,558.960,True),
        rows(558.725,558.966))
    assert v["source_pair_matched"] is True
    assert v["cross_receiver_order_consistent"] is True

def test_unmatched_stamp_cannot_be_passed():
    v=compare_worst_scan_pair_receivers(PAIR,
        rows(558.710,558.955),
        [{"topic":"scan","source_stamp_ns":A,
          "host_monotonic_sec":558.715}],
        rows(558.725,558.966))
    assert v["source_pair_matched"] is False
