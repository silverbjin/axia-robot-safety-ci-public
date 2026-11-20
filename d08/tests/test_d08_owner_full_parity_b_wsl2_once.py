#!/usr/bin/env python3
"""Waffle/Gazebo/Nav2/YOLO/D05→Owner first cycle public L2 and WSL2 contract.

Prior WSL2 first >500ms occurred ONLY AFTER live D05 passed. This regression
must fail until the same session and release gate actually exercise that stage.
"""
import unittest
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))

class D08OwnerFullParity(unittest.TestCase):
    def test_01_real_ci_replays_first_owner_cycle_after_actual_live_yolo_d05(self):
        src=(ROOT/"d08/scripts/d08_public_gazebo_l2.py").read_text()
        self.assertIn("AXIA_D08_CI_OWNER_CYCLES",src)
        self.assertIn("D08_CI_OWNER_FIRST_AFTER_D05_REAL_SCAN_L2_PASS",src)
        self.assertIn("AXIA_D08_CM_SERVICE_PROBE_MODE",src)
        self.assertIn("D08_CI_OWNER_FIRST_AFTER_D05_SCAN_OVER_500MS_HOLD",src)
        self.assertIn("if live_person_range and ci_owner_repro",src)
        self.assertIn("result['d05_executed']",src)
        self.assertIn("first_scan_timing_boundary",src)
        self.assertIn("D08_CI_REAL_GUI_EIGHT_REPEAT_PATHS_L2_PASS",src)

    def test_02_live_ci_job_runs_gui_and_first_owner_cycle_from_same_physical_world(self):
        src=(ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
        self.assertIn("fix/d08-owner-full-parity-b-wsl2-once-20261121",src)
        job=src.split("  real-gazebo-rgb-pinned-upstream-yolo-ros:")[1].split(
            "  d08-owner-parity-release-gate:")[0]
        self.assertIn("AXIA_D08_CM_SERVICE_PROBE_MODE=isolated_process",job)
        self.assertIn("AXIA_D08_CI_OWNER_CYCLES=1",job)
        self.assertIn("xvfb-run",job)
        self.assertIn("--ci-owner-repro",job)
        self.assertIn("--live-person-range",job)
        self.assertIn("ci_owner_replan_cycles",job)
        self.assertIn("cycle_0000",job)
        self.assertIn("first_scan_timing_boundary",job)
        self.assertIn("D08_OWNER_FULL_SAME_SESSION_FIRST_CYCLE_L2_PASS_NOT_WSL2",job)

    def test_03_release_gate_holds_if_live_d05_skipped(self):
        src=(ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
        tail=src.split("  d08-owner-parity-release-gate:")[1]
        self.assertIn("fix/d08-owner-full-parity-b-wsl2-once-20261121",tail)
        self.assertIn("RELEASE_HOLD_COVERAGE_INCOMPLETE",tail)
        self.assertIn("real-gazebo-rgb-pinned-upstream-yolo-ros",tail)

    def test_04_wsl2_owner_is_single_unattended_first_cycle_not_infinite_loop(self):
        source=(ROOT/"d08/scripts/d08_public_gazebo_l2.py").read_text()
        self.assertIn("AXIA_D08_OWNER_FIRST_CYCLE_ONLY",source)
        self.assertIn("D08_OWNER_GUI_ONE_REAL_CYCLE_COMPLETE",source)
        self.assertIn("D08_OWNER_GUI_AUTO_COMPLETE_AFTER_ONE_CYCLE",source)
        self.assertIn("D08_OWNER_FIRST_CYCLE_NOT_COMPLETED_HOLD",source)

    def test_05_actual_first_map_lifecycle_reply_timeout_precedes_planner_and_cm_summary(self):
        # Sanitized REAL CI #44831417211: Map I/O succeeded, Fast DDS
        # failed to send the /map_server/change_state service response.
        from d08_cm_native_probe_isolated import classify_nav2_lifecycle_first_boundary
        log="\n".join([
            "[lifecycle_manager_localization]: Configuring map_server",
            "[map_server]: Configuring",
            "[map_io]: Read map ...: 384 X 384 map @ 0.05 m/cell",
            "[map_server.rclcpp]: failed to send response to /map_server/change_state (timeout): client will not receive response, at ./src/rmw_response.cpp:153",
            "[lifecycle_manager_navigation]: Configuring collision_monitor",
            "[collision_monitor]: Configuring",
            "[lifecycle_manager_navigation]: Activating planner_server",
            "[global_costmap.global_costmap]: Timed out waiting for transform from base_link to map"])
        v=classify_nav2_lifecycle_first_boundary(log)
        self.assertEqual(v["status"],
            "D08_NAV2_MAP_SERVER_CHANGE_STATE_RESPONSE_TIMEOUT_HOLD")
        self.assertEqual(v["first_lifecycle_boundary"],
                         "/map_server/change_state:response_timeout")
        self.assertEqual(v["rmw_root_cause"],"UNDETERMINED")
        self.assertFalse(v["owner_wsl2_accepted"])
        self.assertFalse(v["cm_internal_120ms_verified"])

    def test_06_rmw_comparison_is_only_enabled_on_scoped_full_parity_branch(self):
        workflow=(ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
        target="fix/d08-owner-full-parity-b-wsl2-once-20261121"
        job=workflow.split("  real-gazebo-rgb-pinned-upstream-yolo-ros:")[1].split(
            "  d08-owner-parity-release-gate:")[0]
        self.assertIn("RMW_IMPLEMENTATION=rmw_cyclonedds_cpp",job)
        self.assertIn("ros-jazzy-rmw-cyclonedds-cpp",job)
        self.assertIn(target,job)
        self.assertIn("D08_CYCLONE_RMW_OWNER_ISOLATED_COMPARISON_L2_CANDIDATE",job)
        self.assertIn("RMW_IMPLEMENTATION",job)

    def test_05_wrapper_is_pinned_and_does_not_inflate_diagnostics(self):
        script=ROOT/"d08/scripts/d08_owner_full_parity_b_wsl2_once.sh"
        self.assertTrue(script.exists())
        contents=script.read_text()
        self.assertIn("AXIA_D08_CM_SERVICE_PROBE_MODE=isolated_process",contents)
        self.assertIn("AXIA_D08_OWNER_FIRST_CYCLE_ONLY=1",contents)
        self.assertIn("OWNER_BLOB=",contents)
        self.assertIn("RUNTIME_SHA=",contents)
        self.assertIn("D08_OWNER_UPLOAD_ONLY_THIS_ZIP",contents)
        self.assertIn("sha256sum",contents)
        self.assertIn("8388608",contents)
        self.assertIn("D08_OWNER_PUBLIC_L2_SCOPE",contents)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",contents)

if __name__=="__main__":
    unittest.main()
