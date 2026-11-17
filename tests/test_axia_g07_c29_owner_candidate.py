"""G07 C29 public bootstrap contract only: NO ROS, no Gazebo, no Goal."""
import os
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_g07_c29_owner_one_goal_ttl_once.sh"


class OwnerG07C29Candidate(unittest.TestCase):
    def test_fixed_exact_ci_and_private_sha_and_no_fake_acceptance(self):
        s=SCRIPT.read_text()
        self.assertIn("275d68012a6a1cdc5ce466f2581281b9614c4381",s)
        self.assertIn("44008818507",s)
        self.assertIn("70de0c1a52f11d194e1f2aa0f1b263db7f75912c",s)
        self.assertIn("861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e",s)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",s)
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",s)

    def test_selfcheck_is_no_ros_no_goal(self):
        r=subprocess.run(["bash",str(SCRIPT),"--self-check"],text=True,
                         capture_output=True,timeout=8)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("AXIA_G07_C29_OWNER_STATIC_L0_PASS",r.stdout)
        self.assertIn("NO_ROS_NO_GAZEBO_NO_GOAL OWNER_L3_NOT_RUN",r.stdout)

    def test_no_tty_blocks_before_any_clone_or_goal(self):
        r=subprocess.run(["bash",str(SCRIPT)],text=True,
                         input="",capture_output=True,timeout=8)
        self.assertEqual(r.returncode,3,r.stdout+r.stderr)
        self.assertIn("CONTROLLING_TTY_REQUIRED",r.stderr)
        self.assertNotIn("OWNER_PRIVATE_SOURCE_VERIFIED",r.stdout)

    def test_manual_owner_authority_not_implicitly_granted(self):
        s=SCRIPT.read_text()
        self.assertIn("gh auth status",s)
        self.assertIn("AXIA_P2_OWNER_PINNED_SHA",s)
        self.assertIn("--case G07 --mvp-relocated-obstacle",s)
        self.assertIn("requires manual YES-P2-G07-GOAL",s)
        self.assertNotRegex(s,r"\byes\s*\|")
        self.assertNotIn("AXIA_G07_CI_SIM_GOAL_ALLOWED=1",s)
        self.assertIn("GITHUB_ACTIONS_MUST_NOT_SEND_OWNER_GOAL",s)

    def test_source_provenance_checked_before_private_checkout(self):
        s=SCRIPT.read_text()
        self.assertLess(s.index("gh api"),s.index("gh repo clone"))
        self.assertLess(s.index("git -C \"$WORK/instructor\" rev-parse HEAD"),
                        s.index('bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh"'))
        self.assertIn("completed success",s)
        self.assertIn("CI_OWNER_WSL2_KERNEL_WSLG_SCHEDULER_NOT_EQUAL",s)


if __name__=="__main__":
    unittest.main()
