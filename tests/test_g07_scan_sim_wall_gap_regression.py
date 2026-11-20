"""Numerical contract for first e96rL7BT /scan wall violation (ROS-free).

Raw field TAR was not mounted in this session; the fixture records the user's
SHA-verified measurements, not a newly extracted claim.
"""
import json
from pathlib import Path
import unittest
from d06.diagnostic.g07_scan_sim_wall_gap import assess_first_scan_wall_gap

FIXTURE=Path(__file__).parent/"fixtures/g07_wsl2_first_scan_wall_gap_20261120.json"

class ScanFirstWallGap(unittest.TestCase):
    def sample(self):
        return json.loads(FIXTURE.read_text())

    def test_actual_independent_bag_and_oracle_wall_breach_is_hold(self):
        report=assess_first_scan_wall_gap(self.sample())
        self.assertEqual(report["status"],"SCAN_WALL_300_VIOLATION_HOLD")
        self.assertAlmostEqual(report["first_gap_ms"],317.942691,places=5)
        self.assertAlmostEqual(report["scan_header_sim_gap_ms"],102.0,places=5)
        self.assertFalse(report["oracle_only_observer_stall_supported"])
        self.assertFalse(report["cause_proven"])
        self.assertEqual(report["root_cause"],"CAUSE_UNDETERMINED")
        self.assertEqual(report["release"],"HOLD")
        self.assertFalse(report["certified_estop"])
        self.assertEqual(report["native_publish_boundary"],"NOT_MEASURED")
        self.assertGreater(report["rosbag_scan_gap_ms"],300)
        self.assertGreater(report["rosbag_safety_gap_ms"],300)
        self.assertIsNotNone(report["rtf_window_estimate"])
        self.assertEqual(report["owner_wsl2_l3"],"BLOCKED")

    def test_sim_102ms_does_not_imply_wall_300ms_pass(self):
        d=self.sample()
        d["oracle_first_gap_ms"]=270.0
        d["oracle_now_monotonic_s"]=d["oracle_prev_monotonic_s"]+.270
        d["rosbag_scan_receive_gap_ms"]=322.262
        report=assess_first_scan_wall_gap(d)
        self.assertEqual(report["release"],"HOLD")
        self.assertFalse(report["scan_wall_300_pass"])

    def test_oracle_only_candidate_requires_independent_rosbag_healthy(self):
        d=self.sample()
        d["rosbag_scan_receive_gap_ms"]=105.0
        d["rosbag_safety_scan_receive_gap_ms"]=106.0
        report=assess_first_scan_wall_gap(d)
        self.assertEqual(report["origin_candidate"],"ORACLE_ONLY_CALLBACK_STALL_CANDIDATE")
        self.assertFalse(report["cause_proven"])

    def test_native_publish_missing_forbids_bridge_attribution(self):
        report=assess_first_scan_wall_gap(self.sample())
        self.assertNotIn(report["origin_candidate"],
                         {"GAZEBO_GENERATION_CONFIRMED","ROS_GZ_BRIDGE_CONFIRMED"})
        self.assertFalse(report["gazebo_bridge_delay_proven"])

    def test_invalid_or_mismatched_pairs_fail_closed(self):
        d=self.sample()
        d["same_laserscan_pair"]=False
        self.assertEqual(assess_first_scan_wall_gap(d)["release"],"HOLD")
        d=self.sample()
        d["scan_header_sim_now_s"]=float("nan")
        self.assertEqual(assess_first_scan_wall_gap(d)["status"],
                         "SCAN_FIRST_PAIR_UNVERIFIED_HOLD")

if __name__=="__main__":
    unittest.main()
