"""Real failed first Scan pair MUST be compared to same-session existing bag."""
import unittest
from pathlib import Path
FLOW=Path(__file__).resolve().parents[1]/".github/workflows/axia-g07-fv17-owner-evidence-parity-native-l2.yml"
class FirstScanBagIntegration(unittest.TestCase):
    def test_numeric_only_bag_first_pair_on_any_run_result(self):
        s=FLOW.read_text()
        self.assertIn("g07_scan_rosbag_first_boundary.py",s)
        self.assertIn('if: always()',s)
        self.assertIn('--first-report "$GITHUB_WORKSPACE/native/g07_ci_scan_pregoal.json"',s)
        self.assertIn('--bag-root "$GITHUB_WORKSPACE/native/rosbag2"',s)
        self.assertIn('public_evidence/first_scan_rosbag_exact_pair.json',s)
        self.assertIn('public_evidence/first_scan_rosbag_exact_pair.sha256',s)
        self.assertIn("FIRST_SCAN_ROSBAG_EXACT_PAIR",s)
        self.assertNotIn("public_evidence/rosbag2",s)
        self.assertNotIn("raw_goal_uuid",s)
if __name__=="__main__":unittest.main()
