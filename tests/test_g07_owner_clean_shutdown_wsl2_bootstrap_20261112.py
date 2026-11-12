"""Public-only WSL2 Owner bootstrap for G07 ordered Nav2 shutdown.

Exact source and evidence labels: previous moving L2 != new no-Goal teardown
L2. No private code checked out here; manual TTY approval cannot be faked.
"""
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_p2_g07_ci_pass_owner_wsl2_once.sh"
MOVING=ROOT/".github/workflows/axia-p2-g07-ci-real-gazebo-moving-goal-l2.yml"
SHUTDOWN=ROOT/".github/workflows/axia-g07-ordered-nav2-shutdown-real-l2.yml"
NEW="21d658fac03396c9f30798237a820e187ecb447c"
BASE="9f12d7581e07752a53e3b3acd2d5c45ad7d87fa7"
MOVING_RUN="43186070186"
SHUTDOWN_RUN="43234191360"
DIGEST="sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e"


class OwnerCleanShutdownBootstrap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=SCRIPT.read_text()

    def test_exact_source_and_nonoverstated_ci_evidence(self):
        self.assertIn("readonly PRIVATE_SHA='"+NEW+"'",self.s)
        self.assertIn("readonly CI_L2_SOURCE_SHA='"+BASE+"'",self.s)
        self.assertIn("readonly CI_L2_RUN='"+MOVING_RUN+"'",self.s)
        self.assertIn("readonly CI_SHUTDOWN_L2_RUN='"+SHUTDOWN_RUN+"'",self.s)
        self.assertIn("ref: "+BASE,MOVING.read_text())
        self.assertIn("ref: "+NEW,SHUTDOWN.read_text())
        self.assertIn(DIGEST,SHUTDOWN.read_text())
        self.assertNotIn("43072749608",self.s)

    def test_syntax_and_no_goal_selfcheck(self):
        p=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
        q=subprocess.run(["bash",str(SCRIPT),"--self-check"],capture_output=True,text=True,timeout=10)
        self.assertEqual(q.returncode,0,q.stderr)
        self.assertEqual(q.stdout.strip(),
            "AXIA_G07_CI_PASS_OWNER_BOOTSTRAP_STATIC_PASS private_sha="+NEW+
            " moving_l2_baseline="+MOVING_RUN+" moving_l2_source="+BASE+
            " shutdown_l2_exact="+SHUTDOWN_RUN+" OWNER_L3_NOT_RUN")

    def test_no_controlling_tty_is_hard_no_goal(self):
        q=subprocess.run(["bash",str(SCRIPT)],input="",text=True,capture_output=True,timeout=10)
        self.assertEqual(q.returncode,2,q.stderr)
        self.assertIn("real controlling TTY required; NO_GOAL",q.stderr)

    def test_real_owner_consent_and_checkout_preserved(self):
        for snippet in (
            'gh auth status','checkout --detach "$PRIVATE_SHA"',
            '[[ "$ACTUAL" == "$PRIVATE_SHA" ]]',
            '[[ -t 0 && -t 1 && -r /dev/tty ]]',
            'export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"',
            'tools/p2_g07_ordered_shutdown.py',
            'tools/p2_g07_owner_shutdown_audit.py',
            'bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh"',
            '--case G07 --mvp-relocated-obstacle',
            'YES-P2-G07-GOAL','SW Stop != certified E-Stop.'
        ):
            self.assertIn(snippet,self.s)
        self.assertNotIn("echo YES-P2-G07-GOAL",self.s)

    def test_no_protected_goal_or_certification_claim(self):
        self.assertIn("OWNER_L3_NOT_RUN",self.s)
        self.assertNotIn("--case G05",self.s)
        self.assertNotIn("--case G06",self.s)
        self.assertIn("SIMULATION ONLY",self.s)

    def test_mutation_obsolete_sha_and_old_l2_do_not_satisfy_pin(self):
        self.assertNotIn("PRIVATE_SHA='"+BASE+"'",self.s)
        self.assertFalse("PRIVATE_SHA='"+NEW+"'" in self.s.replace(NEW,BASE))
        self.assertFalse("CI_SHUTDOWN_L2_RUN='"+SHUTDOWN_RUN+"'" in
                         self.s.replace(SHUTDOWN_RUN,MOVING_RUN))


if __name__=="__main__":unittest.main()
