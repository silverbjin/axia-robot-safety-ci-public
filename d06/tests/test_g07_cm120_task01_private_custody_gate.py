"""Task01 private evidence canary: public CI must not run Goal without custody.
Contract tests are ROS-free. The actual sealed-secret push/readback is separate.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "d06/scripts/g07_task01_private_custody_canary.sh"

class TestPrivateCustodyGate(unittest.TestCase):
    def test_private_custody_is_required_before_goal(self):
        self.assertTrue(SCRIPT.is_file(), "TASK01_CUSTODY_PREGOAL_SCRIPT_MISSING_RED")
        src = SCRIPT.read_text()
        for marker in (
            "AXIA_G07_TASK01_PRIVATE_SHA256_CANARY_PASS",
            "GITHUB_ACTIONS",
            "AXIA_P0_SIM_ONLY",
            "AXIA_G07_TASK01_GOAL_ALLOWED",
            "AXIA_G07_EVIDENCE_WRITE_TOKEN",
            "sha256sum",
            "git -C",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, src)
    def test_push_and_fresh_readback_not_a_local_only_copy(self):
        src = SCRIPT.read_text() if SCRIPT.is_file() else ""
        self.assertIn("push", src, "TASK01_CUSTODY_REMOTE_PUSH_MISSING_RED")
        self.assertIn("fetch", src, "TASK01_CUSTODY_REMOTE_READBACK_MISSING_RED")
        self.assertIn("FETCH_HEAD", src, "TASK01_CUSTODY_REMOTE_SHA_READBACK_MISSING_RED")
    def test_instructor_evidence_branch_is_not_main_or_public(self):
        src = SCRIPT.read_text() if SCRIPT.is_file() else ""
        self.assertIn("evidence/g07-cm120-task01-20261117", src)
        self.assertIn("axia-robot-safety-instructor", src)
        self.assertNotIn("refs/heads/main", src)
        self.assertNotIn("upload-artifact", src)
    def test_script_is_not_a_goal_runner(self):
        src = SCRIPT.read_text() if SCRIPT.is_file() else ""
        for forbidden in ("ros2 action send_goal", "AXIA_G07_CI_SIM_GOAL_ALLOWED=1",
                          "YES-P2-G07-GOAL", "p2_no_goal_smoke_ci.sh"):
            self.assertNotIn(forbidden, src)

if __name__ == "__main__":
    unittest.main()
