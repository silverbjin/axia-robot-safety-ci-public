"""Actual failed pregoal L2 must publish only bounded numeric first gap."""
import unittest
from pathlib import Path

FLOW=Path(__file__).resolve().parents[1]/".github/workflows/axia-g07-fv17-owner-evidence-parity-native-l2.yml"

class FirstPregoalArtifactContract(unittest.TestCase):
    def test_actual_no_goal_scan_hold_is_retained_when_runner_exits_nonzero(self):
        flow=FLOW.read_text()
        self.assertIn("if: always()",flow)
        self.assertIn("first_scan_pregoal_boundary.json",flow)
        self.assertIn("AXIA_G07_SCAN_PREFLIGHT_FIRST_BOUNDARY_RECORDED",flow)
        self.assertIn("first_scan_timing_boundary",flow)
        # #44773940465 Cycle1 /clock334.226 + /odom335.862 wall:
        # previous exporter dropped this earliest global event entirely.
        self.assertIn('"first_delivery_violation","topic_results"',flow)
        self.assertIn('"clock_max_wall_gap_ms"',flow)
        self.assertIn('"odom_max_wall_gap_ms"',flow)
        self.assertIn('first_delivery_violation',flow)
        self.assertIn("local_window_rtf_estimate",flow)
        self.assertIn("scan_generation_vs_bridge_root_cause",flow)
        self.assertIn("goal_sent",flow)
        self.assertIn("first_nav_server_boundary.json",flow)
        self.assertIn("g07_nav_shutdown_first_server_boundary.py",flow)
        self.assertNotIn("public_evidence/rosbag2",flow)

if __name__=="__main__":unittest.main()
