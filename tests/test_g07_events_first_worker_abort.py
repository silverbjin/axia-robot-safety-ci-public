"""Native Jazzy #44861540326 first worker exception before HEALTH timeout.

A synthetic 8-callback L1 EventsExecutor pass does not prove Nav2/TF/action
runtime. Keep the first fatal thread signal separate from final Goal timeout.
"""
import unittest
from d06.diagnostic.g07_events_first_abort import classify


class FirstActualEventsWorkerAbort(unittest.TestCase):
    def test_native_no_goal_first_worker_error_precedes_health_timeout(self):
        lines=[
            "AXIA_G07_PREGOAL_SCAN_WALL=PASS_SCOPED_RECEIVED_SCAN_ONLY",
            "AXIA_G07_MOVING_EVENTS_EXECUTOR_AB=CI_ONLY",
            "Exception in thread Thread-1 (spin):",
            "SystemError: null argument to internal routine",
            "AXIA_G07_PUBLIC_CI_MOVING_GOAL_BLOCKED RuntimeError:CI_MOVING_GOAL_TIMEOUT_HEALTH"]
        r=classify(lines)
        self.assertEqual(r["first_failure"],"EVENTS_EXECUTOR_SPIN_WORKER_EXCEPTION_HOLD")
        self.assertEqual(r["secondary_failure"],"CI_MOVING_GOAL_TIMEOUT_HEALTH")
        self.assertFalse(r["owner_l3_accepted"])
        self.assertFalse(r["root_cause_proven"])
        self.assertFalse(r["certified_estop"])
        self.assertEqual(r["release"],"HOLD")

    def test_actual_jazzy_l1_two_process_events_spin_once_systemerror_is_hard_hold(self):
        # Genuine native ROS Jazzy #44864606500, source not simulated.
        # Independent child publishes 300Hz /clock and 10Hz /scan;
        # main EventsExecutor dies inside spin_once().
        lines=[
            'File "/tmp/axia_g07_events_scan_messageinfo_l1.py", line 59',
            "File /tmp/axia_g07_events_scan_messageinfo_l1.py, line 59",
            "ex.spin_once(timeout_sec=.04)",
            "SystemError: null argument to internal routine"]
        r=classify(lines)
        self.assertEqual(r["first_failure"],
                         "JAZZY_EVENTS_EXECUTOR_L1_SYSTEMERROR_HOLD")
        self.assertTrue(r["native_l1_no_goal_reproduction"])
        self.assertFalse(r["root_cause_proven"])
        self.assertFalse(r["owner_l3_accepted"])
        self.assertFalse(r["certified_estop"])
        self.assertEqual(r["release"],"HOLD")

    def test_no_events_worker_error_does_not_grant_acceptance(self):
        for rows in ([],["AXIA_G07_MOVING_EVENTS_EXECUTOR_AB=CI_ONLY"],
                     ["RuntimeError:CI_MOVING_GOAL_TIMEOUT_HEALTH"]):
            with self.subTest(rows=rows):
                r=classify(rows)
                self.assertEqual(r["release"],"HOLD")
                self.assertFalse(r["owner_l3_accepted"])
                self.assertFalse(r["root_cause_proven"])


if __name__=="__main__":
    unittest.main()
