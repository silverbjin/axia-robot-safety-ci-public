"""Cycle31 RED: official Jazzy LTTng CM callback is not named cmdVel.

Actual L2 #43812555906: 817 CM metadata events, 849 callback events,
30 registered callbacks, zero 'cmdvel' symbols; one 113.649ms callback
could not be linked to the subscribed '/cmd_vel_supervised' input.

The authoritative mapping is:
rcl_subscription_init(subscription_handle,topic_name)
-> rclcpp_subscription_init(subscription_handle,subscription)
-> rclcpp_subscription_callback_added(subscription,callback)
-> callback_start/end(callback,vpid,vtid).
No ROS/Gazebo/Goal/WSL2 or private traces in public tests.
"""
from __future__ import annotations
import unittest
from d06.live.g07_cycle31_cm_topic_callback_identity import resolve_cm_cmdvel_handles
from d06.live.g07_cycle30_bounded_cm_trace import select_cm_first_window
from d06.live.g07_cycle29_first_cm_callback_trace import classify_callback_gap
from d06.tests.test_g07_cycle29_first_cm_callback_trace import original,CM,WALL_OFFSET

ANCHORS=original()[2]
A={"t":10.0,"rmw_source_ns":1_700_000_100_000_000_000,"rmw_publication_seq":10}
B={"t":10.162,"rmw_source_ns":1_700_000_100_156_345_327,"rmw_publication_seq":11}
def ev(name,t,*,pid=CM,**fields):
    return {"name":name,"vpid":pid,"vtid":pid+1,
            "timestamp_ns":round(t*1e9)+WALL_OFFSET,**fields}
def mapped(topic="/cmd_vel_supervised",callback="cmd",pid=CM):
    return [
      ev("ros2:rcl_subscription_init",9.3,pid=pid,
         subscription_handle="0xrcl1",topic_name=topic),
      ev("ros2:rclcpp_subscription_init",9.31,pid=pid,
         subscription_handle="0xrcl1",subscription="0xsub1"),
      ev("ros2:rclcpp_subscription_callback_added",9.32,pid=pid,
         subscription="0xsub1",callback=callback),
      ev("ros2:rclcpp_callback_register",9.33,pid=pid,
         callback=callback,symbol="std::_Bind<opaque_wrapped_callback>"),
      ev("ros2:callback_start",10.010,pid=pid,callback=callback),
      ev("ros2:callback_end",10.157,pid=pid,callback=callback),
    ]
class Cycle31TopicToCallback(unittest.TestCase):
    def test_strict_topic_chain_resolves_opaque_callback_not_name_heuristic(self):
        rows=mapped()
        handles,counts=resolve_cm_cmdvel_handles(rows,cm_pid=CM)
        self.assertEqual(handles,{"cmd"})
        self.assertEqual(counts["topic_matched_subscriptions"],1)
        self.assertEqual(counts["linked_cmd_vel_callback_handles"],1)
        e,r,a=original()
        verdict=classify_callback_gap(e,r,rows,cm_pid=CM,clock_anchors=a,
                                      cmd_callback_handles=handles)
        self.assertEqual(verdict["status"],"CM_CMDVEL_CALLBACK_OVER_120MS_CANDIDATE_HOLD")
        self.assertAlmostEqual(verdict["cm_cmdvel_max_duration_ms"],147)
        self.assertEqual(verdict["cm_cmdvel_callback_count_near_first_gap"],1)
        self.assertEqual(verdict["cmdvel_identity_source"],"RCLCPP_SUBSCRIPTION_TOPIC_CALLBACK_CHAIN")
        self.assertFalse(verdict["cm_callback_causality_proven"])
        self.assertFalse(verdict["owner_goal_authorized"])
    def test_non_cm_topics_are_never_mistaken_for_cmd_vel(self):
        handles,counts=resolve_cm_cmdvel_handles(mapped("/scan"),cm_pid=CM)
        self.assertEqual(handles,set())
        self.assertEqual(counts["topic_matched_subscriptions"],0)
    def test_other_process_same_topic_does_not_authorize_cm(self):
        handles,counts=resolve_cm_cmdvel_handles(mapped(pid=CM+500),cm_pid=CM)
        self.assertEqual(handles,set())
        self.assertFalse(counts["raw_trace_exported"])
    def test_link_missing_is_fail_closed_not_guess_from_opaque_symbol(self):
        rows=[x for x in mapped() if x["name"]!="ros2:rclcpp_subscription_init"]
        handles,counts=resolve_cm_cmdvel_handles(rows,cm_pid=CM)
        self.assertEqual(handles,set())
        e,r,a=original()
        result=classify_callback_gap(e,r,rows,cm_pid=CM,clock_anchors=a,
                                     cmd_callback_handles=handles)
        self.assertEqual(result["status"],"CM_CALLBACK_IDENTITY_UNVERIFIED_HOLD")
        self.assertFalse(result["ready_for_wsl2_owner_goal"])
    def test_cross_topic_reused_callback_handle_is_ambiguous_hold(self):
        rows=mapped()+mapped("/safety/scan","cmd")
        with self.assertRaisesRegex(ValueError,"CM_TOPIC_CALLBACK_AMBIGUOUS"):
            resolve_cm_cmdvel_handles(rows,cm_pid=CM)
    def test_cm_only_stream_selector_keeps_topic_subscription_link_metadata(self):
        selected,stats=select_cm_first_window(
            mapped()+[ev("ros2:callback_start",10.05,pid=CM+900)],
            cm_pid=CM,first_pair=(A,B),clock_anchors=ANCHORS)
        handles,counts=resolve_cm_cmdvel_handles(selected,cm_pid=CM)
        self.assertEqual(handles,{"cmd"})
        self.assertEqual(stats["cm_subscription_link_events_kept"],3)
        self.assertEqual(stats["cm_callback_events_kept"],2)
        self.assertEqual(stats["cm_register_events_kept"],1)
        self.assertEqual(counts["linked_cmd_vel_callback_handles"],1)
    def test_resolver_does_not_return_raw_handles_or_user_private_content(self):
        handles,counts=resolve_cm_cmdvel_handles(mapped(),cm_pid=CM)
        txt=str(counts)
        self.assertNotIn("'callback': 'cmd'",txt)
        self.assertNotIn("'cmd'",txt)
        self.assertNotIn("/home",txt)
        self.assertNotIn("0xrcl1",txt)
        self.assertNotIn("0xsub1",txt)
        self.assertFalse(counts["certified_estop"])
        self.assertFalse(counts["owner_goal_authorized"])
if __name__=="__main__": unittest.main()
