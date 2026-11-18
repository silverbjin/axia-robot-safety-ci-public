"""Task04 Owner immutable one-shot bootstrap L0; never sends a ROS Goal."""
from pathlib import Path
import subprocess
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/axia_g07_task04_owner_moving_l3_once.sh"
SHA="b274d7c075a570c649697ed5fe55166f2296f8f6"
RUN=44259558479

class OwnerMovingBootstrap(unittest.TestCase):
    def test_static_self_check_instant_no_ros(self):
        r=subprocess.run(["bash",str(SCRIPT),"--self-check"],
                         text=True,capture_output=True,timeout=8)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("AXIA_G07_TASK04_OWNER_MOVING_BOOTSTRAP_L0_PASS",r.stdout)
        self.assertIn(SHA,r.stdout)
        self.assertIn(f"l2_run={RUN}",r.stdout)
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",r.stdout)

    def test_owner_run_never_uses_ci_goal_permissions_or_global_kill(self):
        s=SCRIPT.read_text()
        self.assertIn("AXIA_G07_TASK04_OWNER_MOVING_L3=1",s)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED=0",s)
        self.assertIn("AXIA_P2_G07_RELOCATED_OBSTACLE=1",s)
        self.assertIn("AXIA_G07_CI_OWNER_BAG_PARITY=1",s)
        self.assertIn("AXIA_NAV2_USE_COMPOSITION=False",s)
        self.assertNotIn("GITHUB_ACTIONS=true",s)
        self.assertNotIn("pkill -f",s)
        self.assertNotIn("killall",s)
        self.assertNotIn("wsl --shutdown",s)

    def test_pinned_source_and_private_evidence_archive(self):
        s=SCRIPT.read_text()
        self.assertIn(SHA,s)
        self.assertIn("44259558479",s)
        self.assertIn("p2_g07_task04_moving_review.py",s)
        self.assertIn("AXIA_G07_TASK04_ARCHIVE=",s)
        self.assertIn("AXIA_G07_TASK04_SHA256=",s)
        self.assertIn("task04_owner_verdict.json",s)
        self.assertIn("SHA256SUMS",s)
        self.assertIn("CORE_PARITY_PASS",s)

    def test_bad_argument_fails_without_any_goal(self):
        r=subprocess.run(["bash",str(SCRIPT),"--bad-mode"],
                         text=True,capture_output=True,timeout=8)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("BAD_ARGUMENTS",r.stderr+r.stdout)

if __name__=="__main__":
    unittest.main()
