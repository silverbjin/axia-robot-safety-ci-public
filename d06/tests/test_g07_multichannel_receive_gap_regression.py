"""First actual public CI GUI+Nav2 2026-11-15 43690918618 multi-channel gap.
No ROS/Gazebo or Goal. NO relaxed safety TTL and NO false CM-publisher outage.
"""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[2]
FIX=ROOT/"d06/tests/fixtures/g07_ci_43690918618_multichannel_rmw_receive_gap_sanitized.json"

class MultiChannelFirstReceiveGap(unittest.TestCase):
    def setUp(self):
        from d06.live.g07_multi_channel_receive_gap import classify
        self.classify=classify
        self.f=json.loads(FIX.read_text(encoding="utf-8"))
    def test_first_timing_boundary_is_odom_pre_stop_not_downstream_shutdown(self):
        r=self.classify(self.f)
        self.assertEqual(r["first_violation_channel"],"odom")
        self.assertEqual(r["first_violation_phase"],"PRE_STOP")
        self.assertAlmostEqual(r["first_violation_ms"],355.881974,places=5)
        self.assertEqual(r["status"],"HOLD_MULTICHANNEL_DELIVERY_BEFORE_STOP")
        self.assertFalse(r["safety_pass"])
        self.assertFalse(r["owner_l3_accepted"])
    def test_provenance_is_receive_or_observer_not_cm_source_outage(self):
        r=self.classify(self.f)
        self.assertEqual(r["cm_source_gap_ms"],70.891726)
        self.assertEqual(r["cm_receive_gap_ms"],377.049077)
        self.assertEqual(r["cm_observer_gap_ms"],383.109139)
        self.assertEqual(r["cm_publication_sequence_increment"],1)
        self.assertFalse(r["cm_publisher_stopped_proven"])
        self.assertFalse(r["observer_scheduler_root_proven"])
        self.assertEqual(r["attribution"],"RMW_RECEIVE_OR_OBSERVER_SCHEDULING_CANDIDATE")
    def test_missing_source_receive_pair_remains_unattributed_and_hold(self):
        import copy
        for key in ("first_cm_received_gap_sec","first_cm_source_gap_sec",
                    "publication_sequence_increment"):
            v=copy.deepcopy(self.f);v["cm_rmw"].pop(key)
            with self.subTest(key=key):
                r=self.classify(v)
                self.assertFalse(r["safety_pass"])
                self.assertEqual(r["attribution"],"MISSING_RMW_SOURCE_RECEIVE_PROVENANCE")
    def test_deny_acceptance_if_some_channels_exceed_safety_ttl(self):
        r=self.classify(self.f)
        self.assertEqual(set(r["violated_channels"]),set(self.f["observer_max_gap_sec"]))
        self.assertEqual(r["thresholds_sec"],self.f["original_safety_ttl_sec"])
        self.assertFalse(r["certified_estop"])
    def test_public_fixture_contains_no_private_raw_or_goal_uuid(self):
        s=FIX.read_text()
        for secret in ("/home/","goal_uuid","/tmp/tmp.","p2-l3-owner-",".db3"):
            self.assertNotIn(secret,s)

if __name__=="__main__":
    unittest.main()
