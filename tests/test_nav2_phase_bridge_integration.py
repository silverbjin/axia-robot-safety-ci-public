"""Strict public contract: the full CI uses the validated redacted v2 oracle."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TestV2PhaseBridgeIntegration(unittest.TestCase):
    def test_full_bridge_uses_bounded_tail_not_full_private_log(self):
        text=(ROOT/'scripts/private_ci_bridge.py').read_text()
        self.assertIn('from private_nav2_phase_oracle_v2 import classify_nav2_shutdown_phase',text)
        self.assertIn('from private_nav2_phase_smoke1 import tail_private_log',text)
        self.assertIn("record['nav2_log_read'] = read_mode",text)
        self.assertNotIn("raw_log = (logfile.read_text",text)
        self.assertNotIn("record['launch_log']",text)

    def test_10x_still_requires_actual_success_and_no_goal(self):
        text=(ROOT/'.github/workflows/instructor-sealed-bridge.yml').read_text()
        self.assertIn("matrix:\n        gate: [unit-middleware, fake-faults, gazebo3]",text)
        self.assertIn('python3 scripts/private_ci_bridge.py --private-root _instructor_private --gate gazebo10',text)
        self.assertIn('if [[ "$PUBLIC" != success || "$CORE" != success || "$GAZEBO10" != success ]]',text)
        self.assertIn("G00_REAL_GOAL=NOT_RUN",text)
        self.assertNotIn('continue-on-error: true',text)
