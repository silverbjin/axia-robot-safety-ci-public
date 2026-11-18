"""RED: first ROS scan gap MUST be causally observable in all probes.

Real public L2 #44362964527 cycle_0004 first >500ms observer gap at
225.123349--225.638921 (source 59.100->59.202), but native probe begins
225.531874 (source 59.400) and separate ROS probe begins 226.294943.
No attribution is possible if either probe starts AFTER original callback.
"""
from pathlib import Path
SOURCE=(Path(__file__).resolve().parents[1]/
        "harness/d08_same_world_replan.py").read_text()


def test_all_causal_probes_receive_native_scan_before_observer_spins():
    assert SOURCE.index('until(native_has_samples,"NATIVE_GZ_SCAN_RX_NOT_READY",9)') < SOURCE.index("thread.start()")
    assert SOURCE.index('until(isolated_has_samples,"ISOLATED_ROS_SCAN_RX_NOT_READY",9)') < SOURCE.index("thread.start()")
    assert SOURCE.index("thread.start()") < SOURCE.index('"SCAN_COSTMAP_ODOM_MISSING",25')
    assert SOURCE.index("independent_thread.start()") < SOURCE.index('"SCAN_COSTMAP_ODOM_MISSING",25')


def test_source_stamp_witness_gap_not_recovered_by_later_data():
    # This first-boundary scenario is regression DATA, not synthetic L2.
    original=[(225.123349,59100000000),(225.638921,59202000000)]
    native=[(225.531874,59400000000),(225.579729,59502000000)]
    isolated=[(226.294943,60102000000)]
    stamps=set(x[1] for x in original[:2])
    assert not stamps.issubset({x[1] for x in native})
    assert not stamps.issubset({x[1] for x in isolated})
