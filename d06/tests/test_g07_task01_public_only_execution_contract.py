"""G07 Task01 public-only, exactly one diagnostic Goal: CI fail-closed contract.

Static ROS-free test. Never approves release; does not fetch private source.
"""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/axia-g07-task01-public-only-one-diagnostic-l2-20261117.yml"
STUDENT_SHA="6a3047b5aa219687f5fc918e467cea5115d3d482"

class PublicOnlyTask01Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=WF.read_text(encoding="utf-8")

    def test_fixed_public_student_runtime_exact_sha(self):
        self.assertIn("repository: silverbjin/axia-robot-safety-student",self.source)
        self.assertIn("ref: "+STUDENT_SHA,self.source)
        self.assertIn("git -C runtime rev-parse HEAD",self.source)

    def test_no_private_repository_or_secret_anywhere_in_execution(self):
        self.assertNotIn("axia-robot-safety-instructor",self.source)
        self.assertNotIn("AXIA_CLOUD_CI",self.source)
        self.assertNotIn("axia-instructor-sealed",self.source)
        self.assertNotIn("secrets.",self.source)
        self.assertIn("permissions:",self.source)
        self.assertIn("contents: read",self.source)

    def test_exact_single_sim_goal_and_original_runner_only(self):
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '1'",self.source)
        self.assertIn("AXIA_P0_SIM_ONLY: '1'",self.source)
        self.assertIn("bash scripts/p2_no_goal_smoke_ci.sh",self.source)
        self.assertIn("timeout --signal=TERM --kill-after=10s 900s",self.source)
        self.assertIn("AXIA_G07_OWNER_STARTUP_PARITY: '1'",self.source)
        self.assertNotIn("ros2 action send_goal",self.source)

    def test_same_session_first_gap_and_safe_public_allowlist(self):
        self.assertIn("g07_task01_extract_public_gap.py",self.source)
        self.assertIn("AXIA_G07_CM120_TF_DIAG_FILE",self.source)
        self.assertIn("SHA256SUMS.txt",self.source)
        self.assertIn("first_gap_sanitized.json",self.source)
        self.assertIn("if-no-files-found: error",self.source)
        self.assertNotIn("path: /tmp/axia_task01_raw",self.source)

    def test_diagnostic_is_not_release_and_no_auto_merge(self):
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",self.source)
        self.assertIn("CM120_TRACER_OFF_RELEASE=HOLD",self.source)
        self.assertNotIn("CM120_TRACER_OFF_RELEASE=PASS",self.source)
        self.assertNotIn("pull_request_target:",self.source)

if __name__=="__main__":
    unittest.main()
