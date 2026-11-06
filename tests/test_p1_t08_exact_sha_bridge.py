"""Public-only policy guard for the exact instructor SHA; no private imports."""
import sys
from pathlib import Path
from unittest import TestCase
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import private_ci_bridge as bridge

class P1T08PinnedGateTests(TestCase):
    def test_exact_private_sha_is_pinned(self):
        self.assertEqual(bridge.PIN,'9a9f1fd328f273542205b82ddbca902fc31bb986')
    def test_new_gate_contains_complete_approved_python_contract_tests(self):
        suite=set(bridge.R01_R08_UNIT_FILES)
        self.assertEqual(len(suite),11)
        for name in ('test_p1_t08_r01_binding.py','test_p1_t08_supervisor_receipt.py',
                     'test_p1_t08_r02_fake_goal.py','test_p1_t08_r03_no_motion.py',
                     'test_p1_t08_r04_custody.py','test_p1_t08_r06_triplicate.py',
                     'test_p1_t08_r07_fault_suite.py','test_p1_t08_r08_release.py'):
            self.assertTrue(any(p.endswith(name) for p in suite))
    def test_fake_faults_and_gazebo_cannot_issue_real_goal(self):
        self.assertEqual(bridge.preloc_settings('gazebo3'),(3,False))
        self.assertEqual(bridge.preloc_settings('gazebo10'),(10,False))
        self.assertFalse(any('live' in x.lower() for x in bridge.R01_R08_UNIT_FILES))
