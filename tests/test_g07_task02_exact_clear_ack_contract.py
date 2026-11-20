"""Reuse exact core Moving Goal CLEAR-before-action-ACK constraint.

Read-only Task02 diagnostic must not contradict the already strict real Goal
oracle, but may never infer execution from a transient/unknown action status.
"""
import unittest
from d06.diagnostic.g07_task02_strict_gate import assess

def evidence(clear=None,before=True,later=True,slow=2,stop=2):
    data=dict(schema="axia_g07_public_ci_moving_goal_v1",
        status="CI_GAZEBO_MOVING_GOAL_CANDIDATE",
        guard_latched=False,real_gazebo_world=True,actual_physical_scan=True,
        native_obstacle_set_pose_ack=True,stop_native_set_pose_ack=True,
        odom_stopped_dwell_sec=1.02,observed_odom_moved_m=.13,
        goal_status_at_clear=clear,goal_status_at_slow=slow,goal_status_at_stop=stop,
        clear_before_action_ack=before,same_goal_executing_after_clear=later,
        max_source_interval_sec=.07,max_cm_interval_sec=.07,max_guard_interval_sec=.07,
        max_scan_interval_sec=.22,max_odom_interval_sec=.14,
        max_clock_interval_sec=.11)
    events=[{"kind":"owner_goal_published","t":1.0}]
    events.extend({"kind":"pre_guard","t":1.1+i*.05,
                   "rmw_source_ns":1_000_000_000+i*50_000_000,
                   "rmw_publication_seq":i} for i in range(18))
    return data,events

class ExactCoreClearStatusParity(unittest.TestCase):
    def test_clear_before_ack_with_later_same_goal_execution_is_valid_candidate(self):
        report,events=evidence(clear=None,before=True,later=True)
        actual=assess(report,events)
        self.assertEqual(actual["status"],"TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")
        self.assertFalse(actual["tracer_off_release_pass"])

    def test_no_later_same_goal_execution_remains_hard_hold(self):
        report,events=evidence(clear=None,before=True,later=False)
        self.assertEqual(assess(report,events)["status"],
                         "TASK02_NAV2_GOAL_EXECUTING_STAGES_UNVERIFIED_HOLD")

    def test_clear_unknown_without_preack_marker_remains_hold(self):
        report,events=evidence(clear=None,before=False,later=True)
        self.assertEqual(assess(report,events)["status"],
                         "TASK02_NAV2_GOAL_EXECUTING_STAGES_UNVERIFIED_HOLD")

    def test_slow_or_stop_unconfirmed_remains_hard_hold(self):
        for slow,stop in ((1,2),(2,None)):
            report,events=evidence(clear=None,before=True,later=True,
                                   slow=slow,stop=stop)
            self.assertEqual(assess(report,events)["status"],
                             "TASK02_NAV2_GOAL_EXECUTING_STAGES_UNVERIFIED_HOLD")

    def test_normal_clear_goal_executing_still_valid(self):
        report,events=evidence(clear=2,before=False,later=False)
        self.assertEqual(assess(report,events)["status"],
                         "TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")

if __name__=="__main__":unittest.main()
