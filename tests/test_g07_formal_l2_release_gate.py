"""Formal release CI must not treat educational visual HOLD as real L2 PASS."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/axia-g07-fv17-owner-evidence-parity-native-l2.yml"


class FormalReleaseGate(unittest.TestCase):
    def test_real_goal_l2_fallback_never_passes_formal_release(self):
        s=WORKFLOW.read_text()
        marker="AXIA_G07_TASK04_MVP_VISUAL_L2_PASS_FORMAL_LOCALIZATION_SHUTDOWN_HOLD"
        self.assertIn(marker,s)
        fallback=s[s.index(marker):s.index("            fi",s.index(marker))]
        self.assertIn("exit 3",fallback)
        self.assertNotIn("exit 0",fallback)

    def test_real_two_cycles_and_actual_student_sha_are_pinned(self):
        s=WORKFLOW.read_text()
        self.assertIn("fail-fast: false",s)
        self.assertIn("cycle: [1, 2]",s)
        self.assertIn("ref: 59f8ab6acb5107dcdcfd2bf37b7c16b881b7130c",s)
        self.assertIn("AXIA_G07_TASK04_NATIVE_MOVING_GUI_XVFB_L2_PASS",s)
        self.assertIn("verify_real_goal_and_guard_evidence || exit 3",s)
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false",s)


if __name__=="__main__":
    unittest.main()
