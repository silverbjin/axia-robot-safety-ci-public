"""Actual CI first postGoal failure classifier contracts. L0 only; no Goal or Gazebo.

Native source #44865087050 first distinct failure after STOP+Cancel+Nav/Loc ACK
is LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET. Native #44865216748's
CI_MOVING_GOAL_TIMEOUT_SLOW occurs before its later supervisor teardown error.
Keep the first boundary, not final rc, and do not release safety evidence.
"""
import unittest
from d06.diagnostic.g07_first_postgoal_boundary import classify


class FirstPostgoalBoundary(unittest.TestCase):
    def test_original_first_shutdown_after_all_safety_motion_success(self):
        rows=[
            "G07_CI_SIM_GOAL_SENT",
            "AXIA_G07_PUBLIC_CI_MOVING_CLEAR_REAL_GAZEBO_LIDAR_CM_PASS",
            "AXIA_G07_PUBLIC_CI_MOVING_SLOW_REAL_GAZEBO_LIDAR_CM_PASS",
            "AXIA_G07_PUBLIC_CI_MOVING_STOP_REAL_GAZEBO_LIDAR_CM_PASS",
            "AXIA_G07_TASK03_EXACT_GOAL_UUID_CANCELED_NATIVE_ACTION_PASS",
            "G07_NAV2_ORDERED_SHUTDOWN_ACK_LOCALIZATION_AND_NAVIGATION",
            "G07_CI_MANAGED_LAUNCH_EXIT_26S Nav2_ACK_REQUIRED",
            "G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET",
            "P2_L2_SMOKE_RC=3"
        ]
        r=classify(rows)
        self.assertEqual(r["first_postgoal_failure"],"POST_NAV_ACK_LAUNCH_PID_ALIVE_HOLD")
        self.assertEqual(r["exit_budget_s"],26)
        self.assertTrue(r["navigation_ack_before_failure"])
        self.assertEqual(r["first_safety_state_transition"],"NOT_PROVEN_FROM_LOG")
        self.assertFalse(r["root_cause_proven"])
        self.assertEqual(r["release"],"HOLD")

    def test_original_first_slow_timeout_before_secondary_supervisor_exit(self):
        rows=[
            "AXIA_G07_PUBLIC_CI_SIMULATION_ONLY_ONE_SUPERVISOR_GOAL_SENT",
            "AXIA_G07_PUBLIC_CI_MOVING_CLEAR_REAL_GAZEBO_LIDAR_CM_PASS",
            "AXIA_G07_MVP_SLOW_PHYSICAL_FIXTURE_ACK",
            "AXIA_G07_CI_MOVING_SLOW_TIMEOUT_DIAGNOSTICS max_supervised_in_slow_zone=-0.0019620272796601057 observations=96 min_front_m=0.6688",
            "AXIA_G07_PUBLIC_CI_MOVING_GOAL_BLOCKED RuntimeError:CI_MOVING_GOAL_TIMEOUT_SLOW",
            "AXIA_G07_TASK03_EXACT_GOAL_UUID_CANCELED_NATIVE_ACTION_PASS",
            "p2_supervisor_node process has died exit code 1",
            "P2_L2_SMOKE_RC=2"
        ]
        r=classify(rows)
        self.assertEqual(r["first_postgoal_failure"],"SLOW_POSITIVE_COMMAND_NOT_OBSERVED_HOLD")
        self.assertEqual(r["slow_zone_max_supervised_vx"],-0.0019620272796601057)
        self.assertEqual(r["slow_zone_samples"],96)
        self.assertEqual(r["first_safety_state_transition"],"NOT_PROVEN_FROM_LOG")
        self.assertFalse(r["root_cause_proven"])
        self.assertFalse(r["motion_acceptance_proven"])
        self.assertEqual(r["release"],"HOLD")

    def test_missing_order_or_no_first_failure_fails_closed(self):
        r=classify([
          "G07_NAV2_ORDERED_SHUTDOWN_ACK_LOCALIZATION_AND_NAVIGATION",
          "AXIA_G07_PUBLIC_CI_MOVING_STOP_REAL_GAZEBO_LIDAR_CM_PASS",
          "G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET"])
        self.assertFalse(r["navigation_ack_before_failure"])
        self.assertEqual(r["release"],"HOLD")
        self.assertFalse(r["root_cause_proven"])
        good=classify(["AXIA_G07_PUBLIC_CI_MOVING_CLEAR_REAL_GAZEBO_LIDAR_CM_PASS",
                       "AXIA_G07_PUBLIC_CI_MOVING_SLOW_REAL_GAZEBO_LIDAR_CM_PASS"])
        self.assertEqual(good["first_postgoal_failure"],"NONE_RECORDED_NOT_ACCEPTED_HOLD")
        self.assertFalse(good["motion_acceptance_proven"])

if __name__=="__main__":
    unittest.main()
