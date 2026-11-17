"""Cycle05 contract: actual CM input callback interval vs first RMW source gap.

Synthetic timestamps in tests, never a real Gazebo, TF or safety PASS.
"""
import unittest
from d06.live.g07_cycle05_cm_callback_window import classify


PID=4242
SRC=1700000000000000000
OFF=1800000000000000000-10000000000

def evt(name,t,handle="0xcommand",procname="collision_monit",pid=PID,vtid=303):
    return dict(name=name,timestamp_ns=int(t*1e9),callback=handle,
                vpid=pid,vtid=vtid,procname=procname)

def meta():
    return [
      dict(name="ros2:rcl_subscription_init",vpid=PID,procname="collision_monit",
           subscription_handle="0xa",topic_name="/cmd_vel_supervised"),
      dict(name="ros2:rclcpp_subscription_init",vpid=PID,procname="collision_monit",
           subscription_handle="0xa",subscription="0xb"),
      dict(name="ros2:rclcpp_subscription_callback_added",vpid=PID,procname="collision_monit",
           subscription="0xb",callback="0xcommand"),
    ]

def observer():
    return [
      dict(kind="owner_goal_published",t=11.0),
      dict(kind="pre_guard",t=12.0,rmw_source_ns=SRC,rmw_publication_seq=7),
      dict(kind="pre_guard",t=12.132,rmw_source_ns=SRC+132000000,rmw_publication_seq=8),
    ]

def anchors():
    return dict(start=dict(mono_ns=10000000000,wall_ns=1800000000000000000),
                end=dict(mono_ns=20000000000,wall_ns=1800000010000000000))


class CMFirstRmwInputCallback(unittest.TestCase):
    def test_same_cm_handle_completed_110ms_callback_inside_132ms_source_gap(self):
        trace=meta()+[evt("ros2:callback_start",12.010),
                      evt("ros2:callback_end",12.120)]
        r=classify(observer(),trace,anchors())
        self.assertEqual(r["status"],"CM_INPUT_CALLBACK_INTERVAL_OBSERVED_HYPOTHESIS_ONLY")
        self.assertAlmostEqual(r["first_cm_rmw_source_gap_ms"],132.0)
        self.assertAlmostEqual(r["max_matched_cm_cmd_callback_duration_ms"],110.0)
        self.assertGreater(r["max_callback_overlap_first_gap_ms"],100.0)
        self.assertFalse(r["tf_lookup_causality_proven"])
        self.assertFalse(r["cm120_release_pass"])

    def test_same_handle_short_callback_does_not_prove_tf_wait(self):
        trace=meta()+[evt("ros2:callback_start",12.040),
                      evt("ros2:callback_end",12.046)]
        r=classify(observer(),trace,anchors())
        self.assertEqual(r["status"],"CM_INPUT_CALLBACK_INTERVAL_OBSERVED_HYPOTHESIS_ONLY")
        self.assertLess(r["max_matched_cm_cmd_callback_duration_ms"],20.0)
        self.assertFalse(r["scheduler_causality_proven"])

    def test_missing_callback_and_clock_domain_or_rmw_seq_fail_closed(self):
        r=classify(observer(),meta(),anchors())
        self.assertEqual(r["status"],"CM_FIRST_GAP_CALLBACK_ABSENT_HOLD")
        shifted=dict(start=dict(mono_ns=10000000000,wall_ns=1800000000000000000),
                     end=dict(mono_ns=20000000000,wall_ns=1800000010100000000))
        r=classify(observer(),meta()+[evt("ros2:callback_start",12.0),
                                      evt("ros2:callback_end",12.1)],shifted)
        self.assertEqual(r["status"],"TRACE_CLOCK_ANCHOR_UNVERIFIED_HOLD")
        evs=observer()
        evs[-1]["rmw_publication_seq"]=9
        r=classify(evs,meta()+[evt("ros2:callback_start",12.0),
                              evt("ros2:callback_end",12.1)],anchors())
        self.assertEqual(r["status"],"FIRST_CM_RMW_SOURCE_PAIR_UNVERIFIED_HOLD")

if __name__=="__main__":
    unittest.main()
