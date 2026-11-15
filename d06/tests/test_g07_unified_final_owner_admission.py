"""G07 final single WSLg Owner admission: CI GREEN != WSLg acceptance.

NO ROS, Goal, private code, or access tokens in this test module.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/g07_unified_final_owner_wsl2_once.sh"
GATE=ROOT/"d06/acceptance/g07_unified_final_owner_ci_gate.json"
PRIVATE_SHA="db1eec05e01e1db0d0d2e0c05610806ef4e499f9"
PRIVATE_TREE="005cc352d63067beb9d34397e51b51f7974ce7ef"
P4_RELEASE_SHA="2bb0a46dd1eccdce364ccc9faeb4d5650bfb99f2"
GUI_L2_RUN=43685818018

class FinalOwnerAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from d06.live.g07_unified_final_owner_gate import verify_gate
        cls.verify_gate=staticmethod(verify_gate)

    def test_exact_success_receipt_grants_only_one_wslg_manual_attempt(self):
        gate=json.loads(GATE.read_text(encoding="utf-8"))
        r=self.verify_gate(gate)
        self.assertEqual(r["status"],"ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY")
        self.assertTrue(r["manual_attempt_allowed"])
        self.assertFalse(r["owner_l3_accepted"])
        self.assertFalse(r["full_demo_accepted"])
        self.assertFalse(r["certified_estop"])
        self.assertEqual(gate["instructor_source_sha"],PRIVATE_SHA)
        self.assertEqual(gate["instructor_tree_sha"],PRIVATE_TREE)
        self.assertEqual(gate["public_p4_release_sha"],P4_RELEASE_SHA)
        self.assertEqual(gate["ci_gui_l2_run_id"],GUI_L2_RUN)
        self.assertEqual(gate["actual_wslg_verified"],False)

    def test_first_safety_latch_missing_shutdown_or_stale_source_is_hold(self):
        good=json.loads(GATE.read_text(encoding="utf-8"))
        mutations=(
            ("first_guard_latch","UPSTREAM_STALE_AFTER_MOTION"),
            ("cm_rmw_source_max_ms",170.642126),
            ("scan_max_ms",333.397),
            ("odom_stopped_dwell_sec",0.2),
            ("native_s02_positive_contacts",1),
            ("navigation_shutdown_ack",False),
            ("cm_exit_code",-11),
            ("original_rosbag_topic_count",13),
            ("real_gui_windows_before_goal",False),
            ("ci_gui_l2_conclusion","failure"),
            ("instructor_source_sha","6e402e30f5036285f067b5dffed085eff41af599"),
            ("owner_l3_accepted",True),
            ("certified_estop",True),
        )
        for key,bad in mutations:
            t=copy.deepcopy(good);t[key]=bad
            with self.subTest(key=key):
                r=self.verify_gate(t)
                self.assertFalse(r["manual_attempt_allowed"])
                self.assertEqual(r["status"],"HOLD_UNVERIFIED_CI_GUI_L2_OR_SOURCE")

    def test_missing_metadata_is_not_promoted_to_owner_admission(self):
        good=json.loads(GATE.read_text(encoding="utf-8"))
        for key in ("cm_rmw_source_max_ms","first_guard_latch",
                    "actual_wslg_verified","public_p4_release_sha"):
            t=copy.deepcopy(good);t.pop(key)
            with self.subTest(key=key):
                self.assertFalse(self.verify_gate(t)["manual_attempt_allowed"])

    def test_one_shot_owner_wrapper_is_source_locked_and_does_not_auto_consent(self):
        self.assertTrue(SCRIPT.is_file())
        source=SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(subprocess.run(["bash","-n",str(SCRIPT)],
                         capture_output=True,text=True).returncode,0)
        for must in ("ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY",
                     PRIVATE_SHA,PRIVATE_TREE,P4_RELEASE_SHA,
                     "scripts/axia_p4_mvp_final_owner_once.sh",
                     "d06_rviz_sidecar.sh",
                     "gh auth status","/dev/tty",
                     "mkdir -m 700","G07_OWNER_FINAL_SINGLE_ATTEMPT_RESERVED",
                     "D06_RVIZ_STARTED","AXIA_G07_OWNER_WSLG_NOT_CI_VERIFIED"):
            self.assertIn(must,source)
        self.assertNotIn("AXIA_G07_CI_SIM_GOAL_ALLOWED=1",source)
        self.assertNotIn("AXIA_P2_GUARD_BYPASS=1",source)
        self.assertNotIn('printf "YES-P2-G07-GOAL"',source)

    def test_no_tty_blocks_before_ros_or_goal(self):
        result=subprocess.run(["bash",str(SCRIPT)],capture_output=True,text=True,
            env={"PATH":os.environ.get("PATH",""),"HOME":os.environ.get("HOME","/tmp")},
            timeout=5)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("AXIA_G07_FINAL_OWNER_TTY_REQUIRED_NO_ROS_NO_GOAL",
                      result.stdout+result.stderr)

    def test_readonly_visual_files_and_no_command_publisher(self):
        required=("d06/live/d06_readonly_monitor.py",
                  "d06/scripts/d06_rviz_sidecar.sh",
                  "d06/rviz/d06_safety_bubble.rviz",
                  "d06/live/d06_gui_cpu_plan.py")
        for path in required:self.assertTrue((ROOT/path).is_file(),path)
        src=(ROOT/required[0]).read_text()
        self.assertIn("MarkerArray",src)
        self.assertIn('/axia/d06/rviz/bubble',src)
        self.assertNotIn('create_publisher(Twist',src)
        self.assertNotIn('create_publisher(Pose',src)

if __name__=="__main__":
    unittest.main()
