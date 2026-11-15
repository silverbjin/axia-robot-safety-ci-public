"""#43676794777 sanitized first-boundary regression; NO ROS, Goal, or private raw.

Separate from cWID Owner first latch and #43674784552 P4 successful SHA.
Tests use D06's existing read-only analyzers, not a second G07 controller.
"""
import json
import unittest
from pathlib import Path

from d06.live.d06_sensor_rmw_first_delivery import analyze_delivery
from d06.live.d06_native_guard_vs_observer import inspect_native_guard
from d06.live.d06_guard_cm_first_latch_join import analyze_first_latch

ROOT = Path(__file__).resolve().parents[2]
CI = json.loads((ROOT / "d06/tests/fixtures/g07_ci_20261115_first_162ms_no_latch_sanitized.json").read_text())
OWNER = json.loads((ROOT / "d06/tests/fixtures/g07_owner_20261115_second_cm_publication_gap_sanitized.json").read_text())

def _pre_guard(t, source_ns, received_ns, seq):
    return {"kind":"pre_guard", "t":t, "rmw_source_ns":source_ns,
            "rmw_received_ns":received_ns, "rmw_publication_seq":seq}

def _guard(t, cm_count, windows, latched=False):
    return {"kind":"guard", "t":t,
            "data":{"latched":latched,
                    "native_input_timing":{
                        "schema":"axia.g07.guard_native_callback_intervals_v1",
                        "cm_callback_gaps_over_150ms":cm_count,
                        "supervisor_callback_gaps_over_150ms":0,
                        "cm_gap_windows":windows,
                        "supervisor_gap_windows":[]}}}

class UnifiedG07FirstBoundary(unittest.TestCase):
    def test_same_run_162ms_source_and_native_guard_both_fail_without_latch(self):
        e = CI["first_cm_consecutive_publication_window"]
        native = CI["native_guard_direct_input"]
        self.assertEqual(CI["origin"]["public_actions_run_id"],43676794777)
        self.assertEqual(CI["origin"]["private_instructor_source_sha"],
                         "6e402e30f5036285f067b5dffed085eff41af599")
        self.assertEqual(e["publication_sequence_increment"],1)
        self.assertEqual(e["upstream_supervisor_publications_within_gap"],3)
        self.assertLess(e["upstream_supervisor_max_source_gap_ms"],150)
        # Synthetic timestamps preserve only REAL measured pair differences:
        # never compare RMW SYSTEM epoch directly with Guard monotonic time.
        a=_pre_guard(10.15,100000000000,100000050000,101)
        b=_pre_guard(10.15+e["observer_callback_gap_ms"]/1000,
                     a["rmw_source_ns"]+round(e["source_gap_ms"]*1e6),
                     a["rmw_received_ns"]+round(e["received_gap_ms"]*1e6),102)
        r=analyze_delivery([{"kind":"owner_goal_published","t":10.0},a,b])
        self.assertEqual(r["first_boundary"]["classification"],"PUBLISH_SOURCE_GAP")
        self.assertAlmostEqual(r["first_boundary"]["source_gap_ms"],162.259185,places=4)
        self.assertAlmostEqual(r["first_boundary"]["received_gap_ms"],162.437463,places=4)
        self.assertAlmostEqual(r["first_boundary"]["callback_gap_ms"],159.804555,places=4)
        self.assertFalse(r["safety_pass"])
        duration=native["goal_scoped_callback_gap_ms"]/1000
        cm_window=[{"start_mono":10.2, "end_mono":10.2+duration, "gap_sec":duration}]
        observed=inspect_native_guard([
            _guard(9.9,0,[]),
            {"kind":"owner_goal_published","t":10.0},
            _guard(10.45,1,cm_window,latched=False)
        ],active_end=10.5)
        self.assertEqual(observed["status"],"HOLD_NATIVE_GUARD_CM_INPUT_GAP_150MS")
        self.assertAlmostEqual(observed["native_cm_callback_max_gap_ms"],162.494,places=3)
        self.assertEqual(observed["native_cm_goal_scoped_gap_count"],1)
        self.assertFalse(observed["native_guard_latch_observed"])
        self.assertFalse(observed["safety_pass"])
        self.assertFalse(observed["owner_l3_accepted"])
        self.assertFalse(native["native_guard_latch_observed"])

    def test_distinct_owner_post_latch_pair_is_right_censored_not_safe(self):
        self.assertEqual(OWNER["first_guard_latch"]["measured_age_ms"],169.168036)
        r=analyze_first_latch(OWNER)
        self.assertEqual(r["status"],"HOLD_CM_SOURCE_GAP_WITH_FIRST_GUARD_LATCH")
        self.assertTrue(r["pre_latch_cm_observer_evidence_right_censored"])
        self.assertEqual(OWNER["observation_window"]["first_pre_latch_observer_violation"],None)
        self.assertAlmostEqual(r["cm_source_gap_ms"],184.414666,places=4)
        self.assertEqual(r["supervisor_publications_inside_cm_gap"],4)
        self.assertEqual(r["first_safety_transition"],"UPSTREAM_STALE_AFTER_MOTION")
        self.assertFalse(r["safety_pass"])
        self.assertFalse(r["owner_l3_accepted"])

    def test_prior_separate_ci_receive_delay_never_proves_source_or_guard_stall(self):
        a=_pre_guard(2.0,100000000000,100000050000,31)
        b=_pre_guard(2.397164783,
                     a["rmw_source_ns"]+round(69.596117*1e6),
                     a["rmw_received_ns"]+round(393.579510*1e6),32)
        r=analyze_delivery([{"kind":"owner_goal_published","t":1.0},a,b])
        self.assertEqual(r["first_boundary"]["classification"],"RMW_RECEIVE_GAP")
        self.assertAlmostEqual(r["first_boundary"]["source_gap_ms"],69.596117,places=3)
        self.assertFalse(r["guard_received_same_delay_proven"])
        self.assertFalse(r["safety_pass"])

    def test_fixture_privacy_and_no_acceptance_authority(self):
        s=(ROOT / "d06/tests/fixtures/g07_ci_20261115_first_162ms_no_latch_sanitized.json").read_text()
        for forbidden in ("/home/", "p2-l3-owner-", "rosbag2_0.db3",
                          "YES-P2-G07-GOAL", "AXIA_CLOUD_CI", "goal_uuid"):
            self.assertNotIn(forbidden,s)
        self.assertFalse(CI["result"]["safety_pass"])
        self.assertFalse(CI["result"]["owner_l3_accepted"])
        self.assertFalse(CI["result"]["certified_estop"])

if __name__=="__main__":
    unittest.main()
