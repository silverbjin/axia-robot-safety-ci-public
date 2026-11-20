#!/usr/bin/env python3
"""Field 2026-11-20 WSL2 500.535ms first Scan RMW boundary, ROS-free.

Numeric fixture is from verified bounded PRIVATE evidence, NOT an actual
replayed Gazebo or DDS test. No raw evidence/PII uploaded to public CI.
"""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/scripts"))
sys.path.insert(0,str(ROOT/"d08/harness"))


class D08First500ms(unittest.TestCase):
    def first(self):
        return {
            "kind":"ROS_LASERSCAN_FIRST_RECEIVE_GAP",
            "scope":"owner_replan_cycles/cycle_0000",
            "host_start_sec":272.757400,"host_end_sec":273.257935,
            "gap_sec":.500535,
            "previous_ros_stamp_ns":39102000000,
            "current_ros_stamp_ns":39201000000,
            "header_sim_gap_sec":.099,"limit_sec":.5,
        }

    def test_500_535ms_is_real_fail_closed_not_rounded_pass(self):
        from d08_scan_gap_trace import first_scan_receive_gap
        first=first_scan_receive_gap([
            (272.757400,39102000000),
            (273.257935,39201000000)])
        self.assertEqual(first["receive_gap_sec"],.500535)
        self.assertEqual(first["previous_ros_stamp_ns"],39102000000)
        self.assertEqual(first["current_ros_stamp_ns"],39201000000)
        self.assertGreaterEqual(first["receive_gap_sec"],.5)

    def test_rmw_independent_ros_is_same_python_process_not_isolated_witness(self):
        from d08_owner_rmw_first_gap import correlate_first_boundary
        b=self.first()
        events=[
            {"direction":"publish","node":"ros_gz_bridge",
             "host_monotonic_sec":272.755284,"source_timestamp":10},
            {"direction":"publish","node":"ros_gz_bridge",
             "host_monotonic_sec":272.925565,"source_timestamp":11},
            {"direction":"publish","node":"ros_gz_bridge",
             "host_monotonic_sec":273.096000,"source_timestamp":12},
            {"direction":"publish","node":"ros_gz_bridge",
             "host_monotonic_sec":273.360552,"source_timestamp":13},
        ]
        for node,events_at in (
                ("axia_d08_independent_rx_no_goal",
                 [272.758379,273.254544,273.273136]),
                ("axia_d08_official_physical_replan_no_goal",
                 [272.757400,273.257935,273.274206])):
            events.extend({"direction":"take","node":node,
                           "host_monotonic_sec":at,
                           "source_timestamp":100+i}
                          for i,at in enumerate(events_at))
        verdict=correlate_first_boundary(b,events,capture_complete=True)
        self.assertTrue(verdict["first_500ms_violation_retained"])
        self.assertFalse(verdict["owner_wsl2_accepted"])
        self.assertEqual(verdict["independent_ros_origin"],
                         "SAME_PYTHON_PROCESS_DIFFERENT_RCLPY_NODE_EXECUTOR")
        self.assertFalse(verdict["independent_ros_separate_process"])
        self.assertTrue(verdict["isolated_os_process_not_represented_here"])
        self.assertTrue(verdict["first_500ms_violation_retained"])
        self.assertFalse(verdict["cm_internal_receive_ttl_verified"])
        self.assertFalse(verdict["guard_ttl_verified"])

    def test_heartbeat_spin_and_cm_overlap_are_candidates_not_proven(self):
        from d08_scan_gap_trace import scan_gap_operation_overlaps
        pair={"previous_host_monotonic_sec":272.757400,
              "current_host_monotonic_sec":273.257935}
        spans=[
            {"name":"cm_get_state_service_wait",
             "start_sec":272.342032,"end_sec":273.620514},
            {"name":"cm_native_service_probe",
             "start_sec":272.286077,"end_sec":273.862419}]
        verdict=scan_gap_operation_overlaps(pair,spans)
        self.assertFalse(verdict["root_cause_confirmed"])
        self.assertEqual(verdict["status"],"OBSERVED_OVERLAP_NOT_CAUSE")
        self.assertEqual(len(verdict["overlaps"]),2)
        self.assertAlmostEqual(verdict["overlaps"][0]["overlap_sec"],.500535,places=6)

if __name__=="__main__":unittest.main()
