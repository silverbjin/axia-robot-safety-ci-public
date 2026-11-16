"""Cycle29 RED: first genuine CM output RMW gap mapped to official callback trace.

Only sanitized synthetic events here. LTTng raw traces and private Owner bag
must remain on the sealed CI runner. No ROS Goal, no extra publisher, no TTL
change. Chronological and clock-domain failures are fail-closed.
"""
from __future__ import annotations
import copy
import unittest
from d06.live.g07_cycle29_first_cm_callback_trace import classify_callback_gap

CM=3210
WALL_OFFSET=1_700_000_000_000_000_000
def traced(name,monotonic_sec,*,pid=CM,tid=3211,callback="cmd"):
    return {"name":name, "timestamp_ns":round(monotonic_sec*1e9)+WALL_OFFSET,
            "vpid":pid,"vtid":tid,"callback":callback,
            "symbol":"nav2_collision_monitor::CollisionMonitor::cmdVelInCallback"
                    if name=="ros2:rclcpp_callback_register" else None}

def original():
    s=1700000000000000000
    def row(kind,recv,source,seq):
        return {"kind":kind,"t":recv,
                "rmw_source_ns":s+round(source*1e9),
                "rmw_received_ns":s+round(source*1e9)+1_000_000,
                "rmw_publication_seq":seq}
    events=[{"kind":"owner_goal_published","t":9.0},
            row("pre_guard",10.000,100.000,10),
            row("pre_guard",10.162,100.156345327,11)]
    events.extend(row("supervised",10.01+i*.048,100.025+i*.049,100+i)
                  for i in range(3))
    report={"cm_first_120ms_rmw_release_margin":{
                "status":"CM_SOURCE_GAP_EXCEEDS_120MS",
                "cm_source_gap_sec":.156345327,
                "upstream_publications_inside_gap":3},
            "stop_native_rpc_monotonic_window":{
                "started_at":10.02,"ended_at":10.129705409}}
    anchor={"start":{"mono_ns":9_000_000_000,
                     "wall_ns":9_000_000_000+WALL_OFFSET},
            "end":{"mono_ns":12_000_000_000,
                   "wall_ns":12_000_000_000+WALL_OFFSET}}
    return events,report,anchor

class FirstCallbackTrace(unittest.TestCase):
    def invoke(self,callback_rows,*,events=None,report=None,anchor=None,cm_pid=CM):
        e,r,a=original()
        return classify_callback_gap(e if events is None else events,
                                     r if report is None else report,
                                     callback_rows,cm_pid=cm_pid,
                                     clock_anchors=a if anchor is None else anchor)

    def test_long_actual_official_cmdvel_callback_is_candidate_not_proof(self):
        trace=[traced("ros2:rclcpp_callback_register",9.5),
               traced("ros2:callback_start",10.010),
               traced("ros2:callback_end",10.157)]
        r=self.invoke(trace)
        self.assertEqual(r["status"],"CM_CMDVEL_CALLBACK_OVER_120MS_CANDIDATE_HOLD")
        self.assertAlmostEqual(r["first_cm_source_gap_ms"],156.345327,places=4)
        self.assertAlmostEqual(r["cm_cmdvel_max_duration_ms"],147,places=3)
        self.assertEqual(r["upstream_publications_inside_gap"],3)
        self.assertEqual(r["trace_clock_domain"],"LTTNG_WALL_EPOCH_MAPPED_MONOTONIC")
        self.assertFalse(r["cm_callback_causality_proven"])
        self.assertFalse(r["owner_goal_authorized"])
        self.assertFalse(r["owner_l3_accepted"])

    def test_short_cmdvel_callback_does_not_explain_full_output_gap(self):
        trace=[traced("ros2:rclcpp_callback_register",9.5),
               traced("ros2:callback_start",10.065),
               traced("ros2:callback_end",10.069)]
        r=self.invoke(trace)
        self.assertEqual(r["status"],"CM_INPUT_DELIVERY_OR_EXECUTOR_DELAY_CANDIDATE_HOLD")
        self.assertAlmostEqual(r["cm_cmdvel_max_duration_ms"],4,places=3)
        self.assertFalse(r["cm_callback_causality_proven"])

    def test_unregistered_callback_cannot_be_called_cm_input(self):
        trace=[traced("ros2:callback_start",10.01),
               traced("ros2:callback_end",10.15)]
        r=self.invoke(trace)
        self.assertEqual(r["status"],"CM_CALLBACK_IDENTITY_UNVERIFIED_HOLD")
        self.assertIsNone(r["cm_cmdvel_max_duration_ms"])

    def test_wrong_process_traces_cannot_claim_cm_callback(self):
        trace=[traced("ros2:rclcpp_callback_register",9.5,pid=999),
               traced("ros2:callback_start",10.01,pid=999),
               traced("ros2:callback_end",10.15,pid=999)]
        r=self.invoke(trace)
        self.assertEqual(r["status"],"CM_CALLBACK_IDENTITY_UNVERIFIED_HOLD")

    def test_wall_and_monotonic_offset_step_is_fail_closed(self):
        events,report,anchor=original()
        anchor["end"]["wall_ns"]+=100_000_000
        trace=[traced("ros2:rclcpp_callback_register",9.5),
               traced("ros2:callback_start",10.01),
               traced("ros2:callback_end",10.15)]
        r=self.invoke(trace,anchor=anchor)
        self.assertEqual(r["status"],"TRACE_CLOCK_CALIBRATION_UNVERIFIED_HOLD")
        self.assertFalse(r["owner_goal_authorized"])

    def test_first_cm_gap_provenance_mismatch_is_hold(self):
        events,report,_=original()
        report["cm_first_120ms_rmw_release_margin"]["cm_source_gap_sec"]=.1
        r=self.invoke([traced("ros2:rclcpp_callback_register",9.5)],
                      events=events,report=report)
        self.assertEqual(r["status"],"FIRST_CM_RMW_ORACLE_UNVERIFIED_HOLD")

    def test_unclosed_callback_is_not_completed_processing(self):
        trace=[traced("ros2:rclcpp_callback_register",9.5),
               traced("ros2:callback_start",10.04)]
        r=self.invoke(trace)
        self.assertEqual(r["status"],"CM_INPUT_DELIVERY_OR_EXECUTOR_DELAY_CANDIDATE_HOLD")
        self.assertIsNone(r["cm_cmdvel_max_duration_ms"])

    def test_output_has_no_private_ros_messages_pid_goal_uuid(self):
        trace=[traced("ros2:rclcpp_callback_register",9.5),
               traced("ros2:callback_start",10.02),
               traced("ros2:callback_end",10.05)]
        r=self.invoke(trace)
        import json
        txt=json.dumps(r)
        for forbidden in ("goal_uuid","cm_pid","thread_id",
                          "/home/","raw_trace","collision_monitor::"):
            self.assertNotIn(forbidden,txt)
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",txt)

if __name__=="__main__":
    unittest.main()
