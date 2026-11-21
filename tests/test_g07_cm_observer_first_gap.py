"""Owner 1ibYCGPg exact first callback gap after RMW receipt.

Only differences of consecutive wall-monotonic and consecutive RMW received
timestamps: NEVER subtract absolute host monotonic from DDS system epoch.
No ROS, Goal, QoS, CM, or Guard modification.
"""
import json
from pathlib import Path
import unittest
from d06.diagnostic.g07_cm_observer_first_gap import classify

DATA=json.loads((Path(__file__).parent/"fixtures"/
  "g07_owner_1ibycgpg_cm_first_timing_numeric_20261121.json").read_text())

class FirstCmAfterReceiveGap(unittest.TestCase):
    def test_original_first_gap_is_post_rmw_callback_backlog_candidate_hold(self):
        r=classify(DATA)
        self.assertEqual(r["status"],"POST_RMW_OBSERVER_DELIVERY_SPACING_HOLD")
        self.assertAlmostEqual(r["cm_observer_minus_rmw_receive_delta_ms"],82.167289,places=5)
        self.assertAlmostEqual(r["supervised_observer_minus_rmw_receive_delta_ms"],74.164658,places=5)
        self.assertEqual(r["first_observer_violation_channel"],"pre_guard")
        self.assertTrue(r["first_gap_spans_goal_cancel_boundary"])
        self.assertEqual(r["observed_peer_count_over_120ms"],3)
        self.assertFalse(r["publisher_halt_proven"])
        self.assertFalse(r["executor_scheduler_cause_proven"])
        self.assertFalse(r["owner_wsl2_l3_accepted"])

    def test_pre_cancel_backlog_was_already_present(self):
        r=classify(DATA)
        self.assertAlmostEqual(r["pre_cancel_cm_observer_minus_rmw_receive_delta_ms"],61.360731,places=5)
        self.assertTrue(r["pre_cancel_backlog_candidate"])
        self.assertFalse(r["cancel_client_is_sole_cause_proven"])

    def test_true_source_130ms_and_obs_130ms_still_blocks(self):
        from copy import deepcopy
        data=deepcopy(DATA)
        q=data["first_cm_observer_breach"]["pre_guard"]
        q["observer_gap_ms"]=130.0
        q["received_gap_ms"]=131.0
        q["source_gap_ms"]=129.0
        r=classify(data)
        self.assertEqual(r["status"],"REAL_OBSERVER_120MS_BREACH_WITH_NO_BACKLOG_PROOF_HOLD")
        self.assertFalse(r["root_cause_proven"])

    def test_missing_independent_observer_data_cannot_grant_pass(self):
        r=classify({})
        self.assertEqual(r["release"],"HOLD")
        self.assertFalse(r["root_cause_proven"])
        self.assertFalse(r["certified_estop"])

if __name__=="__main__":unittest.main()
