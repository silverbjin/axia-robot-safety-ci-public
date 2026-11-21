"""Actual #44865087050 first 26s native teardown role evidence fail-closed L0."""
import json
import unittest
from d06.diagnostic.g07_g25_teardown_process_boundary import assess

class G25ManagedExit(unittest.TestCase):
    def test_actual_post_nav_ack_26sec_live_launch_needs_role_not_timeout_increase(self):
        ps="PID PGID STAT COMMAND\n303 303 S /usr/bin/python3 /opt/ros/jazzy/bin/ros2 launch nav2_bringup navigation_launch.py --foo=/home/private\n305 303 Sl gz sim -s /tmp/secret/world.sdf\n308 303 Z [robot_state_publisher] <defunct>\n"
        r=assess(ps,"P2_L2_FORCED_TEARDOWN",
                 "G07_MOVING_GOAL_ORDERED_SHUTDOWN_ACK_BEFORE_SIGINT\nG07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET")
        self.assertEqual(r['status'],'POST_ACK_LAUNCH_GROUP_ALIVE_HOLD')
        self.assertEqual(r['roles'],{'gazebo_server':1,'ros2_launch':1})
        self.assertEqual(r['active_non_zombie_count'],2)
        self.assertFalse(r['root_cause_proven'])
        self.assertEqual(r['release'],'HOLD')
        self.assertNotIn('/home/private',json.dumps(r))
        self.assertNotIn('/tmp/secret',json.dumps(r))

    def test_original_artifact_missing_ps_does_not_claim_clean_exit(self):
        r=assess(None,"P2_L2_FORCED_TEARDOWN",
                 "G07_MOVING_GOAL_ORDERED_SHUTDOWN_ACK_BEFORE_SIGINT\nG07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET")
        self.assertEqual(r['status'],'TEARDOWN_PROCESS_ROLES_NOT_CAPTURED_HOLD')
        self.assertFalse(r['clean_child_exit_proven'])
        self.assertEqual(r['release'],'HOLD')

    def test_first_slow_timeout_precedes_later_supervisor_exit(self):
        r=assess("PID PGID STAT COMMAND\n",
                 "P2_L2_FORCED_TEARDOWN",
                 "CI_MOVING_GOAL_TIMEOUT_SLOW\np2_supervisor_node exit code 1\nG07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET")
        self.assertEqual(r['status'],'FIRST_SLOW_TIMEOUT_BEFORE_TEARDOWN_HOLD')
        self.assertFalse(r['root_cause_proven'])

    def test_invalid_ps_or_no_ack_is_not_cleanup_pass(self):
        r=assess("not ps\n1 1 S echo secret-data", "", "")
        self.assertEqual(r['release'],'HOLD')
        self.assertFalse(r['root_cause_proven'])
        self.assertFalse(r['clean_child_exit_proven'])

if __name__=='__main__':unittest.main()
