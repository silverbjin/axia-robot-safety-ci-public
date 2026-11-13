"""First failed NAV startup classification, never use bag-zero as root cause."""
import unittest

from tools.p3_s01_startup_first_boundary import summarize

NATIVE = {"status":"REJECTED","manager":"navigation","request_sent":True,
          "elapsed_sec":1.32,"success":False}


class FirstNavLifecycleBoundaryTests(unittest.TestCase):
    def test_first_actual_startup_error_not_shutdown_noise(self):
        trace = """[INFO] [lifecycle_manager_navigation]: Starting bringup
[ERROR] [collision_monitor]: Failed to configure: scan source invalid
[ERROR] [lifecycle_manager_navigation]: Failed to bring up all requested nodes
[INFO] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[ERROR] [other]: shutdown teardown error
"""
        s = summarize(trace, NATIVE)
        self.assertEqual(s["first_failure_stage"], "NAVIGATION_START")
        self.assertEqual(s["native_status"], "REJECTED")
        self.assertEqual(s["first_error_line"], 2)
        self.assertEqual(s["first_error_node"], "collision_monitor")
        self.assertEqual(s["first_error_class"], "NODE_CONFIGURE_FAILURE")

    def test_bag_zero_is_not_root_cause(self):
        trace = """[ERROR] [planner_server]: Failed to activate
[INFO] bag contains zero /cmd_vel_pre_guard
"""
        s = summarize(trace, NATIVE)
        self.assertEqual(s["first_error_class"], "NODE_ACTIVATION_FAILURE")
        self.assertFalse(s["goal_sent"])
        self.assertFalse(s["raw_safety_behavior_accepted"])

    def test_rejected_with_no_observed_error_is_unresolved(self):
        s = summarize("[INFO] still starting\n", NATIVE)
        self.assertEqual(s["first_error_class"], "UNKNOWN_FIRST_NAV_ERROR")
        self.assertEqual(s["first_error_line"], None)

    def test_timeout_is_distinct_from_rejected(self):
        s = summarize("no diagnostic\n", dict(NATIVE,status="SERVICE_TIMEOUT"))
        self.assertEqual(s["native_status"], "SERVICE_TIMEOUT")
        self.assertEqual(s["first_error_class"], "UNKNOWN_FIRST_NAV_ERROR")

    def test_output_is_redacted_and_never_contains_private_paths(self):
        trace = "[ERROR] [bt_navigator]: Failed to configure /home/jinho/private/TOKEN=secret\n"
        s = summarize(trace, NATIVE)
        self.assertNotIn("jinho", repr(s))
        self.assertNotIn("secret", repr(s))
        self.assertNotIn("/home/", repr(s))
        self.assertEqual(s["first_error_node"], "bt_navigator")

    def test_cleanup_only_cannot_forge_earlier_startup_issue(self):
        trace = """[INFO] nav2 nodes initializing
[INFO] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[ERROR] [collision_monitor]: Failed to cleanup
"""
        s = summarize(trace, NATIVE)
        self.assertEqual(s["first_error_class"], "UNKNOWN_FIRST_NAV_ERROR")
        self.assertTrue(s["cleanup_started_before_error"])

    def test_manager_ack_does_not_appear_as_failure(self):
        s = summarize("[INFO] started\n", dict(NATIVE,status="ACK",success=True))
        self.assertEqual(s["first_failure_stage"], "NO_NAV_FAILURE_CONFIRMED")


if __name__ == "__main__":
    unittest.main()
