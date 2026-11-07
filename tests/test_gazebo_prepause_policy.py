"""Public-only, fail-closed experiment policy; no instructor import."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/p1-t08-gazebo3-prepause.yml'

class TestPrepausePolicy(unittest.TestCase):
    def test_exact_sha_and_no_goal_protections(self):
        text = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('ref: 59805dc98ef27a3eb1efee8095406bb3fc93bd3a', text)
        self.assertIn('name: axia-instructor-sealed', text)
        self.assertIn('--gate gazebo3-prepause', text)
        self.assertIn("github.actor == 'silverbjin'", text)
        self.assertIn("github.event_name == 'push'", text)
        self.assertIn('persist-credentials: false', text)
        self.assertIn('rm -rf _instructor_private', text)
        self.assertNotIn('actions/upload-artifact', text)
        self.assertNotIn('ros2 action send_goal', text)
        self.assertNotIn('/axia/safety/start', text)
        self.assertNotIn('allow_fault_injection:=true', text)

    def test_not_a_release_or_stability_gate(self):
        text = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('PREPAUSE_EXPERIMENT_ONLY', text)
        self.assertIn('G00/G03/G04 REAL ACCEPTANCE=NOT_RUN', text)
        self.assertNotIn('GAZEBO_10X', text)
        self.assertNotIn('gate_accepted=true', text)
