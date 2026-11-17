"""Task 01: diagnose original TF's individual sleep interval in same CM callback.
Synthetic L0 only. A sleep observed is never a proven TF Buffer wait or
scheduler root cause. RMW source SYSTEM and Observer MONOTONIC remain distinct.
"""
import unittest
from d06.diagnostic.analyze_first_cm_tf import analyze
from d06.tests.test_g07_cm120_tf_first_gap_join import (
    observer, trace, anchor, line, READY
)

def poll(t0,t1,pid=4242,tid=33,req_ms=10,rc=0):
    return (f"TF_SLEEP pid={pid} tid={tid} mono_start_ns={round(t0*1e9)} "
            f"mono_end_ns={round(t1*1e9)} req_ns={req_ms*1000000} rc={rc}")

class FirstGapSameTFCallSleepSpan(unittest.TestCase):
    def test_sleep_intervals_inside_tf_and_observer_pair_not_source_proof(self):
        v=analyze(observer(),trace(),[
            READY,line(12.014,12.105,cpu=.0003),
            poll(12.024,12.034),poll(12.044,12.054)],anchor())
        self.assertEqual(v["status"],"TF_FUNCTION_DOMINANT_WAIT_CAUSE_UNPROVEN")
        self.assertEqual(v["tf_sleep_event_count"],2)
        self.assertAlmostEqual(v["tf_sleep_nominal_observer_overlap_ms"],20,places=3)
        self.assertFalse(v["source_publication_to_monotonic_alignment_proven"])
        self.assertFalse(v["tf_sleep_in_source_gap_proven"])
        self.assertFalse(v["root_cause_proven"])
        self.assertFalse(v["gate_c_authorized"])
    def test_sleep_other_pid_does_not_count_as_current_callback(self):
        v=analyze(observer(),trace(),[
            READY,line(12.014,12.105,cpu=.0003),
            poll(12.024,12.034,pid=4243)],anchor())
        self.assertEqual(v["tf_sleep_event_count"],0)
        self.assertFalse(v["gate_c_authorized"])
    def test_sleep_extends_beyond_matched_tf_interval_fails_closed(self):
        v=analyze(observer(),trace(),[
            READY,line(12.014,12.105,cpu=.0003),
            poll(12.104,12.124)],anchor())
        self.assertEqual(v["status"],"TF_SLEEP_SPAN_CROSS_BOUNDARY_HOLD")
        self.assertFalse(v["root_cause_proven"])
    def test_duplicate_overlapping_sleeps_fail_closed(self):
        v=analyze(observer(),trace(),[
            READY,line(12.014,12.105,cpu=.0003),
            poll(12.024,12.040),poll(12.030,12.044)],anchor())
        self.assertEqual(v["status"],"TF_SLEEP_SPANS_OVERLAP_HOLD")
    def test_malformed_sleep_span_fails_closed(self):
        v=analyze(observer(),trace(),[
            READY,line(12.014,12.105,cpu=.0003),
            poll(12.055,12.044)],anchor())
        self.assertEqual(v["status"],"TF_SLEEP_INTERVAL_INVALID_HOLD")

if __name__=="__main__":
    unittest.main()
