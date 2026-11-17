"""Task01 actual public Jazzy CM RMW source->native publish TF polling gate.

Actual source is a SHA256-verified public GitHub Actions numeric-only artifact.
No redacted PID/TID, TF frame, raw geometry, bag or user secrets are stored.
This is Task01 ROOT cause *for the selected first CM gap*, not CM120 release.
"""
import json
import unittest
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[1]/"evidence/g07_cm120_task01/run_44109119429_publisher_causality.json"

class FirstNativeRmwPublisherGap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_actual_public_artifact_is_source_pinned_and_auditable(self):
        d=self.d
        self.assertEqual(d["run_id"],"44109119429")
        self.assertEqual(d["original_artifact_id"],14339398674)
        self.assertEqual(d["original_sanitized_sha256"],
            "383ce756a50e136eaeb2eab83e8c10d174f280bbbe2c43f4075d754df380f3bd")
        self.assertEqual(d["source"]["public_ci_diagnostic_sha"],
                         "28c5e41e3c13be3df7bd6bc83579a85a32a41927")
        self.assertEqual(d["source"]["public_student_runtime_sha"],
                         "6a3047b5aa219687f5fc918e467cea5115d3d482")
        self.assertEqual(d["source"]["configured_use_composition"],False)

    def test_first_native_publisher_gap_has_exact_stamps_and_120ms_tf_sleep(self):
        d=self.d
        p=d["same_run_exact_publisher_tf_join"]
        self.assertEqual(p["status"],"CM_SOURCE_TF_POLLING_NATIVE_PUBLISH_JOIN_PROVEN_SCOPED")
        self.assertTrue(p["rmw_publisher_source_timestamp_pair_exact"])
        self.assertTrue(p["same_cm_input_callback_tf_publisher"])
        self.assertTrue(p["source_clock_epoch_calibrated"])
        self.assertEqual(p["source_gap_ns"],172_590_315)
        self.assertEqual(p["observer_gap_ns"],173_162_403)
        self.assertEqual(p["native_rmw_publish_gap_ns"],172_591_647)
        self.assertLess(abs(p["source_gap_ns"]-p["native_rmw_publish_gap_ns"]),5_000)
        self.assertLess(p["native_source_max_clock_error_ns"],5_000)
        self.assertEqual(p["tf_call_wall_ns"],122_282_121)
        self.assertEqual(p["tf_sleep_requests_ns"],120_000_000)
        self.assertEqual(p["tf_sleep_count"],12)
        self.assertTrue(p["tf_call_sleep_coverage_complete"])
        self.assertIs(p["tf_available_before"],False)
        self.assertIs(p["tf_available_after"],True)
        self.assertEqual(p["tf_end_to_second_native_publish_ns"],161_663)
        self.assertGreaterEqual(p["tf_sleep_requests_ns"]/p["source_gap_ns"],0.69)
        self.assertTrue(d["verdict"]["task01_selected_cm_publisher_gap_tf_polling_cause_proven"])

    def test_guard_first_ttl_breach_and_release_still_hold(self):
        d=self.d
        self.assertEqual(d["first_guard_latch"]["reason"],"UPSTREAM_STALE_AFTER_MOTION")
        self.assertEqual(d["first_guard_latch"]["cm_age_ns"],156_944_056)
        self.assertFalse(d["first_guard_latch"]["exact_pair_overlap_proven"])
        self.assertFalse(d["verdict"]["scheduler_runqueue_wait_proven"])
        self.assertFalse(d["verdict"]["cm120_tracer_off_release_pass"])
        self.assertFalse(d["verdict"]["owner_wsl2_l3_accepted"])
        self.assertFalse(d["verdict"]["certified_estop"])
        self.assertEqual(d["verdict"]["moving_goal_runner_rc"],2)


if __name__=="__main__":
    unittest.main()
