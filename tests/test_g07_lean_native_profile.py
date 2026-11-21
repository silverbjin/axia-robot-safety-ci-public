"""G07 lean profile CI contract; no safety-logic changes or TTL relaxation.

RED on the existing diagnostic-heavy workflow; GREEN by turning off ONLY
nonessential observer heartbeat/I/O and independent RMW witness in Native.
This checks the static admission profile, not actual Gazebo/WSL2 stability.
"""
from pathlib import Path
import unittest

WORKFLOW=Path(__file__).resolve().parents[1]/".github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml"


class LeanProfileContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow=WORKFLOW.read_text()

    def test_lean_branch_native_two_independent_cycles(self):
        w=self.workflow
        self.assertIn("'perf/g07-lean-native-no-heavy-probe-20261121'",w)
        self.assertIn("cycle: [1, 2]",w)
        self.assertIn("AXIA_G07_LEAN_PROFILE: '1'",w)

    def test_disable_only_nonessential_io_and_independent_subscriber(self):
        w=self.workflow
        self.assertIn("AXIA_G07_OBSERVER_IO_PROBE: '0'",w)
        self.assertIn('test "$AXIA_G07_OBSERVER_IO_PROBE" = 0',w)
        self.assertIn("AXIA_G07_CI_INDEPENDENT_CM_WITNESS: '0'",w)
        self.assertIn('if [[ "$AXIA_G07_CI_INDEPENDENT_CM_WITNESS" == 1 ]];then',w)
        self.assertIn("AXIA_G07_LEAN_INDEPENDENT_CM_WITNESS_DISABLED",w)

    def test_preserve_real_safety_and_sensor_contract(self):
        w=self.workflow
        self.assertIn("AXIA_G07_DEPTH_SENSOR_ENABLED: '0'",w)
        self.assertIn("AXIA_G07_EVENTS_EXECUTOR_AB: '0'",w)
        self.assertIn("AXIA_G07_CI_EXECUTOR_WAIT_BOUNDED_AB: '0'",w)
        self.assertIn("AXIA_G07_CI_EXECUTOR_GUARD_WAKE_AB: '0'",w)
        self.assertIn("AXIA_G07_SCAN_PREFLIGHT_STRICT: '1'",w)
        self.assertIn("AXIA_G07_TASK03_ECM_WITNESS: '1'",w)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '1'",w)
        self.assertIn("AXIA_G07_NATIVE_L2_GUARD_SUPERVISOR_ACTUAL_CHILD_EXIT0_PASS",w)
        self.assertIn("G07_REAL_DEPTH_ABSENT_SCAN_PRESENT_PASS",w)
        self.assertIn("AXIA_G07_NATIVE_MOVING_HEADLESS_SAFETY_L2_PASS",w)

    def test_no_changes_to_student_or_safety_node_runtime(self):
        w=self.workflow
        self.assertIn("e1241a2f3cc4fe85412b68ce026c337312d56a02",w)
        self.assertIn("libaxia_g07_s02_ecm_witness.so",w)
        self.assertIn("first_postgoal_rmw_heartbeat_join.json",w)


if __name__=="__main__":
    unittest.main()
