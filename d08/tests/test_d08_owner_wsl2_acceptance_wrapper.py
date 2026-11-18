"""Release-only immutable wrapper contract; L0 is not WSLg L3."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / 'd08/scripts/d08_owner_wsl2_acceptance_20261118.sh'


class TestOwnerWsl2AcceptanceWrapper(unittest.TestCase):
    def test_owner_wrapper_exists_and_is_bash_valid(self):
        self.assertTrue(WRAPPER.is_file(), 'D08_OWNER_WRAPPER_MISSING_RED')
        subprocess.run(['bash', '-n', str(WRAPPER)], check=True)

    def test_verified_green_sha_and_bootstrap_blob_are_immutable(self):
        source = WRAPPER.read_text()
        self.assertIn('342c6355b27af5b8b11a79b7e345820be18a581f', source)
        self.assertIn('bad5b738e57827a102ebe56595d3b4b7dc3e6f83', source)
        self.assertIn('git hash-object', source)
        self.assertIn('raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public', source)
        self.assertNotIn('refs/heads/main', source)
        self.assertNotIn('refs/pull/166/head', source)

    def test_self_check_is_non_ros_and_l3_fail_closed(self):
        r = subprocess.run(['bash', str(WRAPPER), '--self-check'], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=8)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('D08_OWNER_WRAPPER_L0_PASS_NO_ROS_GAZEBO_RUN', r.stdout)
        source = WRAPPER.read_text()
        self.assertIn('D08_OWNER_WSLG_VISUAL=OWNER_CONFIRM_REQUIRED', source)
        self.assertIn('D08_MOVING_E2E_ACCEPTED=HOLD', source)
        self.assertIn('D08_OWNER_RUNTIME=BLOCKED', source)
        self.assertIn('pipefail', source)
        self.assertIn('D08_OWNER_ACCEPTANCE_RUN_LOG=', source)


if __name__ == '__main__':
    unittest.main()
