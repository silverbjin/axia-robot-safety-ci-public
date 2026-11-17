"""Real public Gazebo run 44101521543 numeric-only same-run evidence contract.

This verifies the exact official CM TF invocation and 12 real 10ms sleeps
in the first 120ms RMW-source-breached observer pair. It MUST NOT infer a
proven RMW SYSTEM-to-MONOTONIC clock join or unmeasured runqueue wait.
"""
import json
import unittest
from pathlib import Path

EVIDENCE=(Path(__file__).resolve().parents[1]/
    "evidence/g07_cm120_task01/run_44101521543_native_tf_budget_summary.json")
SHA256="b71afac1ad0a8615f4d407745956aca53089814eb338d755a32ddbecc75a2c36"


class RealFirstGapNativeTfBudget(unittest.TestCase):
    def test_original_artifact_provenance_and_no_release_grant(self):
        v=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(v["run_id"],"44101521543")
        self.assertEqual(v["original_public_artifact_id"],14335962966)
        self.assertEqual(v["original_sanitized_sha256"],SHA256)
        self.assertEqual(v["public_diagnostic_sha"],
                         "02ad6c63f3c16ee8e0526e6f176db92e5639d84a")
        self.assertEqual(v["public_student_runtime_sha"],
                         "6a3047b5aa219687f5fc918e467cea5115d3d482")
        for key in ("cm120_tracer_off_release_pass","root_cause_proven",
                    "publisher_source_causality_proven","scheduler_runqueue_wait_proven",
                    "tf_internal_clock_proven","certified_estop",
                    "owner_wsl2_l3_accepted"):
            self.assertIs(v["verdict"][key],False,key)

    def test_same_native_tf_call_first_observer_pair_has_actual_120ms_sleeps(self):
        v=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        gap=v["same_observer_first_source_gap"]
        call=v["native_cm_tf_call_within_first_observer_pair"]
        verdict=v["verdict"]
        self.assertGreater(gap["rmw_source_gap_ns"],120_000_000)
        self.assertGreater(gap["observer_gap_ns"],120_000_000)
        self.assertTrue(gap["source_sequence_consecutive_observed"])
        self.assertEqual(call["wholly_inside_first_observer_pair_count"],1)
        self.assertGreater(call["start_rel_observer_ns"],0)
        self.assertLess(call["end_rel_observer_ns"],gap["observer_gap_ns"])
        self.assertEqual(call["end_rel_observer_ns"]-call["start_rel_observer_ns"],
                         call["original_tf_wall_ns"])
        self.assertEqual(call["sleep_count"],12)
        self.assertEqual(call["sleep_request_ns"],120_000_000)
        self.assertEqual(call["sleep_wall_ns"],121_830_939)
        self.assertTrue(call["complete_sleep_coverage"])
        self.assertIs(call["tf_available_before_call"],False)
        self.assertIs(call["tf_available_after_call"],True)
        self.assertLess(call["thread_cpu_ns"],1_000_000)
        self.assertEqual(call["original_tf_wall_ns"]-call["sleep_request_ns"],
                         call["nonrequested_wall_upper_bound_ns"])
        self.assertLess(call["nonrequested_wall_upper_bound_ns"],3_000_000)
        self.assertTrue(verdict["same_native_cm_tf_call_and_sleep_coverage_proven"])
        self.assertTrue(verdict["tf_transform_unavailable_at_entry_proven"])
        self.assertFalse(verdict["publisher_source_causality_proven"])

    def test_clock_mapping_must_remain_explicitly_conditional(self):
        v=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        p=v["conditional_same_host_epoch_projection"]
        src=v["same_observer_first_source_gap"]
        self.assertEqual(src["wall_minus_monotonic_anchor_delta_ns"],30)
        self.assertEqual(src["rmw_to_received_latencies_ns"],[385532,133433])
        self.assertEqual(src["received_to_observer_anchor_projected_ns"],
                         [7328706,6566754])
        self.assertEqual(p["source_second_minus_tf_end_ns_if_same_host_realtime_mapping"],
                         217417)
        self.assertIs(p["clock_epoch_alignment_proven"],False)
        self.assertIs(p["rmw_sender_epoch_validated_against_local_mono"],False)
        self.assertIn("SOURCE_CLOCK_CAUSALITY_HOLD",v["verdict"]["status"])


if __name__=="__main__":
    unittest.main()
