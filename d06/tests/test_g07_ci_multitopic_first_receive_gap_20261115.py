"""Cycle 05: actual GUI L2 #43690918618 pre-STOP multi-topic receive stall.

No ROS or Owner goal. Source-time and receive-time are distinct domains.
Regression must not downgrade the strict 150/300ms delivery gates.
"""
import json
import unittest
from pathlib import Path
from d06.live.d06_ci_multitopic_receive_gap_triage import classify

ROOT=Path(__file__).resolve().parents[2]
FIX=ROOT/"d06/tests/fixtures/g07_ci_20261115_multitopic_receive_gap_sanitized.json"
class TestG07MultiTopicReceive(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(FIX.read_text())
    def test_first_violation_is_pre_stop_odom_not_post_shutdown(self):
        v=classify(self.data)
        self.assertEqual(self.data["origin"]["public_ci_run_id"],43690918618)
        self.assertEqual(v["status"],"HOLD_MULTITOPIC_DELIVERY_GAP_RECEIPT_CANDIDATE")
        self.assertEqual(v["first_timing_channel"],"odom")
        self.assertEqual(v["first_timing_stage"],"PRE_STOP")
        self.assertAlmostEqual(v["first_timing_gap_ms"],355.881974,places=5)
        self.assertFalse(v["safety_pass"])
    def test_rmw_source_70ms_receive_377ms_is_not_cm_publish_stall(self):
        v=classify(self.data)
        self.assertAlmostEqual(v["cm_rmw_source_gap_ms"],70.891726,places=5)
        self.assertAlmostEqual(v["cm_rmw_received_gap_ms"],377.049077,places=5)
        self.assertEqual(v["cm_receive_attribution"],"RMW_RECEIVE_DELAY_CANDIDATE")
        self.assertFalse(v["cm_publisher_stopped_proven"])
        self.assertFalse(v["native_guard_latch_observed"])
        self.assertFalse(v["scheduler_or_rmw_root_cause_proven"])
        self.assertFalse(v["owner_l3_accepted"])
    def test_multiple_channels_remain_failed_and_no_fake_pass(self):
        v=classify(self.data)
        self.assertIn("source",v["over_limit_channels"])
        self.assertIn("cm",v["over_limit_channels"])
        self.assertIn("scan",v["over_limit_channels"])
        self.assertTrue(v["first_timing_violation_proven"])
        self.assertFalse(v["whole_gazebo_l2_pass"])
        self.assertFalse(v["certified_estop"])
    def test_missing_rmw_sequence_or_first_boundary_stays_hold(self):
        import copy
        for name,key in (("pair","publication_sequence_gap"),
                         ("first","channel")):
            f=copy.deepcopy(self.data)
            if name=="pair":f["first_cm_rmw_pair"].pop(key)
            else:f["first_observer_violation"].pop(key)
            with self.subTest(name=name):
                self.assertFalse(classify(f)["whole_gazebo_l2_pass"])
    def test_sanitized_fixture_privacy(self):
        raw=FIX.read_text()
        for secret in ("/home/","goal_uuid","p2-l3-owner-",".db3","AXIA_CLOUD_CI"):
            self.assertNotIn(secret,raw)
if __name__=="__main__":unittest.main()
