"""G25 real no-goal Native: first error BEFORE final 10s launch teardown."""
import unittest
from d06.diagnostic.g07_g25_nogoal_first_stage import first_failure

class G25FirstStage(unittest.TestCase):
    def test_earlier_real_lifecycle_startup_error_wins_over_final_teardown(self):
        log=("P2_NO_GOAL_BLOCKED: see staged_startup.log/launch.log\n"
             "G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET\nP2_L2_SMOKE_RC=3")
        r=first_failure(log,role_status="TEARDOWN_PROCESS_ROLES_NOT_CAPTURED_HOLD")
        self.assertEqual(r["status"],"STARTUP_BLOCKED_BEFORE_TEARDOWN_HOLD")
        self.assertFalse(r["root_cause_proven"])
        self.assertEqual(r["release"],"HOLD")
    def test_ack_then_launch_liveness_has_separate_first_failure(self):
        log=("G07_SHUTDOWN_L2_NO_GOAL REAL_CM_ACTIVE_BEFORE_SHUTDOWN\n"
             "G07_REAL_NAV2_ORDERED_SHUTDOWN_ACK_BEFORE_SIGINT\n"
             "G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET\nP2_L2_SMOKE_RC=3")
        r=first_failure(log,role_status="POST_ACK_LAUNCH_GROUP_ALIVE_HOLD")
        self.assertEqual(r["status"],"POST_ACK_LAUNCH_LIVENESS_TIMEOUT_HOLD")
        self.assertFalse(r["clean_exit_proven"])
    def test_incomplete_log_does_not_infer_root_from_terminal_marker(self):
        r=first_failure("G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET",role_status=None)
        self.assertEqual(r["status"],"EARLY_SHUTDOWN_STAGE_UNVERIFIED_HOLD")
    def test_no_goal_sanity_not_acceptance(self):
        r=first_failure("G07_SHUTDOWN_L2_NO_GOAL REAL_CM_ACTIVE_BEFORE_SHUTDOWN",role_status=None)
        self.assertEqual(r["release"],"HOLD")
        self.assertFalse(r["certified_estop"])
        self.assertFalse(r["moving_goal_two_cycle_pass"])
        self.assertEqual(r["status"],"NO_GOAL_SHUTDOWN_INCOMPLETE_HOLD")
if __name__=="__main__":unittest.main()
