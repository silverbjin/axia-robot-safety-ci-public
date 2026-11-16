"""Cycle30 RED: L2 #43809629649 exceeded 500k global LTTng events.

Must retain *all* real CM vpid callback register events and all CM
callback start/end in a bounded time window around the first actual
>=120ms CM RMW publisher gap, NOT materialize every global ROS process.
No ROS, Gazebo, Goal, raw data, or private artifact in public CI.
"""
from __future__ import annotations
import unittest
from d06.live.g07_cycle30_bounded_cm_trace import select_cm_first_window

PID=3210
OFFSET=1_700_000_000_000_000_000
ANCHORS={"start":{"mono_ns":9_000_000_000,"wall_ns":9_000_000_000+OFFSET},
         "end":{"mono_ns":12_000_000_000,"wall_ns":12_000_000_000+OFFSET}}
FIRST=({"t":10.0,"rmw_source_ns":1700000000000000000+100_000_000_000,
        "rmw_publication_seq":10},
       {"t":10.16,"rmw_source_ns":1700000000000000000+100_156_345_327,
        "rmw_publication_seq":11})
def ev(name,t,*,pid=PID,cb="cmd",epoch=True):
    return {"name":name,"timestamp_ns":round(t*1e9)+(OFFSET if epoch else 0),
            "vpid":pid,"vtid":pid+1,"callback":cb,
            "symbol":"nav2_collision_monitor::CollisionMonitor::cmdVelInCallback"
             if name=="ros2:rclcpp_callback_register" else None}

class Cycle30SelectedTrace(unittest.TestCase):
    def select(self,rows,**kwargs):
        options={"cm_pid":PID,"first_pair":FIRST,"clock_anchors":ANCHORS}
        options.update(kwargs)
        return select_cm_first_window(rows,**options)
    def test_more_than_500k_unrelated_trace_events_dont_exceed_cm_limit(self):
        # exact prior failure shape: global ROS trace is huge, owned
        # official CollisionMonitor has only a few relevant callbacks.
        def source():
            yield ev("ros2:rclcpp_callback_register",9.1)
            for n in range(500_100):
                yield ev("ros2:callback_start",10.1,pid=9000+n%5)
            yield ev("ros2:callback_start",10.025)
            yield ev("ros2:callback_end",10.035)
        chosen,stats=self.select(source(),max_cm_callbacks=50,max_cm_regs=20)
        self.assertEqual(len(chosen),3)
        self.assertEqual(stats["cm_callback_events_kept"],2)
        self.assertEqual(stats["cm_register_events_kept"],1)
        self.assertGreater(stats["total_events_seen"],500000)
        self.assertEqual(stats["raw_trace_exported"],False)
    def test_both_wall_and_monotonic_trace_domains_retained(self):
        for epoch in (True,False):
            with self.subTest(epoch=epoch):
                chosen,stats=self.select([
                   ev("ros2:rclcpp_callback_register",9.1,epoch=epoch),
                   ev("ros2:callback_start",10.02,epoch=epoch),
                   ev("ros2:callback_end",10.06,epoch=epoch),
                   ev("ros2:callback_start",11.2,epoch=epoch)])
                self.assertEqual([x["name"] for x in chosen],
                     ["ros2:rclcpp_callback_register","ros2:callback_start","ros2:callback_end"])
                self.assertEqual(stats["cm_callback_events_kept"],2)
    def test_all_outside_window_registration_survives_for_callback_identity(self):
        chosen,_=self.select([
            ev("ros2:rclcpp_callback_register",9.2),
            ev("ros2:callback_start",9.71),
            ev("ros2:callback_end",9.72),
            ev("ros2:callback_start",10.02),
            ev("ros2:callback_end",10.17),
            ev("ros2:callback_start",10.50),
            ev("ros2:callback_end",10.60)])
        self.assertEqual(len(chosen),5)
        self.assertEqual(chosen[0]["name"],"ros2:rclcpp_callback_register")
    def test_cm_window_limit_fails_closed_never_silent_truncation(self):
        with self.assertRaisesRegex(ValueError,"CM_CALLBACK_WINDOW_UNBOUNDED"):
            self.select((ev("ros2:callback_start",10.01+i*.0001)
                         for i in range(30)),max_cm_callbacks=10)
        with self.assertRaisesRegex(ValueError,"CM_CALLBACK_REGISTRATION_UNBOUNDED"):
            self.select((ev("ros2:rclcpp_callback_register",9.1,cb=str(i))
                         for i in range(20)),max_cm_regs=8)
    def test_invalid_anchor_or_no_gap_is_hold(self):
        bad={"start":ANCHORS["start"],"end":{
            "mono_ns":12_000_000_000,"wall_ns":12_000_000_000+OFFSET+60_000_000}}
        with self.assertRaises(ValueError):
            select_cm_first_window([ev("ros2:callback_start",10.1)],
                cm_pid=PID,first_pair=FIRST,clock_anchors=bad)
        with self.assertRaises(ValueError):
            self.select([ev("ros2:callback_start",10.1)],
                        first_pair=(FIRST[0],FIRST[0]))
    def test_real_first_gap_pair_must_be_consecutive_published_sequence(self):
        wrong=FIRST[0],{**FIRST[1],"rmw_publication_seq":14}
        with self.assertRaises(ValueError):
            select_cm_first_window([ev("ros2:callback_start",10.1)],
                cm_pid=PID,first_pair=wrong,clock_anchors=ANCHORS)
    def test_selector_returns_no_private_paths_or_goal_authority(self):
        chosen,stats=self.select([ev("ros2:rclcpp_callback_register",9.5),
            ev("ros2:callback_start",10.05),ev("ros2:callback_end",10.08)])
        self.assertFalse(stats["raw_trace_exported"])
        self.assertFalse(stats["owner_goal_authorized"])
        self.assertFalse(stats["certified_estop"])
        self.assertTrue(all(x["vpid"]==PID for x in chosen))
        self.assertNotIn("owner_l3_accepted=true",str(stats))
if __name__=="__main__":unittest.main()
