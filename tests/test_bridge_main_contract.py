"""CI-06 RED contracts: private bridge MUST be safe when eventually targeted at main.

The workflow must be reviewable via a public PR without granting read
access to the instructor repository or emitting private artifacts.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/instructor-sealed-bridge.yml"
SCRIPT = ROOT / "scripts/private_ci_bridge.py"
TESTS = ROOT / "tests/test_private_ci_bridge.py"

class MainBranchBridgeContract(unittest.TestCase):
    def text(self):
        return WORKFLOW.read_text(encoding="utf-8")

    def test_all_bridge_components_present_in_staging(self):
        for path in (WORKFLOW, SCRIPT, TESTS):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), f"missing staged bridge component: {path.name}")

    def test_private_jobs_only_explicit_owner_manual_main_dispatch(self):
        value = self.text()
        self.assertIn("workflow_dispatch:", value)
        self.assertIn("run_private:", value)
        for rule in ("github.repository == 'silverbjin/axia-robot-safety-ci-public'",
                     "github.actor == 'silverbjin'",
                     "github.ref == 'refs/heads/main'",
                     "github.event_name == 'workflow_dispatch'",
                     "inputs.run_private == true"):
            with self.subTest(rule=rule):
                self.assertGreaterEqual(value.count(rule), 3, rule)
        self.assertNotIn("pull_request_target:", value)

    def test_private_checkout_pin_and_env_secrets(self):
        value = self.text()
        src = SCRIPT.read_text(encoding="utf-8")
        match = re.search(r"^PIN = '([a-f0-9]{40})'$", src, re.M)
        self.assertIsNotNone(match)
        self.assertEqual(value.count("ref: " + match.group(1)), 2)
        self.assertGreaterEqual(value.count("name: axia-instructor-sealed"), 2)
        self.assertGreaterEqual(value.count("persist-credentials: false"), 3)
        self.assertNotIn("upload-artifact@", value)
        self.assertNotIn("pull_request_target:", value)

    def test_public_pr_never_needs_secret_or_private_repo(self):
        value = self.text()
        self.assertIn("pull_request:", value)
        self.assertIn("public-fail-closed-contracts:", value)
        self.assertIn("python3 -m unittest discover -s tests -p test_private_ci_bridge.py -v", value)
        self.assertIn("python3 -m unittest discover -s tests -p test_bridge_main_contract.py -v", value)
        self.assertNotIn("env: {PRIVATE_READ_TOKEN", value)

    def test_long_gazebo_runs_cannot_be_cancelled_by_push(self):
        value = self.text()
        self.assertIn("cancel-in-progress: false", value)
        self.assertNotIn("cancel-in-progress: true", value)

    def test_public_pr_does_not_fail_due_to_skipped_private_jobs(self):
        value = self.text()
        self.assertIn("instructor-prelocal-aggregate:", value)
        self.assertIn("always()", value)
        self.assertIn("needs.instructor-gazebo10.result", value)
        self.assertIn("gate_accepted=false", value)
        self.assertIn("certified_estop=false", value)

if __name__ == "__main__":
    unittest.main()
