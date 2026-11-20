#!/usr/bin/env python3
"""Field 2026-11-20 D05 farther Scan first 500ms evidence and release parity.

Pure stdlib; does not synthesize passing ROS/Gazebo observations.
"""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/scripts"))


class D05OwnerParity(unittest.TestCase):
    def fixture(self, root):
        live=root/"live_evidence"
        (live/"live_person_range").mkdir(parents=True)
        (live/"official_path_phases").mkdir()
        first={"kind":"ROS_LASERSCAN_FIRST_RECEIVE_GAP",
               "sample_index":12,
               "receive_gap_sec":.521381,
               "previous_host_monotonic_sec":5210.1,
               "current_host_monotonic_sec":5210.621381,
               "previous_ros_stamp_ns":68100000000,
               "current_ros_stamp_ns":68200000000,
               "header_sim_gap_sec":.1, "limit_sec":.5}
        scan={"scan_count":20,"front_m":.8,
              "wall_gap_max_sec":.521381,
              "sim_stamp_period_median_sec":.1,
              "observed_rtf":.483,
              "first_rx_gap_over_500ms":first,
              "no_synthetic_scan":True}
        (live/"live_person_range"/"farther_scan.json").write_text(json.dumps(scan))
        (live/"live_person_range"/"verdict.json").write_text(json.dumps({
            "status":"HOLD","stages":[],
            "first_boundary":"RuntimeError:D08_PERSON_FARTHER_ACTUAL_SCAN_CADENCE_NOT_VERIFIED"
        }))
        (live/"official_path_phases"/"verdict.json").write_text(json.dumps({
            "status":"D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL"}))
        return first

    def test_field_zip_includes_actual_d05_source_pair_and_rtf(self):
        from d08_compact_evidence import create_compact_evidence
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/"run"
            first=self.fixture(root)
            output=Path(folder)/"diagnostics.zip"
            create_compact_evidence(root,output)
            with zipfile.ZipFile(output) as z:
                name="live_evidence/live_person_range/farther_scan.json"
                self.assertIn(name,z.namelist())
                data=json.loads(z.read(name))
                self.assertEqual(data["first_rx_gap_over_500ms"],first)
                self.assertEqual(data["observed_rtf"],.483)
            self.assertLessEqual(output.stat().st_size,8*1024*1024)

    def test_rmw_classifier_must_select_d05_first_active_scan_violation(self):
        from d08_owner_rmw_first_gap import collect_first_scan_boundary
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/"run"
            first=self.fixture(root)
            selected=collect_first_scan_boundary(root)
            self.assertEqual(selected["kind"],"ROS_LASERSCAN_FIRST_RECEIVE_GAP")
            self.assertEqual(selected["scope"],"live_person_range/farther")
            self.assertEqual(selected["gap_sec"],first["receive_gap_sec"])
            self.assertEqual(selected["previous_ros_stamp_ns"],first["previous_ros_stamp_ns"])
            self.assertEqual(selected["current_ros_stamp_ns"],first["current_ros_stamp_ns"])

    def test_d05_verdict_preserves_first_boundary_even_on_error(self):
        source=(ROOT/"d08/harness/d08_live_person_range_session.py").read_text()
        self.assertIn('first_scan_timing_boundary',source)
        self.assertIn('first_rx_gap_over_500ms',source)
        self.assertIn("D08_PERSON_",source)

    def test_missing_or_skipped_d05_job_prevents_release(self):
        from d08_owner_parity_coverage_gate import check_required_coverage
        for status in ("skipped","failure","cancelled",None):
            with self.subTest(status=status):
                result=check_required_coverage(
                    {"l0-human-proxy-red-green":"success",
                     "real-gazebo-rgb-pinned-upstream-yolo-ros":status})
                self.assertEqual(result["status"],"RELEASE_HOLD_COVERAGE_INCOMPLETE")
                self.assertFalse(result["ready_for_wsl2"])
        pass_result=check_required_coverage({
            "l0-human-proxy-red-green":"success",
            "real-gazebo-rgb-pinned-upstream-yolo-ros":"success"})
        self.assertEqual(pass_result["status"],"D08_PUBLIC_OWNER_PARITY_COVERAGE_L2_PASS_NOT_WSL2")
        self.assertFalse(pass_result["l3_tested"])

    def test_yolo_d05_real_job_is_required_on_this_branch(self):
        workflow=(ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
        target="fix/d08-owner-d05-ci-wsl2-parity-20261120"
        self.assertIn("d08-owner-parity-release-gate:",workflow)
        self.assertIn(target,workflow)
        jobs=workflow.split("  real-gazebo-rgb-pinned-upstream-yolo-ros:")[1]
        self.assertIn("--official-nav2 --official-path-phases --live-person-range",jobs)
        self.assertIn("D08_REAL_LIVE_RGBD_YOLO_D05_NAV2_THREE_PATHS_L2_PASS_NO_GOAL",jobs)
        self.assertIn("RELEASE_HOLD_COVERAGE_INCOMPLETE",workflow)


if __name__=="__main__":
    unittest.main()
