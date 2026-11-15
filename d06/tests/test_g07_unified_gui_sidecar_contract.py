"""CI-only display sidecar contract: no Goal/control authority, no Owner bypass."""
from pathlib import Path
import os
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/g07_unified_ci_readonly_display.sh"

class UnifiedGuiSidecarContract(unittest.TestCase):
    def test_single_sidecar_script_exists_and_shell_syntax_valid(self):
        self.assertTrue(SCRIPT.is_file(), "G07_UNIFIED_CI_READONLY_DISPLAY_MISSING")
        result=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_ci_only_no_ros_no_goal_denies_external_execution(self):
        result=subprocess.run(["bash",str(SCRIPT),"/tmp","/tmp"],
            capture_output=True,text=True,env={"PATH":os.environ.get("PATH","")},timeout=5)
        self.assertEqual(result.returncode,3)
        self.assertIn("G07_UNIFIED_GUI_CI_ONLY_NO_ROS_NO_GOAL",result.stdout+result.stderr)
    def test_readonly_guard_and_real_display_attestation(self):
        s=SCRIPT.read_text()
        for x in ("GITHUB_ACTIONS","AXIA_P0_SIM_ONLY","AXIA_G07_CI_SIM_GOAL_ALLOWED",
                  "startup_verdict.json","SMOKE_READY","rviz2","d06_readonly_monitor.py",
                  "xwininfo","DISPLAY_WINDOW"):
            self.assertIn(x,s)
        for x in ("ros2 action send_goal","ros2 topic pub /cmd_vel",
                  "YES-P2-G07-GOAL","p2_owner_l3_wsl2.sh"):
            self.assertNotIn(x,s)

    def test_ros_environment_is_sourced_before_rviz_command_discovery(self):
        s=SCRIPT.read_text()
        self.assertIn("source /opt/ros/jazzy/setup.bash",s)
        self.assertLess(s.index("source /opt/ros/jazzy/setup.bash"),
                        s.index("for cmd in rviz2 gz xwininfo"),
                        "CI_GUI_SIDECAR_ROS_PATH_MUST_BE_ACTIVE_BEFORE_RVIZ_CHECK")

    def test_gui_l2_overlay_sources_ros_before_rviz_lookup(self):
        workflow=(ROOT/".github/workflows/axia-g07-unified-gui-one-goal-l2.yml").read_text()
        overlay=workflow.split("      - name: Install test-only official RViz and Xvfb overlay",1)[1].split("      - name: Isolated S02",1)[0]
        lookup=overlay.index("for cmd in Xvfb rviz2 xwininfo gz")
        source=overlay.find("source /opt/ros/jazzy/setup.bash")
        self.assertGreaterEqual(source,0,"CI_GUI_OVERLAY_ROS_ENV_NOT_SOURCED")
        self.assertLess(source,lookup,"CI_GUI_RVIZ_BIN_DISCOVERY_BEFORE_ROS_SETUP")

if __name__=="__main__":
    unittest.main()
