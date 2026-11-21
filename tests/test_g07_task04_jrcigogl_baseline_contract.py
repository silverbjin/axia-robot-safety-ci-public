"""AXIA G07 educational MVP baseline contract, real Owner WSL2 jrCIgoGl.

Immutable SHA256-backed field evidence was examined offline. This is a
small public derived fixture (not user raw bag); it NEVER changes the
original raw owner's HOLD_RAW_REVIEW_AND_VISUAL_PENDING status.
"""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"tests/fixtures/g07_task04_jrcigogl_20261120_public_derived.json"
BASELINE=ROOT/"docs/operations/AXIA_G07_TASK04_DEMO_BASELINE_20261119_KO.md"
REPORT=ROOT/"docs/operations/AXIA_G07_TASK04_JRCIGOL_OWNER_MVP_ACCEPTANCE_20261120_KO.md"
OWNER=ROOT/"scripts/axia_g07_task04_owner_moving_l3_once.sh"


class ActualFieldMvpBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=json.loads(FIXTURE.read_text())
        cls.doc=BASELINE.read_text()
        cls.report=REPORT.read_text()

    def test_real_owner_evidence_provenance(self):
        a=self.a
        self.assertEqual(a["run_id"],"jrCIgoGl")
        self.assertEqual(a["tar_sha256"],"2d454845183704d8f53b50dcdbaa48446d1103bfa9f750cc3ce662d9af7684db")
        self.assertEqual(a["zip_sha256"],"92c31af277bc7a64742540a2b9e5c99f13ded4cac51ae1bd1b76f3c16a4dd331")
        self.assertEqual(a["manifest_entries_valid"],141)
        self.assertEqual(a["sqlite_quick_check"],"ok")
        self.assertEqual(a["bag_topics"],14)
        self.assertEqual(a["first_failure"],"NONE")
        self.assertEqual(a["source_sha"],"5c7983598fa3bcd7148433a06f37a4e78b091273")

    def test_one_real_goal_slow_stop_cancel_and_21_numeric_gates(self):
        a=self.a
        self.assertEqual(a["numeric_checks_pass"],21)
        self.assertEqual(a["numeric_checks_total"],21)
        self.assertTrue(a["real_nav2_goal_executing"])
        self.assertTrue(a["exact_goal_uuid_cancelled"])
        self.assertTrue(a["real_scan_fixture_ack"])
        self.assertTrue(a["nav_loc_ack"])
        self.assertEqual(a["cm_process_exit_code"],0)
        self.assertEqual(a["actual_gui_window_count"],2)
        self.assertFalse(a["guard_latched"])
        self.assertGreater(a["odom_movement_m"],0.12)
        self.assertGreater(a["zero_dwell_sec"],1.0)

    def test_ttl_values_are_observed_and_not_relaxed(self):
        a=self.a
        for metric,ceiling in [
            ("scan_gap_max_ms",300),
            ("cm_source_gap_max_ms",120),
            ("cm_observer_gap_max_ms",120),
            ("guard_internal_cm_age_max_ms",150),
            ("guard_status_gap_max_ms",150),
        ]:
            self.assertLessEqual(a[metric],ceiling,(metric,a[metric]))
        self.assertEqual(a["clock_backward_pairs"],0)
        self.assertEqual(a["pre_guard_rmw_source_backward_pairs"],0)
        self.assertEqual(a["supervised_rmw_source_backward_pairs"],0)

    def test_scope_and_old_baseline_are_both_preserved(self):
        a=self.a
        self.assertEqual(a["raw_machine_status"],"HOLD_RAW_REVIEW_AND_VISUAL_PENDING")
        self.assertFalse(a["raw_machine_l3_accepted"])
        self.assertFalse(a["visual_content_verified"])
        self.assertFalse(a["formal_safety_timing_accepted"])
        self.assertFalse(a["certified_estop"])
        for item in ("AXIA-G07-T04-DEMO-BASELINE-20261119-CZObXAdP",
                     "AXIA-G07-T04-DEMO-BASELINE-20261120-jrCIgoGl",
                     "FORMAL_SAFETY_TIMING_ACCEPTANCE=NOT_CLAIMED",
                     "CERTIFIED_ESTOP=false"):
            self.assertIn(item,self.doc)
        for item in ("jrCIgoGl","21/21","HOLD_RAW_REVIEW_AND_VISUAL_PENDING",
                     "RViz", "Destroyable", "188.578"):
            self.assertIn(item,self.report)
        self.assertIn(a["source_sha"],OWNER.read_text())
        self.assertIn("CI_L2_RUN=44653465671",OWNER.read_text())


class FirstGuardLatchFailClosedRegression(unittest.TestCase):
    """Real public Gazebo Moving Goal #44652034063, never relabel as PASS.

    Original job 136009021796 logged actual Guard tick, last CM RX and
    independent CM Observer. It did NOT prove the CM publisher's matching
    source-publish timestamp, so root cause must remain undetermined.
    """

    def test_actual_first_guard_latch_and_unproven_source_cause(self):
        a=json.loads((ROOT/"tests/fixtures/g07_c32_first_guard_latch_44652034063.json").read_text())
        self.assertEqual(a["run_id"],44652034063)
        self.assertEqual(a["first_transition"],"UPSTREAM_STALE_AFTER_MOTION")
        guard_age_ms=(a["guard_tick_monotonic_sec"]-a["guard_last_cm_rx_monotonic_sec"])*1000
        observer_age_ms=(a["guard_tick_monotonic_sec"]-a["cm_observer_last_rx_monotonic_sec"])*1000
        self.assertAlmostEqual(guard_age_ms,188.577986,places=3)
        self.assertAlmostEqual(observer_age_ms,173.465091,places=3)
        self.assertGreater(guard_age_ms,a["guard_ttl_ms"])
        # Observer age is a snapshot of staleness, NOT a measured pair gap.
        self.assertEqual(a["cm_observer_interarrival_ceiling_ms"],120)
        self.assertGreater(observer_age_ms,150)
        self.assertTrue(a["cm_observer_last_rx_derived_from_age"])
        self.assertLess(a["last_unlatched_guard_status_monotonic_sec"],
                        a["guard_tick_monotonic_sec"])
        self.assertLess(a["guard_tick_monotonic_sec"],
                        a["first_latched_guard_status_monotonic_sec"])
        self.assertLess(a["first_latched_guard_status_monotonic_sec"]-
                        a["guard_tick_monotonic_sec"],0.05)
        self.assertAlmostEqual(
            (a["cm_observer_last_rx_monotonic_sec"]-
             a["guard_last_cm_rx_monotonic_sec"])*1000,
            15.112895,places=3)
        self.assertEqual(a["cm_observer_newer_samples"],1)
        self.assertFalse(a["cm_publisher_stopped_proven"])
        self.assertFalse(a["cm_source_publication_pair_proven"])
        self.assertEqual(a["root_cause"],"UNDETERMINED")
        self.assertTrue(a["guard_fail_closed_zero"])
        self.assertFalse(a["exact_goal_cancel_accepted"])
        self.assertFalse(a["formal_timing_accepted"])
        accepted=json.loads(FIXTURE.read_text())
        self.assertTrue(accepted["scope_education_numeric_baseline_accepted"])
        self.assertFalse(accepted["intermittent_ci_guard_first_latch_root_cause_resolved"])


if __name__=="__main__":
    unittest.main()
