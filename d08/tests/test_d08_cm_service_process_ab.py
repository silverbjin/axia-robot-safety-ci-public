#!/usr/bin/env python3
"""D08 real WSL2 500.535ms first gap: service-query process A/B RED contract.

ROS-free: simulates only result schemas; never claims ROS or Gazebo acceptance.
"""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))


class CMServiceABTest(unittest.TestCase):
    def _api(self):
        from d08_cm_native_probe_isolated import (
            mode_for_cycle,parse_isolated_probe_output,summarize_cm_ab)
        return mode_for_cycle,parse_isolated_probe_output,summarize_cm_ab

    def _real_witness_shape(self):
        return {
            "status":"D08_CM_NATIVE_ACTIVE_SCAN_PASS",
            "official_cm_active_scan_configured":True,
            "cm_native_lifecycle_state":"active",
            "cm_native_observation_sources":["scan"],
            "cm_actual_configured_scan_topic":"/scan",
            "cm_internal_receive_gap_verified":False,
            "cm_action_state_verified":False,
        }

    def test_same_world_eight_cycles_alternate_original_and_isolated(self):
        mode,_,_=self._api()
        self.assertEqual(
            [mode(i,enabled=True) for i in range(8)],
            ["in_process","isolated_process"]*4)
        self.assertEqual(
            [mode(i,enabled=False) for i in range(3)],
            ["in_process"]*3)

    def test_real_service_identity_and_active_scan_required(self):
        _,parse,_=self._api()
        payload=self._real_witness_shape()
        result=parse("preflight\nD08_CM_NATIVE_ISOLATED_RESULT="+json.dumps(payload)+"\n")
        self.assertEqual(result["cm_native_lifecycle_state"],"active")
        self.assertEqual(result["cm_actual_configured_scan_topic"],"/scan")
        for key,value in (
            ("cm_native_lifecycle_state","inactive"),
            ("cm_actual_configured_scan_topic","/fake_scan"),
            ("official_cm_active_scan_configured",False),
            ("cm_native_observation_sources",[]),
            ("cm_internal_receive_gap_verified",True),
        ):
            with self.subTest(bad_key=key):
                corrupted={**payload,key:value}
                with self.assertRaises(ValueError):
                    parse("D08_CM_NATIVE_ISOLATED_RESULT="+json.dumps(corrupted))
        with self.assertRaises(ValueError):
            parse("D08_CM_NATIVE_ISOLATED_RESULT={corrupt-json}\n")
        with self.assertRaises(ValueError):
            parse("no service result available\n")

    def test_ab_only_labels_result_not_root_cause_or_safety_pass(self):
        _,_,summarize=self._api()
        cycles=[]
        for i in range(8):
            cycles.append({
                "status":"D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL",
                "cm_service_probe_mode":"in_process" if i%2==0 else "isolated_process",
                **self._real_witness_shape(),
                "first_scan_timing_boundary":None,
                "worst_scan_pair_source_stamps":{"receive_gap_sec":.165+i*.005},
            })
        result=summarize(cycles)
        self.assertEqual(result["status"],"D08_CM_SERVICE_AB_OBSERVED_L2_PASS_NOT_ROOT_CAUSE")
        self.assertEqual(result["cycles_per_mode"],{"in_process":4,"isolated_process":4})
        self.assertEqual(result["root_cause"],"UNDETERMINED")
        self.assertFalse(result["cm_internal_120ms_verified"])
        self.assertFalse(result["guard_150ms_verified"])
        self.assertFalse(result["owner_wsl2_accepted"])
        with self.assertRaises(ValueError):
            summarize(cycles[:-1])
        bad=[dict(x) for x in cycles]
        bad[3]["first_scan_timing_boundary"]={"receive_gap_sec":.500535}
        with self.assertRaises(ValueError):
            summarize(bad)
        bad=[dict(x) for x in cycles]
        bad[1]["cm_service_probe_mode"]="in_process"
        with self.assertRaises(ValueError):
            summarize(bad)

    def test_helper_queries_unmodified_actual_cm_services_in_separate_ros_context(self):
        path=ROOT/"d08/harness/d08_cm_native_probe_isolated.py"
        source=path.read_text()
        self.assertIn('"/collision_monitor/get_state"',source)
        self.assertIn('"/collision_monitor/get_parameters"',source)
        self.assertIn('"observation_sources","scan.topic"',source)
        self.assertIn("rclpy.init()",source)
        self.assertIn("GetState",source)
        self.assertIn("GetParameters",source)
        self.assertIn("D08_CM_NATIVE_ISOLATED_RESULT=",source)

    def test_original_ros_observer_changes_no_500ms_or_cm_ttl(self):
        path=ROOT/"d08/harness/d08_same_world_replan.py"
        source=path.read_text()
        self.assertIn("AXIA_D08_CM_SERVICE_PROBE_MODE",source)
        self.assertIn("d08_cm_native_probe_isolated.py",source)
        self.assertIn("read_official_cm_native_state_and_scan()",source)
        self.assertIn("cm_service_probe_mode",source)
        self.assertIn("compare_native_scan_first_gap",source)
        self.assertIn("if v>.5",source)
        self.assertNotIn("AXIA_D08_DISABLE_SCAN_GAP",source)

    def test_actual_gazebo_eight_cycle_job_is_armed_for_ab_branch(self):
        w=(ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
        self.assertIn("feat/d08-cm-service-ab-isolation-20261121",w)
        self.assertIn('AXIA_D08_CM_AB_MODE: "1"',w)
        self.assertIn("D08_CM_AB_EIGHT_CYCLES_L2_PASS_NOT_ROOT_CAUSE",w)
        self.assertIn("d08-cm-service-ab-comparison.json",w)
        self.assertIn("AXIA_D08_NATIVE_RX_PROBE",w)
        self.assertIn("AXIA_D08_ROS_ISOLATED_RX_PROBE",w)


if __name__=="__main__":
    unittest.main()
