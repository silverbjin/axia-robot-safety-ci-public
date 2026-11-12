"""Public-only regression for G07 Owner bootstrap's exact proven source.

No private repository checkout, ROS, Gazebo, Goal or hardware action here.
The real Harmonic/Nav2 L2 evidence is immutable and independently linked.
"""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts/axia_p2_g07_ci_pass_owner_wsl2_once.sh"
APPROVED = ROOT / ".github/workflows/axia-p2-g07-ci-real-gazebo-moving-goal-l2.approved-trigger"
L2_WORKFLOW = ROOT / ".github/workflows/axia-p2-g07-ci-real-gazebo-moving-goal-l2.yml"
INSTRUCTOR_SHA = "19ea30fa936fe2218cef4265f05211dc5358d1e8"
SUCCESSFUL_L2_RUN = "43149852597"
OLD_INSTRUCTOR_SHA = "cc92327d1ae4a17d331d06e845437760ca2bdafe"
OLD_L2_RUN = "43072749608"
RUNTIME_DIGEST = "sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e"


class G07OwnerBootstrapLatestPin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = BOOTSTRAP.read_text(encoding="utf-8")

    def test_red_latest_exact_sha_and_verified_l2_evidence(self):
        self.assertIn("readonly PRIVATE_SHA='" + INSTRUCTOR_SHA + "'", self.script)
        self.assertIn("readonly CI_L2_RUN='" + SUCCESSFUL_L2_RUN + "'", self.script)
        self.assertNotIn(OLD_INSTRUCTOR_SHA, self.script)
        self.assertNotIn("CI_L2_RUN='" + OLD_L2_RUN + "'", self.script)
        approved = APPROVED.read_text(encoding="utf-8")
        workflow = L2_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("private_source_sha=" + INSTRUCTOR_SHA, approved)
        self.assertIn("ref: " + INSTRUCTOR_SHA, workflow)
        self.assertIn(RUNTIME_DIGEST, workflow)

    def test_self_check_is_no_goal_and_has_current_evidence(self):
        syntax = subprocess.run(["bash", "-n", str(BOOTSTRAP)], capture_output=True, text=True)
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        result = subprocess.run(["bash", str(BOOTSTRAP), "--self-check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "AXIA_G07_CI_PASS_OWNER_BOOTSTRAP_STATIC_PASS "
            + "private_sha=" + INSTRUCTOR_SHA
            + " ci_l2=" + SUCCESSFUL_L2_RUN
            + " OWNER_L3_NOT_RUN",
        )

    def test_no_tty_fails_closed_without_goal(self):
        result = subprocess.run(
            ["bash", str(BOOTSTRAP)], input="", capture_output=True, text=True, timeout=12
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("real controlling TTY required; NO_GOAL", result.stderr)

    def test_owner_authority_and_private_checkout_are_unchanged(self):
        s = self.script
        self.assertIn("PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'", s)
        self.assertIn('gh auth status', s)
        self.assertIn('git -C "$WORK/instructor" fetch --no-tags --depth 1 origin "$PRIVATE_SHA"', s)
        self.assertIn('checkout --detach "$PRIVATE_SHA"', s)
        self.assertIn('[[ "$ACTUAL" == "$PRIVATE_SHA" ]]', s)
        self.assertIn('[[ -z "$(git -C "$WORK/instructor" status --porcelain)" ]]', s)
        self.assertIn('[[ -t 0 && -t 1 && -r /dev/tty ]]', s)
        self.assertIn('export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"', s)
        self.assertIn('bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh"', s)
        self.assertIn('--case G07 --mvp-relocated-obstacle', s)
        self.assertIn("YES-P2-G07-GOAL", s)
        self.assertIn("SIMULATION ONLY", s)
        self.assertIn("SW Stop != certified E-Stop.", s)
        self.assertNotRegex(s, r"(?m)^\s*(?:echo|printf|yes)\s+['\"]?YES-P2-G07-GOAL")
        self.assertNotIn("--case G05", s)
        self.assertNotIn("--case G06", s)

    def test_negative_mutation_old_pin_is_detected(self):
        def matches_current_pin(text):
            return (
                "readonly PRIVATE_SHA='" + INSTRUCTOR_SHA + "'" in text
                and "readonly CI_L2_RUN='" + SUCCESSFUL_L2_RUN + "'" in text
            )
        self.assertFalse(matches_current_pin(self.script.replace(INSTRUCTOR_SHA, OLD_INSTRUCTOR_SHA)))
        self.assertFalse(matches_current_pin(self.script.replace(SUCCESSFUL_L2_RUN, OLD_L2_RUN)))


if __name__ == "__main__":
    unittest.main()
