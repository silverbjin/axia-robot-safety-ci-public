"""Public-only Instructor CI policy contract; stdlib, no ROS or private source."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs/operations/AXIA_INSTRUCTOR_PUBLIC_CI_ONLY_POLICY_20261121_KO.md"
WORKFLOW = ROOT / ".github/workflows/block-d-d13-instructor-public-sealed-l0.yml"
STUDENT_SHA = "89e94f78dce6537d8be032759f4bf6274d0d5996"
INSTRUCTOR_SHA = "32ee25c5ff6d4319d66eaf0652642a86b8e70751"

class PublicOnlyInstructorCIContract(unittest.TestCase):
    def test_documented_trust_and_status_policy(self):
        txt = POLICY.read_text(encoding="utf-8")
        for token in ("Public CI", "axia-instructor-sealed", "HOLD_PUBLIC_ONLY",
                      "main", "Instructor", "NOT_RUN", "RED", "GREEN"):
            self.assertIn(token, txt)

    def test_workflow_pins_exact_source_and_synthetic_contract(self):
        txt = WORKFLOW.read_text(encoding="utf-8")
        for token in (STUDENT_SHA, INSTRUCTOR_SHA, "Ran 10 tests", "test_d13_beginner_guide_contract.py", "test_d13_story_24_slides_contract.py", "PRIVATE_D13_STORY_24_SLIDES_PASS",
                      "test_d13_live_replay_contract.py",
                      "test_d13_live_replay_instructor_contract.py",
                      "PUBLIC_D13_LIVE_REPLAY_6_TESTS_1920X1080_HEADLESS_CHROME_PASS",
                      "PRIVATE_D13_LIVE_REPLAY_GUIDE_PASS",
                      "FAILED (failures=2)", "Ran 8 tests", "Ran 3 tests",
                      "85dd0fa35b2e7982b0c86020fdd4f4952e6a039f"):
            self.assertIn(token, txt)

    def test_private_token_access_is_only_in_guarded_job(self):
        txt = WORKFLOW.read_text(encoding="utf-8")
        public_job, protected = txt.split("  protected-instructor-l0:", 1)
        self.assertNotIn("secrets.AXIA_CLOUD_CI", public_job)
        self.assertIn("secrets.AXIA_CLOUD_CI", protected)
        self.assertIn("axia-instructor-sealed", protected)
        self.assertIn("release/p2-g06-cm-ttl-20261110", protected)
        self.assertIn("github.event_name == 'push'", protected)
        self.assertIn("persist-credentials: false", protected)

    def test_sanitization_and_ephemeral_cleanup(self):
        txt = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: always()", txt)
        self.assertIn("rm -rf -- instructor", txt)
        self.assertIn("PRIVATE_D13_L0_HOLD", txt)
        self.assertIn("PRIVATE_D13_L0_PASS", txt)
        self.assertIn("NO_ROS_GAZEBO_GOAL", txt)
        self.assertIn("private_d13_live_guide.log", txt)
        self.assertEqual(txt.count("  protected-instructor-l0:"), 1)

if __name__ == "__main__":
    unittest.main()
