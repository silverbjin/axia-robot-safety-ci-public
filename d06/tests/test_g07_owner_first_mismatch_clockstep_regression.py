"""Cycle03 public regression from real Owner sanitized evidence: no ROS, Goal or instructor code.
Clock-source step != actual monotonic packet dropout; first safety latch != CM TTL.
"""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[2]
FIX=ROOT/"d06/tests/fixtures/g07_owner_20261115_cm_supervisor_mismatch_clockstep_sanitized.json"

class G07FirstMismatch(unittest.TestCase):
    def setUp(self):
        from d06.live.d06_guard_first_mismatch_triage import inspect
        self.inspect=inspect
        self.f=json.loads(FIX.read_text(encoding="utf-8"))
    def test_real_first_latch_is_persistent_mismatch_not_cm_ttl(self):
        got=self.inspect(self.f)
        self.assertEqual(got["status"],"HOLD_CM_SUPERVISOR_RECONCILIATION_EXPIRED")
        self.assertEqual(got["first_safety_transition"],"CM_EXCEEDS_SUPERVISOR")
        self.assertAlmostEqual(got["reconciliation_elapsed_ms"],125.424570,places=5)
        self.assertLess(got["cm_age_ms"],150)
        self.assertLess(got["supervisor_age_ms"],500)
        self.assertGreater(got["cm_linear_x"],got["supervisor_linear_x"])
        self.assertEqual(got["last_emitted"],"ZERO")
        self.assertFalse(got["ttl_violation_proven"])
        self.assertFalse(got["safety_pass"])
    def test_common_source_clock_jump_not_asserted_cm_no_publish(self):
        got=self.inspect(self.f)
        self.assertEqual(got["clock_domain_status"],"HOST_SYSTEM_CLOCK_STEP_CANDIDATE")
        self.assertAlmostEqual(got["rmw_cm_source_jump_ms"],1470.056234,places=4)
        self.assertAlmostEqual(got["cm_observer_monotonic_gap_ms"],53.606801,places=4)
        self.assertFalse(got["cm_publisher_stopped_proven"])
        self.assertFalse(got["clock_step_root_cause_proven"])
        self.assertFalse(got["safety_pass"])
    def test_no_automatic_acceptance_when_latch_or_clock_unverified(self):
        import copy
        f=copy.deepcopy(self.f)
        for k in ("reconciliation_since_mono","first_latch_tick_mono","last_emitted"):
            alt=copy.deepcopy(f);alt["guard_first_latch"].pop(k)
            with self.subTest(missing=k):
                self.assertFalse(self.inspect(alt)["safety_pass"])
        self.assertFalse(self.inspect(self.f)["owner_l3_accepted"])
    def test_privacy_fixture_contains_no_original_path_or_goal_uuid(self):
        s=FIX.read_text(encoding="utf-8")
        for secret in ("/home/","goal_uuid","/tmp/tmp.","p2-l3-owner-","rosbag2_0.db3","YES-P2-G07-GOAL"):
            self.assertNotIn(secret,s)
if __name__=="__main__":unittest.main()
