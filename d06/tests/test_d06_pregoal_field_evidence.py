"""Regression against non-identifying numerical evidence derived from actual WSLg SQLite.

Not a replacement for same-hardware physics or GUI acceptance. Never make
non-clear scans into a valid Goal by lowering distances/TTL.
"""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/"d06/fixtures/g07_owner_pregoal_lidar_summary_20261118.json"
STUDENT=ROOT/"student/block_B/day07/h01_runtime"
sys.path.insert(0,str(STUDENT/"tools"))
from p2_g07_owner_pregoal_l2 import diagnose_pregoal_baseline

class ActualFieldPregoalRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fact=json.loads(EVIDENCE.read_text())
        cls.stats=cls.fact["measured"]
        cls.thresholds=cls.fact["original_gate"]

    def test_real_337_scans_never_met_clear_contract(self):
        d=self.stats
        self.assertEqual(d["scans"],337)
        self.assertEqual(d["original_clear_samples"],0)
        self.assertEqual(d["near_0p40_to_0p85_fraction"]["min"],1)
        self.assertLess(d["front_m"]["max"],self.thresholds["front_strict_greater_than_m"])
        self.assertLess(d["side_m"]["max"],self.thresholds["side_strict_greater_than_m"])
        r=diagnose_pregoal_baseline(front_m=d["front_m"]["median"],
            side_m=d["side_m"]["median"],near_fraction=1.0,
            valid_beams=d["beams_per_scan"],scan_count=d["scans"])
        self.assertEqual(r["status"],"NO_GOAL_BASELINE_UNSAFE")
        self.assertEqual(r["reason"],"FRONT_AND_SIDE_NOT_CLEAR")
        self.assertFalse(r["safe_to_reposition_fixture"])
        self.assertFalse(r["goal_sent"])

    def test_actual_scan_callback_breach_is_reported_not_suppressed(self):
        d=self.stats
        self.assertGreater(d["scan_callback_max_gap_sec"],
                           self.thresholds["scan_ttl_sec"])
        self.assertEqual(d["real_goal_count"],0)
        self.assertEqual(self.fact["first_failure"],"OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE")
        self.assertTrue(self.fact["safety"]["early_collision_monitor_stop_front_polygon"])
        self.assertFalse(self.fact["safety"]["guard_latched"])

    def test_wslg_gpu_cause_not_falsely_certified(self):
        self.assertEqual(self.fact["renderer"]["backend"],"D3D12")
        self.assertFalse(self.fact["renderer"]["confirmed_sensor_causality"])
        self.assertIn("CI Linux/Xvfb not equivalent to Owner WSLg",self.fact["limitations"])

if __name__=="__main__":
    unittest.main()
