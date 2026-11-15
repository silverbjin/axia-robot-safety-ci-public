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

if __name__=="__main__":
    unittest.main()
