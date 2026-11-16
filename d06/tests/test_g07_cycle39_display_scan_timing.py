"""G07 Cycle39: scoped display, LaserScan geometry and independent timing contracts.

NO ROS/NAV2/GOAL in these tests. Actual world/scan/TF remain UNVERIFIED until
captured in one timestamp-aligned real Gazebo run.
"""
from __future__ import annotations
import math
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
RVIZ = ROOT / "rviz" / "d06_safety_bubble.rviz"
MONITOR = ROOT / "live" / "d06_readonly_monitor.py"
GEOM = ROOT / "live" / "g07_cycle39_scan_geometry.py"
TIMING = ROOT / "live" / "g07_cycle39_scan_timing.py"


class DisplayOnly(unittest.TestCase):
    def test_rviz_readable_without_taking_robot_control(self):
        content = RVIZ.read_text(encoding="utf-8")
        self.assertIn("Name: Raw LaserScan", content)
        self.assertIn("Value: /scan", content)
        self.assertIn("Fixed Frame: odom", content)
        self.assertIn("Target Frame: base_footprint", content)
        self.assertIn("Name: RobotModel\n      Enabled: false", content)
        self.assertIn("Show Arrows: false", content)
        self.assertIn("Class: rviz_default_plugins/TF", content)


class ScanAngles(unittest.TestCase):
    @staticmethod
    def scan(amin, inc, n=360, first=math.inf, last=math.inf):
        r = [math.inf] * n
        r[0], r[-1] = first, last
        return SimpleNamespace(angle_min=amin, angle_increment=inc,
                               ranges=r, range_min=0.12, range_max=20.0)

    def test_wraparound_front_samples_from_0_to_2pi(self):
        front = runpy.run_path(str(MONITOR))["front_distance"]
        scan = self.scan(0.0, 2 * math.pi / 360, first=1.8, last=0.45)
        self.assertAlmostEqual(front(scan), 0.45)

    def test_negative_pi_style_front_still_correct(self):
        front = runpy.run_path(str(MONITOR))["front_distance"]
        scan = self.scan(-math.pi, 2 * math.pi / 360, first=1.8, last=0.45)
        self.assertIsNone(front(scan))

    def test_unknown_readings_not_reported_as_clear(self):
        front = runpy.run_path(str(MONITOR))["front_distance"]
        self.assertIsNone(front(self.scan(0.0, 2 * math.pi / 360)))


class WorldVsScanGeometry(unittest.TestCase):
    def test_synthetic_cylinder_hit_and_bad_reading(self):
        compare = runpy.run_path(str(GEOM))["compare_cylinder_hit"]
        scan = {"frame_id": "base_scan", "stamp_s": 7.5,
                "angle_min": 0.0, "angle_increment": math.pi/180,
                "ranges": [0.5]+[20.0]*359}
        pose = {"frame_id": "base_scan", "stamp_s": 7.5,
                "x": 0.0, "y": 0.0, "yaw": 0.0, "z": 0.15}
        obstacle = {"x": 0.6, "y": 0.0, "radius": 0.1, "z_min": 0.0, "z_max": 0.48}
        self.assertEqual(compare(scan, pose, obstacle)["status"], "CONSISTENT_CYLINDER_HIT")
        scan["ranges"][0] = 1.0
        self.assertEqual(compare(scan, pose, obstacle)["status"], "NOT_MATCHED_NEEDS_SCENE_REVIEW")

    def test_missing_pose_is_unverified_not_success(self):
        compare = runpy.run_path(str(GEOM))["compare_cylinder_hit"]
        self.assertEqual(compare({"frame_id": "base_scan", "stamp_s": 7.5}, None,
                                 {"x": 0.6})["status"], "UNVERIFIED")


class TimingProvenance(unittest.TestCase):
    def test_observer_410ms_without_source_stamps_is_not_ttl_breach(self):
        classify = runpy.run_path(str(TIMING))["classify_scan_periods"]
        obs = classify(observer_gap_wall_s=0.4107)
        self.assertEqual(obs["status"], "OBSERVER_ONLY_UNATTRIBUTED")
        self.assertFalse(obs["safety_ttl_breach_proven"])

    def test_upstream_proven_violation_is_separate_from_observer(self):
        classify = runpy.run_path(str(TIMING))["classify_scan_periods"]
        result = classify(observer_gap_wall_s=0.4107,
                          source_gap_wall_s=0.33, bridge_gap_wall_s=0.34,
                          supervisor_gap_wall_s=0.36, comparable_clock=True)
        self.assertEqual(result["status"], "SOURCE_DELIVERY_GAP_OVER_300MS")
        self.assertTrue(result["safety_ttl_breach_proven"])

    def test_clock_mismatch_cannot_be_promoted_to_pass(self):
        classify = runpy.run_path(str(TIMING))["classify_scan_periods"]
        result = classify(observer_gap_wall_s=0.41, source_gap_wall_s=0.10,
                          bridge_gap_wall_s=0.1, supervisor_gap_wall_s=0.1,
                          comparable_clock=False)
        self.assertEqual(result["status"], "CLOCK_DOMAINS_UNVERIFIED")
        self.assertFalse(result["safety_ttl_breach_proven"])


if __name__ == "__main__":
    unittest.main()
