"""Owner WSL2 field 2026-11-18: reproduce the FIRST actual shell/GUI failure.

The uploaded original ZIP SHA256 was independently verified and 11/11 files
verified. No ROS or Gazebo in L0. Native Xvfb L2 is a SEPARATE real test.
"""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh"
FIXTURE=ROOT/"tests/fixtures/g07_task04_owner_wsl2_first_failure_20261118.json"

class ActualWsl2FirstBoundary(unittest.TestCase):
    def setUp(self):
        self.s=RUNNER.read_text(encoding="utf-8")
        self.e=json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_original_owner_sha_first_stage_and_limit_are_kept(self):
        self.assertEqual(self.e["archive_sha256"],
          "60794337c9dd346c08be41571fec7b84a931154b27d9a06566eaea835d587415")
        self.assertEqual(self.e["archive_inner_sha256_checks"],"11_of_11_pass")
        self.assertEqual(self.e["runtime_parity"],
                         "CORE_PARITY_PASS_25_packages_5_official_files")
        self.assertEqual(self.e["error_stage"],
                         "D07_H01_GUI_RVIZ_PATH_SUBSCRIPTION_ABSENT")
        self.assertFalse(self.e["native_gui_watcher_log_in_archive"])
        self.assertFalse(self.e["native_gui_watcher_ack_in_archive"])
        self.assertFalse(self.e["goal_sent"])
        self.assertIn("01752add2e30c90c4d3286ef3a450f97746ecb55",self.s)

    def test_replay_actual_bash_previous_argument_expansion_must_not_pollute_gz_partition(self):
        # The OLD source literally used $_ which Bash expands to prior
        # 'export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST' argument.
        m=re.search(r'^export GZ_PARTITION=.*$',self.s,re.M)
        self.assertIsNotNone(m)
        script=(
            "export ROS_DOMAIN_ID=86\n"
            "export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST\n"
            +m.group(0)+"\n"
            'printf "%s" "$GZ_PARTITION"\n'
        )
        result=subprocess.run(["bash","-c",script],capture_output=True,text=True,
                              timeout=7,check=True)
        actual=result.stdout
        self.assertRegex(actual,r"^axia_p2_task04_86_[A-Za-z0-9_]+$")
        self.assertNotIn("ROS_AUTOMATIC_DISCOVERY_RANGE",actual)
        self.assertNotIn("=",actual)
        self.assertLessEqual(len(actual),115)

    def test_fail_closed_runtime_partition_and_owner_only(self):
        self.assertIn("AXIA_G07_TASK04_FIRST_FAILURE=GZ_PARTITION_INVALID",self.s)
        self.assertIn("GZ_PARTITION",self.s)
        self.assertIn("GITHUB_ACTIONS",self.s)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED=0",self.s)
        self.assertNotIn("export GITHUB_ACTIONS=true",self.s)
        self.assertNotIn("AXIA_G07_CI_SIM_GOAL_ALLOWED=1",self.s)

    def test_no_goal_gui_watcher_ack_and_first_failure_precede_rviz_subscriber(self):
        # Field runner hid native watcher failure under SECONDARY DDS error.
        # Its GPU trial uses an existing public student watcher with an ACK
        # and a saved exit/transport/first-child record.
        for needed in (
            "AXIA_D07_H01_GPU_GUI_TRIAL=1",
            "d07_gui_watcher_started.txt",
            "d07_gui_watcher.log",
            "d07_gui_watcher_exit.txt",
            "d07_gui_transport_topics.txt",
            "D07_H01_GUI_RVIZ_PATH_SUBSCRIPTION_ABSENT",
            "AXIA_G07_TASK04_FIRST_NATIVE_GUI_FAILURE",
        ):
            self.assertIn(needed,self.s)
        self.assertNotIn("GITHUB_ACTIONS=true",self.s)

    def test_first_failure_archive_includes_native_logs_not_just_outer_stdout(self):
        for needed in (
            'AXIA_P2_SMOKE_RESULTS="$OUT/native"',
            '"$OUT/native/launch.log"',
            '"$OUT/native/d07_gui_watcher.log"',
            '"$OUT/native/d07_h01_geometry.log"',
            'tar -czf "$OUT.tar.gz"',
            'sha256sum "$OUT.tar.gz"',
        ):
            self.assertIn(needed,self.s)
        self.assertIn("AXIA_G07_TASK04_ARCHIVE=",self.s)
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",self.s)

    def test_static_selfcheck_never_starts_ros_or_goal(self):
        r=subprocess.run(["bash",str(RUNNER),"--self-check"],capture_output=True,
                         text=True,timeout=5)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("NO_ROS_NO_GAZEBO_NO_GOAL",r.stdout)
        self.assertIn("AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN",r.stdout)

if __name__=="__main__":
    unittest.main()
