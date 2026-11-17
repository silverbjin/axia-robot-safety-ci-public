"""Task 01 RED: TF function must overlap the FIRST CM source gap itself.
Do not equate "inside callback overlapping gap" with "inside first gap".
Synthetic data only; no ROS/Goal/safety acceptance is authorized.
"""
import unittest
from d06.diagnostic.analyze_first_cm_tf import analyze
from d06.tests.test_g07_cm120_tf_first_gap_join import (
    READY, anchor, cb, line, metadata, observer,
)

def synthetic(callback_begin, callback_end, tf_begin, tf_end):
    trace = metadata() + [
        cb("ros2:callback_start", callback_begin),
        cb("ros2:callback_end", callback_end),
    ]
    return analyze(observer(), trace, [READY, line(tf_begin, tf_end, cpu=.0003)], anchor())

class Task01FirstSourceGapTemporalJoin(unittest.TestCase):
    def test_tf_inside_callback_but_entirely_before_first_source_gap_is_hold(self):
        # First source gap is [12.000, 12.132]; callback overlaps by 20ms.
        # TF consumes 100ms of the callback, but ends before 12.000.
        r = synthetic(11.880, 12.020, 11.889, 11.989)
        self.assertEqual(r["status"], "TF_OUTSIDE_FIRST_CM_OBSERVER_PAIR_HOLD")
        self.assertFalse(r["root_cause_proven"])
        self.assertFalse(r["gate_c_authorized"])
        self.assertFalse(r["cm120_release_pass"])
        self.assertFalse(r["source_publication_to_monotonic_alignment_proven"])

    def test_tf_straddles_first_source_gap_cannot_locate_aggregated_sleep(self):
        r = synthetic(11.960, 12.110, 11.970, 12.080)
        self.assertEqual(r["tf_observer_pair_temporal_relation"], "PARTIAL_OVERLAP")
        self.assertAlmostEqual(r["tf_nominal_overlap_observer_pair_ms"], 80.0, places=3)
        self.assertFalse(r["tf_sleep_in_source_gap_proven"])
        self.assertFalse(r["root_cause_proven"])
        self.assertFalse(r["gate_c_authorized"])

    def test_mono_observer_window_never_proves_rmw_system_publication_alignment(self):
        # RMW source nanoseconds identify the first gap; a.t/b.t are a
        # different host-MONOTONIC observer interval. It is invalid to treat
        # their absolute epochs as identical without source-clock calibration.
        r = synthetic(12.010, 12.110, 12.014, 12.105)
        self.assertEqual(r["tf_observer_pair_temporal_relation"], "FULL_NOMINAL_OVERLAP")
        self.assertFalse(r["source_publication_to_monotonic_alignment_proven"])
        self.assertFalse(r["tf_sleep_in_source_gap_proven"])
        self.assertFalse(r["root_cause_proven"])
        self.assertFalse(r["gate_c_authorized"])

    def test_tf_fully_in_first_source_gap_is_still_not_tf_buffer_or_scheduler_cause(self):
        r = synthetic(12.010, 12.110, 12.014, 12.105)
        self.assertEqual(r["tf_observer_pair_temporal_relation"], "FULL_NOMINAL_OVERLAP")
        self.assertAlmostEqual(r["tf_nominal_overlap_observer_pair_ms"], 91.0, places=3)
        # Existing TF clock interval cannot prove which library sleep or queue
        # caused the gap. S2 sleep totals are from a DIFFERENT Goal run.
        self.assertFalse(r["tf_sleep_in_source_gap_proven"])
        self.assertFalse(r["root_cause_proven"])
        self.assertFalse(r["tf_wait_proven"])
        self.assertFalse(r["scheduler_wait_proven"])
        self.assertFalse(r["gate_c_authorized"])
        self.assertFalse(r["cm120_release_pass"])

if __name__ == "__main__":
    unittest.main()
