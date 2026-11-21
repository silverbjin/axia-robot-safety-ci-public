"""G10 native first-postGoal RMW/heartbeat join: diagnostics never release Goal."""
import unittest
from d06.diagnostic.g07_first_actual_delivery_gap import first_postgoal_reception_boundary


def native_cycle1():
    delivery = {
        "first_violation": {"channel": "odom", "current_rx_monotonic": 839.734406805,
                            "previous_rx_monotonic": 839.368603139, "gap_ms": 365.803666},
        "first_pairs": {"pre_guard": {"channel": "pre_guard",
                        "current_rx_monotonic": 839.734908249,
                        "previous_rx_monotonic": 839.370113612, "gap_ms": 364.794637}},
        "cm_rmw_first_pair": {"status": "RMW_RECEIPT_GAP_CANDIDATE",
                              "callback_gap_ms": 364.794637,
                              "rmw_source_gap_ms": 55.973048,
                              "rmw_received_gap_ms": 360.356970,
                              "rmw_publication_seq_gap": 1,
                              "same_publisher_consecutive_seq": True},
        "first_safety_observation": {"first_observed_transition": {
            "from_state": "BOOT_SAFE", "to_state": "NORMAL",
            "at_host_monotonic": 837.924096507},
            "first_observed_guard_latch_at": None},
    }
    independent = {"status": "ORIGINAL_PROCESS_RECEIPT_GAP_CANDIDATE",
                   "matched_publication_seq_gap": 1,
                   "original_source_gap_ms": 55.973048,
                   "independent_source_gap_ms": 55.973048,
                   "original_receive_gap_ms": 360.356970,
                   "independent_receive_gap_ms": 55.938737}
    io = {"first_violation": {"kind": "odom", "current_at": 839.734406805,
                             "previous_at": 839.368603139},
          "first_violation_heartbeat_coverage": True,
          "first_violation_heartbeat_count": 15,
          "first_violation_heartbeat_max_gap_ms": 21.5,
          "heartbeat_max_gap_ms": 364.989207,
          "release": "HOLD", "root_cause_proven": False}
    return delivery, independent, io


class FirstPostgoalRmwHeartbeatJoin(unittest.TestCase):
    def test_first_odom_365_and_same_cm_pair_localizes_before_callback_not_root(self):
        report = first_postgoal_reception_boundary(*native_cycle1())
        self.assertEqual(report["status"], "ORIGINAL_SUBSCRIBER_RMW_RECEPTION_GAP_OBSERVED_HOLD")
        self.assertEqual(report["first_violation_channel"], "odom")
        self.assertAlmostEqual(report["first_violation_ms"], 365.803666)
        self.assertAlmostEqual(report["original_rmw_received_gap_ms"], 360.356970)
        self.assertAlmostEqual(report["independent_rmw_received_gap_ms"], 55.938737)
        self.assertAlmostEqual(report["original_vs_independent_receive_interval_excess_ms"], 304.418233)
        self.assertEqual(report["first_observed_fsm_transition"], "BOOT_SAFE->NORMAL")
        self.assertTrue(report["first_window_heartbeat_covered"])
        self.assertAlmostEqual(report["first_window_heartbeat_max_gap_ms"], 21.5)
        self.assertFalse(report["root_cause_proven"])
        self.assertEqual(report["release"], "HOLD")
        self.assertFalse(report["owner_l3_accepted"])
        self.assertFalse(report["certified_estop"])

    def test_session_wide_heartbeat_max_not_used_as_first_window_evidence(self):
        d, ind, io = native_cycle1()
        io["heartbeat_max_gap_ms"] = 9000
        a = first_postgoal_reception_boundary(d, ind, io)
        self.assertEqual(a["status"], "ORIGINAL_SUBSCRIBER_RMW_RECEPTION_GAP_OBSERVED_HOLD")
        io["first_violation_heartbeat_coverage"] = False
        b = first_postgoal_reception_boundary(d, ind, io)
        self.assertFalse(b["first_window_heartbeat_covered"])
        self.assertIsNone(b["first_window_heartbeat_max_gap_ms"])
        self.assertFalse(b["root_cause_proven"])

    def test_wrong_first_window_or_publisher_pair_fails_closed(self):
        d, ind, io = native_cycle1()
        d["first_pairs"]["pre_guard"]["current_rx_monotonic"] += 0.1
        self.assertEqual(first_postgoal_reception_boundary(d, ind, io)["status"],
                         "FIRST_POSTGOAL_EXACT_WINDOW_UNVERIFIED_HOLD")
        d, ind, io = native_cycle1()
        ind["matched_publication_seq_gap"] = 2
        self.assertEqual(first_postgoal_reception_boundary(d, ind, io)["status"],
                         "FIRST_POSTGOAL_EXACT_CM_PAIR_UNVERIFIED_HOLD")
        d, ind, io = native_cycle1()
        ind["independent_source_gap_ms"] = 220
        self.assertEqual(first_postgoal_reception_boundary(d, ind, io)["status"],
                         "FIRST_POSTGOAL_EXACT_CM_PAIR_UNVERIFIED_HOLD")

    def test_missing_probe_cannot_derive_heartbeat_or_rename_root(self):
        d, ind, _ = native_cycle1()
        report = first_postgoal_reception_boundary(d, ind, {})
        self.assertEqual(report["status"], "FIRST_POSTGOAL_EXACT_WINDOW_UNVERIFIED_HOLD")
        self.assertFalse(report["root_cause_proven"])
        self.assertFalse(report["actual_safety_delivery_pass"])


if __name__ == "__main__":
    unittest.main()
