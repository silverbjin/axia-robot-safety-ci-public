"""Public-only static WSL2 Owner bootstrap: exact PIYO-loaded Gazebo L2.

Never self-authorize an Owner Goal; do not run ROS/Gazebo in L0 or publish
private Instructor source. WSLg GUI/kernel remains local-only acceptance.
"""
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_p2_g07_ci_pass_owner_wsl2_once.sh"
L2=ROOT/".github/workflows/axia-p2-g07-ci-real-gazebo-moving-goal-l2.yml"
PRIVATE_SHA="eb984b73138e592caa67426eed9c60dde2ca2ebd"
PUBLIC_L2="43339521667"
SCOPE="SHARED_STARTUP_GOAL_OWNER14_BAG_CM_CLEAN_EXIT0"
DIGEST="sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e"
OLD_SHA="6099ed78c4b7079c60c447cb03ccb3817a99c7a4"


class PiyoOwnerBootstrap(unittest.TestCase):
    def test_exact_source_and_real_ci_proof_only(self):
        t=SCRIPT.read_text()
        self.assertIn("readonly PRIVATE_SHA='"+PRIVATE_SHA+"'",t)
        self.assertIn("readonly CI_L2_RUN='"+PUBLIC_L2+"'",t)
        self.assertIn("readonly CI_L2_SCOPE='"+SCOPE+"'",t)
        self.assertIn(DIGEST,t)
        self.assertNotIn("PRIVATE_SHA='"+OLD_SHA+"'",t)
        self.assertIn("ref: "+PRIVATE_SHA,L2.read_text())
        self.assertIn("AXIA_G07_CI_OWNER_BAG_PARITY: '1'",L2.read_text())
        self.assertIn(DIGEST,L2.read_text())
        self.assertIn("AXIA_G07_PUBLIC_CI_WSL2_MATCHED_14_TOPIC_REAL_BAG_L2_PASS",L2.read_text())

    def test_bootstrap_exact_static_output_and_syntax(self):
        x=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True,timeout=10)
        self.assertEqual(x.returncode,0,x.stderr)
        x=subprocess.run(["bash",str(SCRIPT),"--self-check"],
                         capture_output=True,text=True,timeout=10)
        self.assertEqual(x.returncode,0,x.stderr)
        self.assertEqual(x.stdout.strip(),
            "AXIA_G07_CI_PASS_OWNER_BOOTSTRAP_STATIC_PASS private_sha="+PRIVATE_SHA+
            " ci_l2="+PUBLIC_L2+" scope="+SCOPE+" OWNER_L3_NOT_RUN")

    def test_no_tty_means_no_goal_before_any_clone(self):
        x=subprocess.run(["bash",str(SCRIPT)],input="",
                         capture_output=True,text=True,timeout=10)
        self.assertEqual(x.returncode,2)
        self.assertIn("real controlling TTY required; NO_GOAL",x.stderr)

    def test_manual_goal_and_exact_private_sha_required(self):
        t=SCRIPT.read_text()
        for needle in (
          "gh auth status",
          'checkout --detach "$PRIVATE_SHA"',
          '[[ "$ACTUAL" == "$PRIVATE_SHA" ]]',
          'export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"',
          "scripts/p2_g07_shared_staged_startup.sh",
          "tools/p2_g07_ci_moving_goal.py",
          "tools/p2_g07_ordered_shutdown.py",
          "tools/p2_g07_owner_shutdown_audit.py",
          "YES-P2-G07-GOAL",
          '--case G07 --mvp-relocated-obstacle',
          "SW Stop != certified E-Stop.",
        ):
            self.assertIn(needle,t)
        self.assertNotIn("echo YES-P2-G07-GOAL",t)
        self.assertIn("OWNER_L3_NOT_RUN",t)
        self.assertNotIn("G07_ACCEPTED=true",t)

    def test_no_docker_image_false_equivalence_to_wslg_host(self):
        t=SCRIPT.read_text()
        self.assertIn("CI L2 PASS != WSL2 Owner L3 acceptance",t)
        self.assertIn("WSLG_KERNEL_SCHEDULER_NOT_EQUIVALENT",t)
        self.assertIn("Owner L3 NOT RUN",t)
