"""Task04 owner WSL2 public-only GUI pre-gate. ROS-free RED/GREEN.

A pre-gate MUST never claim moving-Goal L3 acceptance or impersonate CI.
The original Task03 exact Student SHA and public native Gazebo PASS remain
immutable. Real WSLg GUI is accepted only by actual Owner field evidence.
"""
import re
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh"
STUDENT="01752add2e30c90c4d3286ef3a450f97746ecb55"
RUN="44223320904"


class OwnerPublicWsl2Pregate(unittest.TestCase):
    def source(self):
        return SCRIPT.read_text()

    def test_exact_public_sha_and_no_private_clone(self):
        s=self.source()
        self.assertIn(STUDENT,s)
        self.assertIn(RUN,s)
        self.assertIn("silverbjin/axia-robot-safety-student",s)
        self.assertNotIn("axia-robot-safety-instructor",s)
        self.assertIn('git -C "$CACHE" rev-parse HEAD',s)
        self.assertIn('git -C "$CACHE" status --porcelain',s)

    def test_no_ci_goal_impersonation_or_unsafe_global_cleanup(self):
        s=self.source()
        self.assertIn('GITHUB_ACTIONS',s)
        self.assertIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=0',s)
        self.assertIn('AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN',s)
        self.assertIn('AXIA_MVP_DEMO_ACCEPTED=HOLD',s)
        for bad in ("export GITHUB_ACTIONS=true","pkill -f","killall ","wsl --shutdown",
                    "AXIA_G07_CI_SIM_GOAL_ALLOWED=1","CERTIFIED_ESTOP=true"):
            self.assertNotIn(bad,s)

    def test_owner_wslg_package_parity_and_persistent_one_file_archive(self):
        s=self.source()
        for required in ('/proc/sys/kernel/osrelease','/opt/ros/jazzy/setup.bash',
                         'XDG_RUNTIME_DIR','DISPLAY','rviz2','gz',
                         '--mode owner','CORE_PARITY_PASS','sha256sum',
                         'tar -czf','xwininfo','d07_h01_gui_no_goal_once.sh',
                         'AXIA_G07_TASK04_ARCHIVE=','AXIA_G07_TASK04_FIRST_FAILURE='):
            self.assertIn(required,s)
        self.assertIn("trap",s)
        self.assertIn("ROS_DOMAIN_ID",s)
        self.assertIn("GZ_PARTITION",s)

    def test_selfcheck_and_no_ros_gui_on_non_wsl_linux(self):
        check=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True)
        self.assertEqual(check.returncode,0,check.stderr)
        done=subprocess.run(["bash",str(SCRIPT),"--self-check"],capture_output=True,text=True)
        self.assertEqual(done.returncode,0,done.stderr)
        self.assertIn("AXIA_G07_TASK04_PUBLIC_OWNER_BOOTSTRAP_L0_PASS",done.stdout)
        blocked=subprocess.run(["bash",str(SCRIPT),"--doctor"],capture_output=True,text=True,timeout=8)
        self.assertNotEqual(blocked.returncode,0)
        self.assertRegex(blocked.stdout+blocked.stderr,
                         r"AXIA_G07_TASK04_FIRST_FAILURE=(?:NOT_WSL2|NOT_OWNER|JAZZY_MISSING|WSLG_UNAVAILABLE)")


if __name__=="__main__":
    unittest.main()
