"""Real public, SHA-pinned G07 first-gap source/observer TF sleep bounds.

All time periods are from the SAME public diagnostic run #44049067368.
Do not attribute unrelated NO_GOAL clock audits to this exact source gap.
"""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from d06.diagnostic.classify_first_cm_gap_polling import classify

FIXTURE=(Path(__file__).resolve().parents[1] /
    "evidence/g07_cm120_task01/run_44049067368_first_gap_sanitized.json")


class FirstGapPollingBounds(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_actual_nine_sleep_spans_within_first_observer_pair(self):
        v=classify(self.data)
        self.assertEqual(v["status"],"TF_POLLING_DOMINATES_OBSERVER_WINDOW_CAUSALITY_HOLD")
        self.assertEqual(v["same_observer_pair_sleep_count"],9)
        self.assertEqual(v["sleep_request_ns"],90_000_000)
        self.assertEqual(v["sleep_wall_ns"],91_416_406)
        self.assertEqual(v["sleep_wakeup_excess_ns"],1_416_406)
        self.assertEqual(v["first_rmw_source_gap_ns"],129_299_071)
        self.assertEqual(v["first_observer_gap_ns"],128_391_951)
        self.assertEqual(v["longest_tf_call_ns"],91_732_660)
        self.assertGreater(v["sleep_to_longest_tf_ratio_nominal"],0.99)
        self.assertEqual(v["first_gap_ros_clock_progress"],"UNAVAILABLE_SAME_RUN")
        self.assertEqual(v["scheduler_runqueue"],"UNAVAILABLE_SAME_RUN")
        self.assertFalse(v["source_publication_to_monotonic_alignment_proven"])
        self.assertFalse(v["root_cause_proven"])
        self.assertFalse(v["gate_c_authorized"])
        self.assertFalse(v["cm120_release_pass"])

    def test_sleeps_before_after_first_pair_excluded(self):
        a=deepcopy(self.data)
        out=classify(a)
        self.assertEqual(a["tf_sleep"]["count"],14)
        self.assertEqual(out["same_observer_pair_sleep_count"],9)
        self.assertEqual(out["excluded_sleep_count"],5)
        self.assertEqual(out["sleep_wall_ns"],91_416_406)

    def test_untrusted_coverage_or_crossed_sleep_spans_holds(self):
        a=deepcopy(self.data)
        a["tf_sleep"]["coverage_proven"]=False
        self.assertEqual(classify(a)["status"],"SLEEP_COVERAGE_UNVERIFIED_HOLD")
        b=deepcopy(self.data)
        b["tf_sleep"]["spans"][5]["end_rel_observer_ns"]=b["tf_sleep"]["spans"][5]["start_rel_observer_ns"]-10
        self.assertEqual(classify(b)["status"],"SLEEP_INTERVAL_INVALID_HOLD")

    def test_wrong_run_id_or_release_flag_prevents_credit(self):
        a=deepcopy(self.data)
        a["run_id"]="bogus"
        self.assertEqual(classify(a)["status"],"PUBLIC_SOURCE_PROVENANCE_INVALID_HOLD")
        b=deepcopy(self.data)
        b["cm120_release_pass"]=True
        self.assertEqual(classify(b)["status"],"PUBLIC_DIAGNOSTIC_RELEASE_FLAG_INVALID_HOLD")

    def test_do_not_claim_scheduler_absence_or_tf_clock_cause(self):
        v=classify(self.data)
        self.assertFalse(v["tf_buffer_availability_wait_proven"])
        self.assertFalse(v["sim_time_stall_proven"])
        self.assertFalse(v["scheduler_wait_proven"])
        self.assertEqual(v["clock_anchor_drift_ns"],1)
        self.assertTrue(v["tf_sleep_observed"])
        self.assertFalse(v["tf_sleep_exact_rmw_source_cause_proven"])


if __name__=="__main__":
    unittest.main()
