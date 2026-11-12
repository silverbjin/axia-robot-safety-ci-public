"""Public-only NO-GOAL WSL2 bootstrap pin for the real G07 Owner field fix.

Do not fetch private sources in this static job, do not send Owner consent.
"""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/axia_p2_g07_ci_pass_owner_wsl2_once.sh"
OLD_WORKFLOW = ROOT / ".github/workflows/axia-p2-g07-ci-pass-owner-bootstrap-static-l0.yml"
L2 = ROOT / ".github/workflows/axia-p2-g07-ci-real-gazebo-moving-goal-l2.yml"
PROOF = ROOT / ".github/workflows/axia-p2-g07-ci-real-gazebo-moving-goal-l2.approved-trigger"
SOURCE = "9f12d7581e07752a53e3b3acd2d5c45ad7d87fa7"
RUN = "43186070186"
OLD_SOURCE = "cc92327d1ae4a17d331d06e845437760ca2bdafe"
OLD_RUN = "43072749608"
IMAGE = "ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e"


class OwnerFieldPin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = WRAPPER.read_text(encoding="utf-8")

    def test_exact_fixed_private_sha_proven_real_gazebo_l2(self):
        self.assertIn("readonly PRIVATE_SHA='" + SOURCE + "'", self.content)
        self.assertIn("readonly CI_L2_RUN='" + RUN + "'", self.content)
        self.assertNotIn(OLD_SOURCE, self.content)
        self.assertNotIn("readonly CI_L2_RUN='" + OLD_RUN + "'", self.content)
        self.assertIn("private_source_sha=" + SOURCE, PROOF.read_text())
        self.assertIn("ref: " + SOURCE, L2.read_text())
        self.assertIn(IMAGE, L2.read_text())

    def test_existing_static_ci_expectation_uses_fixed_sha(self):
        content=OLD_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("private_sha=" + SOURCE + " ci_l2=" + RUN + " OWNER_L3_NOT_RUN",content)
        self.assertNotIn("private_sha=" + OLD_SOURCE, content)

    def test_bash_syntax_and_precise_selfcheck(self):
        syntax=subprocess.run(["bash","-n",str(WRAPPER)],capture_output=True,text=True)
        self.assertEqual(syntax.returncode,0,syntax.stderr)
        check=subprocess.run(["bash",str(WRAPPER),"--self-check"],capture_output=True,text=True,timeout=10)
        self.assertEqual(check.returncode,0,check.stderr)
        self.assertEqual(check.stdout.strip(),
            "AXIA_G07_CI_PASS_OWNER_BOOTSTRAP_STATIC_PASS private_sha="+SOURCE+
            " ci_l2="+RUN+" OWNER_L3_NOT_RUN")

    def test_no_tty_never_sends_goal(self):
        cmd=subprocess.run(["bash",str(WRAPPER)],input="",capture_output=True,text=True,timeout=10)
        self.assertEqual(cmd.returncode,2)
        self.assertIn("real controlling TTY required; NO_GOAL",cmd.stderr)

    def test_owner_authority_and_private_checkout_unchanged(self):
        s=self.content
        for value in (
            "PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'",
            'gh auth status',
            'fetch --no-tags --depth 1 origin "$PRIVATE_SHA"',
            'checkout --detach "$PRIVATE_SHA"',
            '[[ "$ACTUAL" == "$PRIVATE_SHA" ]]',
            '[[ -t 0 && -t 1 && -r /dev/tty ]]',
            'export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"',
            'bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh"',
            '--case G07 --mvp-relocated-obstacle',
            'YES-P2-G07-GOAL',
            'SW Stop != certified E-Stop.',
        ):
            self.assertIn(value,s)
        self.assertNotIn("echo YES-P2-G07-GOAL",s)
        self.assertNotIn("--case G05",s)
        self.assertNotIn("--case G06",s)

    def test_old_source_and_run_mutations_are_rejected(self):
        def correct(text):
            return "PRIVATE_SHA='"+SOURCE+"'" in text and "CI_L2_RUN='"+RUN+"'" in text
        self.assertTrue(correct(self.content) or OLD_SOURCE in self.content)
        self.assertFalse(correct(self.content.replace(SOURCE,OLD_SOURCE)))
        self.assertFalse(correct(self.content.replace(RUN,OLD_RUN)))


if __name__ == "__main__":
    unittest.main()
