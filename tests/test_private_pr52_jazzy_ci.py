import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/'scripts/private_pr52_jazzy_ci.py'

class TestPr52JazzyNoSimContract(unittest.TestCase):
    def test_exact_sha_pin_and_unmodified_shared_bridge(self):
        t=FILE.read_text()
        self.assertIn("PIN = '6bc579814c6037d40d644ce8d9f5046fa4a7d4c6'",t)
        self.assertIn("bridge.validate_private_commit(root)",t)
        self.assertIn("env['GITHUB_SHA']=PIN",t)
    def test_selected_jazzy_suite_has_no_real_fault_or_goal(self):
        t=FILE.read_text()
        self.assertIn("'P0_JAZZY_SAFE_LAUNCH'",t)
        self.assertIn("'JAZZY_MIDDLEWARE'",t)
        self.assertIn("'ROS_LIVE_FAKE_INPUT'",t)
        self.assertIn("--show-args >/dev/null",t)
        for forbidden in ('ros2 action send_goal','ros2 topic pub',
                          'ros2 service call','/axia/safety/start',
                          'upload-artifact','main_merge_authorized=True'):
            self.assertNotIn(forbidden,t.replace('No Gazebo, real /axia/safety/start, Goal, Fault injector, raw upload,',''))
    def test_no_real_scenario_or_acceptance_claim(self):
        t=FILE.read_text()
        self.assertIn("'gate_accepted':False",t)
        self.assertIn("'gazebo_executed':False",t)
        self.assertIn("'certified_estop_verified':False",t)
        self.assertIn("junit_failure_fingerprints",t)
