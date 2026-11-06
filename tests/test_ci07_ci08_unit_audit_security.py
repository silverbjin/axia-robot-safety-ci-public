"""CI07/CI08 public contract tests. Never import or load instructor private code."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/ci07-ci08-private-unit-audit.yml"

class IsolatedUnitAuditSecurityTests(unittest.TestCase):
    def test_workflow_exists(self):
        self.assertTrue(WF.is_file())

    def test_source_and_identity_are_statically_pinned(self):
        x = WF.read_text(encoding="utf-8")
        self.assertIn("ref: 063d1788043b313ac9ec3b6ed91a6f972de3d965", x)
        self.assertIn("ref: 516e86d2cb12c72251f1a16a2c9201afde757a58", x)
        self.assertIn("github.repository == 'silverbjin/axia-robot-safety-ci-public'", x)
        self.assertIn("github.actor == 'silverbjin'", x)
        self.assertIn("github.ref == 'refs/heads/feat/secure-instructor-cloud-bridge'", x)
        self.assertIn("github.event_name == 'push'", x)
        self.assertNotIn("pull_request_target:", x)

    def test_private_token_only_in_environment_gated_unit(self):
        x = WF.read_text(encoding="utf-8")
        self.assertIn("name: axia-instructor-sealed", x)
        self.assertIn("secrets.AXIA_CLOUD_CI", x)
        self.assertIn("persist-credentials: false", x)
        self.assertIn("fetch-depth: 1", x)
        self.assertNotIn("upload-artifact@", x)
        self.assertNotIn("continue-on-error: true", x)

    def test_no_motion_or_external_logging(self):
        x = WF.read_text(encoding="utf-8")
        self.assertIn("python3 -m unittest discover", x)
        self.assertIn("test_p1_private_evidence_custody.py", x)
        self.assertIn("test_p1_cloud_g00_admission.py", x)
        self.assertNotIn("ros2 launch", x)
        self.assertNotIn("ros2 topic pub", x)
        self.assertNotIn("send_goal", x)
        self.assertNotIn("gazebo", x.lower().replace("no-gazebo", ""))
        self.assertNotIn("tail -", x)
        self.assertNotIn("cat \"$LOG\"", x)
        self.assertIn("gate_accepted=false", x)
        self.assertIn("certified_estop=false", x)

    def test_private_stdout_is_never_streamed_and_run_is_non_cancellable(self):
        x = WF.read_text(encoding="utf-8")
        self.assertIn('> "$LOG" 2>&1', x)
        self.assertIn('grep -Eq "^Ran ', x)
        self.assertIn('grep -qx "OK" "$LOG"', x)
        self.assertIn('rm -rf _instructor_private', x)
        self.assertIn("cancel-in-progress: false", x)

if __name__ == "__main__":
    unittest.main()
