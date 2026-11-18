"""RED: compare SAME two Scan header stamps at worst Observer gap (even 493ms).

The 493.470ms near-boundary is actual public L2, but its other-process
exact source-pair stamps were not stored then. Tests below are LOGIC ONLY.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import compare_worst_scan_pair_receivers

A=48_501_000_000
B=48_600_000_000
P={"previous_ros_stamp_ns":A,"current_ros_stamp_ns":B,
   "previous_host_monotonic_sec":1550.000,
   "current_host_monotonic_sec":1550.49347,
   "receive_gap_sec":.49347}
def samples(gap):
    return [{"source_stamp_ns":A,"host_monotonic_sec":1549.990},
            {"source_stamp_ns":B,"host_monotonic_sec":1549.990+gap}]

def test_parent_same_python_delayed_but_isolated_process_timely():
    x=compare_worst_scan_pair_receivers(P,samples(.236),
                                         samples(.237),samples(.492))
    assert x["source_pair_matched"] is True
    assert x["native_gap_sec"]==.236
    assert x["isolated_ros_gap_sec"]==.237
    assert x["same_python_gap_sec"]==.492
    assert x["candidate"]=="SAME_PYTHON_PROCESS_DELAY_CANDIDATE"
    assert x["cause"]=="UNDETERMINED"

def test_native_fast_but_two_ros_processes_delayed_means_upstream_ros_candidate():
    x=compare_worst_scan_pair_receivers(P,samples(.236),
                                         samples(.489),samples(.492))
    assert x["candidate"]=="ROS_BRIDGE_DDS_OR_SHARED_HOST_DELAY_CANDIDATE"
    assert x["cause"]=="UNDETERMINED"

def test_missing_one_exact_source_stamp_is_not_evidence():
    missing=[{"source_stamp_ns":A,"host_monotonic_sec":1549.99}]
    x=compare_worst_scan_pair_receivers(P,samples(.236),
                                         missing,samples(.492))
    assert x["source_pair_matched"] is False
    assert x["candidate"]=="SOURCE_PAIR_INCOMPLETE"
    assert x["cause"]=="UNDETERMINED"

def test_healthy_under_500ms_pair_must_not_be_called_safety_failure():
    healthy={**P,"current_host_monotonic_sec":1550.25,
             "receive_gap_sec":.25}
    x=compare_worst_scan_pair_receivers(healthy,samples(.236),
                                         samples(.237),samples(.24))
    assert x["candidate"]=="NO_LARGE_RELATIVE_RX_DELAY"
    assert x["first_500ms_violation"] is False
    assert x["cause"]=="UNDETERMINED"
