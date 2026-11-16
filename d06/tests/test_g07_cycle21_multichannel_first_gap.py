"""Cycle21 RED: first WSL2 CM source gap != pure Observer delay.

Evidence from the user's sanitized six-member Cycle20 bundle; no personal
archive, ROS messages, Goal UUID, Instructor answer or real Goal in CI.
"""
from __future__ import annotations
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/"d06/tests/fixtures/g07_cycle21_first_cm_8channel_sanitized.json"

class FirstGapCrossLayer(unittest.TestCase):
    def setUp(self):
        self.fixture=json.loads(FIXTURE.read_text())

    def classify(self,fixture=None):
        from d06.live.g07_cycle21_first_gap_parity import classify_first_gap
        return classify_first_gap(self.fixture if fixture is None else fixture)

    def test_real_first_guard_and_source_gap_both_fail_hard_limit(self):
        r=self.classify()
        self.assertEqual(r["status"],"FIELD_CM_SOURCE_GAP_AND_OBSERVER_JITTER_CANDIDATE_HOLD")
        self.assertEqual(r["first_guard_transition"],"UPSTREAM_STALE_AFTER_MOTION")
        self.assertAlmostEqual(r["first_guard_cm_age_ms"],174.184617,places=5)
        self.assertAlmostEqual(r["cm_source_gap_ms"],186.714207,places=5)
        self.assertAlmostEqual(r["cm_receive_gap_ms"],189.45695,places=5)
        self.assertAlmostEqual(r["cm_observer_gap_ms"],227.710904,places=5)
        self.assertEqual(r["cm_publication_seq_delta"],1)
        self.assertFalse(r["safety_pass"])
        self.assertFalse(r["owner_goal_authorized"])
        self.assertFalse(r["owner_l3_accepted"])

    def test_four_supervisor_rmw_publications_inside_actual_cm_source_gap(self):
        r=self.classify()
        self.assertEqual(r["upstream_publications_inside_cm_gap"],4)
        self.assertAlmostEqual(r["upstream_max_source_coverage_gap_ms"],64.89631,places=5)
        self.assertEqual(r["upstream_continued_while_cm_source_gap"],True)
        self.assertEqual(r["cm_input_callback_latency_proven"],False)

    def test_distinguish_real_publication_gap_from_observer_additional_latency(self):
        r=self.classify()
        self.assertAlmostEqual(r["cm_receive_minus_source_gap_ms"],2.742743,places=5)
        self.assertAlmostEqual(r["cm_observer_minus_source_gap_ms"],40.996697,places=5)
        self.assertAlmostEqual(r["supervisor_callback_gap_ms"],102.003221,places=5)
        self.assertAlmostEqual(r["same_supervisor_pair_source_gap_ms"],47.358422,places=5)
        self.assertAlmostEqual(r["supervisor_pair_callback_minus_source_gap_ms"],54.644799,places=5)
        self.assertEqual(r["observer_only_explanation"],"INCONSISTENT_WITH_SOURCE_GAP")
        self.assertFalse(r["cm_internal_cause_proven"])

    def test_cross_channel_selected_observer_quiet_window_not_host_freeze_proof(self):
        r=self.classify()
        self.assertAlmostEqual(r["selected_cross_channel_quiet_window_ms"],88.14456,places=5)
        self.assertEqual(r["selected_quiet_channels_count"],7)
        self.assertEqual(r["cross_channel_quiet_attribution"],"OBSERVER_SHARED_DELAY_CANDIDATE_NOT_PROOF")
        self.assertAlmostEqual(r["scan_selected_callback_gap_ms"],284.361886,places=5)
        self.assertAlmostEqual(r["odom_selected_callback_gap_ms"],256.774796,places=5)
        self.assertFalse(r["whole_system_cpu_freeze_proven"])

    def test_stop_rpc_is_before_first_gap_and_clock_step_is_unresolved(self):
        r=self.classify()
        self.assertFalse(r["native_stop_rpc_overlaps_first_cm_gap"])
        self.assertEqual(r["native_stop_rpc_relative_relation"],"FIRST_GAP_AFTER_RPC")
        self.assertAlmostEqual(r["native_stop_rpc_nearest_gap_distance_ms"],435.347732)
        self.assertFalse(r["host_clock_step_excluded"])
        self.assertFalse(r["tf_lookup_block_proven"])

    def test_missing_cm_seq_or_supervisor_rmw_must_not_grant_release(self):
        import copy
        for mutator in (
            lambda e:e["events_by_kind"]["pre_guard"][1].pop("publication_sequence_relative"),
            lambda e:e["events_by_kind"].update(supervised=[]),
            lambda e:e.update(first_guard_cm_age_ms=100),
            lambda e:e.update(host_clock_step_excluded=True)
        ):
            fixture=copy.deepcopy(self.fixture)
            mutator(fixture)
            r=self.classify(fixture)
            self.assertFalse(r["safety_pass"])
            self.assertFalse(r["owner_goal_authorized"])
            self.assertNotEqual(r["status"],"FIELD_CM_SOURCE_GAP_AND_OBSERVER_JITTER_CANDIDATE_HOLD")

    def test_fixture_only_contains_sanitized_relative_numeric_data(self):
        txt=FIXTURE.read_text()
        self.assertNotIn("private_source_sha",txt)
        self.assertNotIn("/home/",txt)
        self.assertNotIn("goal_uuid",txt)
        self.assertNotIn("rmw_source_ns",txt)
        self.assertNotIn("certified_estop\": true",txt)
        self.assertTrue(all(len(v)<=16 for v in self.fixture["events_by_kind"].values()))

if __name__=="__main__":
    unittest.main()
