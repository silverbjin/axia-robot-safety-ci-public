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
            "cm_actual_configured_scan_topic":"scan",  # actual WSL2 official CM config
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
        self.assertEqual(result["cm_actual_configured_scan_topic"],"scan")
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
                **self._real_witness_shape(),
                "status":"D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL",
                "cm_service_probe_mode":"in_process" if i%2==0 else "isolated_process",
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

    def test_real_nav2_cm_lifecycle_first_transition_is_not_planner_failure(self):
        # Sanitized first-failure log from real CI #44766088696.
        # Nav manager initiated CM configuration, but neither CM on_configure
        # callback entry nor manager activation was witnessed.
        from d08_cm_native_probe_isolated import (
            classify_nav2_lifecycle_first_boundary)
        log=(
            "[planner_server]: Configuring\n"
            "[planner_server]: Planner Server has GridBased planners available.\n"
            "[lifecycle_manager_navigation]: Configuring collision_monitor\n"
            "[amcl]: initialPoseReceived\n"
        )
        v=classify_nav2_lifecycle_first_boundary(log)
        self.assertEqual(v["status"],
            "D08_NAV2_CM_CONFIGURE_REQUEST_NO_CALLBACK_ENTRY_OBSERVED_HOLD")
        self.assertTrue(v["navigation_manager_requested_cm_configure"])
        self.assertFalse(v["cm_configure_callback_entry_observed"])
        self.assertFalse(v["cm_navigation_activation_proven"])
        self.assertEqual(v["root_cause"],"UNDETERMINED")
        self.assertFalse(v["owner_wsl2_accepted"])
        self.assertIn("collision_monitor",v["first_lifecycle_boundary"])
        missing=classify_nav2_lifecycle_first_boundary("")
        self.assertEqual(missing["status"],"D08_NAV2_CM_STARTUP_EVIDENCE_INCOMPLETE")
        param=classify_nav2_lifecycle_first_boundary(
            "[lifecycle_manager_navigation]: Configuring collision_monitor\n"
            "[collision_monitor]: Configuring\n"
            "[collision_monitor]: Error while getting parameters: "
            "parameter 'observation_sources' is not initialized")
        self.assertEqual(param["status"],
                         "D08_NAV2_CM_CONFIGURATION_PARAMETER_ERROR_HOLD")

    def test_startup_first_transition_saved_before_runtime_raises(self):
        src=(ROOT/"d08/scripts/d08_public_gazebo_l2.py").read_text()
        self.assertIn("nav2_cm_startup_boundary.json",src)
        self.assertIn("D08_NAV2_CM_FIRST_LIFECYCLE_HANDOFF",src)
        self.assertIn("D08_OFFICIAL_NAV2_BEFORE_PATH_FIRST_BOUNDARY",src)
        self.assertNotIn("AXIA_D08_IGNORE_PLANNER_INACTIVE",src)

    def test_actual_gazebo_eight_cycle_job_is_armed_for_ab_branch(self):
        w=(ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
        self.assertIn("feat/d08-cm-service-ab-isolation-20261121",w)
        self.assertIn("AXIA_D08_CM_AB_MODE:",w)
        self.assertIn("github.head_ref == 'feat/d08-cm-service-ab-isolation-20261121' && '1' || '0'",w)
        self.assertIn("D08_CM_AB_EIGHT_CYCLES_L2_PASS_NOT_ROOT_CAUSE",w)
        self.assertIn("d08-cm-service-ab-comparison.json",w)
        self.assertIn("AXIA_D08_NATIVE_RX_PROBE",w)
        self.assertIn("AXIA_D08_ROS_ISOLATED_RX_PROBE",w)


if __name__=="__main__":
    unittest.main()
