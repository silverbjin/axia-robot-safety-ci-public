"""No ROS needed: guard PR52 against accidental multi-minute Gazebo pushes."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEAVY = (ROOT / '.github/workflows/pr52-cloud-g00-real.yml').read_text(encoding='utf-8')
FAST_PATH = ROOT / '.github/workflows/pr52-fast-policy.yml'
REQUEST = '.github/axia/pr52-g00-3x.request'
BRANCH = 'feat/secure-instructor-cloud-bridge'


class PR52FastPolicyGate(unittest.TestCase):
    def test_heavy_only_on_explicit_simulation_request(self):
        trigger = HEAVY.split('permissions:', 1)[0]
        self.assertIn("  push:\n    branches: [" + BRANCH + "]\n    paths:\n      - '" + REQUEST + "'", trigger)
        self.assertIn('  workflow_dispatch:', trigger)
        self.assertNotIn('scripts/private_pr52_cloud_g00.py', trigger)
        self.assertNotIn('tests/test_private_pr52_cloud_g00.py', trigger)
        self.assertNotIn("- '.github/workflows/pr52-cloud-g00-real.yml'", trigger)

    def test_protected_job_is_restricted_to_owner_and_branch(self):
        self.assertIn("github.repository == 'silverbjin/axia-robot-safety-ci-public'", HEAVY)
        self.assertIn("github.actor == 'silverbjin'", HEAVY)
        self.assertIn("github.ref == 'refs/heads/" + BRANCH + "'", HEAVY)
        self.assertIn("github.event_name == 'push'", HEAVY)
        self.assertIn('environment:\n      name: axia-instructor-sealed', HEAVY)
        self.assertIn('ref: f646762edccb5a626caa7e66a488b5a3f721a6b7', HEAVY)
        self.assertIn('persist-credentials: false', HEAVY)
        self.assertNotIn('upload-artifact', HEAVY)

    def test_fast_ci_is_no_ros_no_private_secret(self):
        self.assertTrue(FAST_PATH.exists(), 'fast CI workflow must exist')
        fast = FAST_PATH.read_text(encoding='utf-8')
        self.assertIn('  push:', fast)
        self.assertIn('branches: [' + BRANCH + ']', fast)
        self.assertIn('cancel-in-progress: true', fast)
        self.assertIn('unittest discover', fast)
        self.assertIn('test_private_pr52_cloud_g00.py', fast)
        self.assertIn('test_pr52_ci_gates.py', fast)
        self.assertIn('test_pr52_block_classifier.py', fast)
        for forbidden in ('apt-get', 'ros:', 'ros-jazzy-', '_instructor_private',
                          'secrets.', 'AXIA_CLOUD_CI', 'upload-artifact'):
            self.assertNotIn(forbidden, fast)

    def test_heavy_keeps_one_goal_per_cold_start_and_cleanup(self):
        self.assertIn('scripts/private_pr52_cloud_g00.py --private-root _instructor_private', HEAVY)
        self.assertIn('rm -rf _instructor_private', HEAVY)
        self.assertIn('cancel-in-progress: false', HEAVY)


if __name__ == '__main__':
    unittest.main()
