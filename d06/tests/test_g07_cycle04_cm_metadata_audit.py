"""Cycle04 TDD: exact configured official CM subscriptions only, no ROS/Goal.

Old Cycle31 resolver remains unchanged. Raw handles never leave memory/logs.
"""
import unittest
from d06.live.g07_cycle04_cm_metadata_audit import classify


def ev(name,pid=4242,proc="collision_monit",**fields):
    return dict(name=name,vpid=pid,procname=proc,**fields)


def good(pid=4242,proc="collision_monit"):
    return [
      ev("ros2:rcl_subscription_init",pid,proc,subscription_handle="0xrcl1",
         topic_name="/cmd_vel_supervised"),
      ev("ros2:rclcpp_subscription_init",pid,proc,
         subscription_handle="0xrcl1",subscription="0xsub1"),
      ev("ros2:rclcpp_subscription_callback_added",pid,proc,
         subscription="0xsub1",callback="0xopaque"),
    ]


class OfficialCMMetadata(unittest.TestCase):
    def test_exact_owned_live_cm_topic_chain_is_identified_without_raw_handles(self):
        r=classify(good()+[
            ev("ros2:rcl_subscription_init",7654,"other_node",
               topic_name="/scan",subscription_handle="0xother")])
        self.assertEqual(r["status"],"CM_INPUT_CALLBACK_HANDLE_IDENTIFIED_NO_GOAL")
        self.assertEqual(r["linked_cmd_vel_callback_handles"],1)
        self.assertEqual(r["owned_cm_process_count"],1)
        self.assertFalse(r["cm_callback_duration_proven"])
        self.assertFalse(r["goal_sent"])
        self.assertNotIn("0xopaque",str(r))
        self.assertNotIn("4242",str(r))

    def test_second_readonly_observer_of_same_topic_is_not_second_cm(self):
        r=classify(good()+[
            ev("ros2:rcl_subscription_init",7654,"other_node",
               topic_name="/cmd_vel_supervised",subscription_handle="0xobserver")])
        self.assertEqual(r["status"],"CM_INPUT_CALLBACK_HANDLE_IDENTIFIED_NO_GOAL")
        self.assertEqual(r["owned_cm_process_count"],1)

    def test_duplicate_cm_process_and_invalid_metadata_fail_closed(self):
        r=classify(good()+good(pid=4243))
        self.assertEqual(r["status"],"CM_MULTIPLE_CMD_SUBSCRIPTION_PROCESSES_HOLD")
        self.assertFalse(r["ready_for_moving_goal"])
        r=classify(good()[:2])
        self.assertEqual(r["status"],"CM_INPUT_CALLBACK_LINK_MISSING_HOLD")

    def test_topic_in_wrong_process_name_never_authorizes_goal(self):
        r=classify(good(proc="rviz2"))
        self.assertEqual(r["status"],"CM_CMD_TOPIC_OWNER_UNVERIFIED_HOLD")
        self.assertFalse(r["ready_for_moving_goal"])


if __name__=="__main__":
    unittest.main()
