"""Fast, non-ROS regressions for allowlisted public PR52 blocker output."""
from pathlib import Path
import importlib.util
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('private_pr52_cloud_g00', SCRIPTS / 'private_pr52_cloud_g00.py')
LIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LIVE)


class PR52BlockedClassifier(unittest.TestCase):
    def classify(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'private-console.log'
            p.write_text(text, encoding='utf-8')
            return LIVE._blocked_phase(p)

    def test_fake_ros_preflight_failure_is_categorized(self):
        self.assertEqual(self.classify('[10:00] [BLOCKED] fake ROS regressions failed\n'),
                         'PREFLIGHT_FAKE_ROS_FAILED')

    def test_successful_guard_message_is_not_false_positive(self):
        self.assertEqual(self.classify('[INFO] CLOUD_CI_G00_ONLY passed\n'),
                         'NO_RECORDED_BLOCKED_LINE')

    def test_no_private_console_excerpt_in_output(self):
        secret = 'PRIVATE_PATH_DO_NOT_ECHO'
        self.assertEqual(self.classify('[BLOCKED] ' + secret + '\n'),
                         'BLOCKED_UNCLASSIFIED')

    def test_specific_pre_goal_block_beats_status_noise(self):
        self.assertEqual(self.classify('CLOUD_CI_G00_ONLY PASS\n[BLOCKED] PRE_GOAL_BLOCKED\n'),
                         'PRE_GOAL_BLOCKED')

    def test_missing_file_is_enum_only(self):
        self.assertEqual(LIVE._blocked_phase(Path('/this/path/is/absent/private.log')),
                         'PRIVATE_CONSOLE_MISSING')


if __name__ == '__main__':
    unittest.main()
