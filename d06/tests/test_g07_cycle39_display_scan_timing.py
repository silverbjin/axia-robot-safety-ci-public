"""Cycle39 MVP freeze: only read-only RViz presentation and front LaserScan wrap.

No ROS imports, no Nav2, no Gazebo and no Goal in this L0 suite.
Old Cycle38 source must RED on RViz arrows and 0..2pi front wrap.
"""
import math
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
RVIZ = ROOT / "rviz" / "d06_safety_bubble.rviz"
MONITOR = ROOT / "live" / "d06_readonly_monitor.py"


class Cycle39ScopedMvp(unittest.TestCase):
    def test_rviz_clarity_preserves_readonly_frame_and_scan(self):
        s = RVIZ.read_text(encoding="utf-8")
        for required in ("Name: Raw LaserScan", "Value: /scan",
                         "Fixed Frame: odom", "Target Frame: base_footprint",
                         "Name: RobotModel\n      Enabled: false",
                         "Show Arrows: false"):
            self.assertIn(required, s)

    @staticmethod
    def scan(amin=0.0, n=360, first=math.inf, last=math.inf):
        ranges = [math.inf] * n
        ranges[0], ranges[-1] = first, last
        return SimpleNamespace(angle_min=amin,
                               angle_increment=2 * math.pi / n,
                               ranges=ranges, range_min=0.12, range_max=20.0)

    def test_front_wrap_includes_both_sides_of_2pi(self):
        front = runpy.run_path(str(MONITOR))["front_distance"]
        self.assertAlmostEqual(front(self.scan(first=1.8, last=0.45)), 0.45)

    def test_invalid_scan_stays_unknown(self):
        f = runpy.run_path(str(MONITOR))
        self.assertIsNone(f["front_distance"](self.scan()))
        self.assertEqual(f["annotated_zone"](None, 0.01), "UNKNOWN")

    def test_monitor_publishes_only_educational_markers(self):
        s = MONITOR.read_text(encoding="utf-8")
        self.assertIn('node.create_publisher(MarkerArray, "/axia/d06/rviz/bubble", 5)', s)
        self.assertEqual(s.count("node.create_publisher("), 1)
        self.assertNotIn("ros2 action send_goal", s)
        self.assertNotIn('create_publisher(Twist, "/cmd_vel"', s)


if __name__ == "__main__":
    unittest.main()
