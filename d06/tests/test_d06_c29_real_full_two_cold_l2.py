"""C29-03 full same-world two cold-run contract.

No claim of WSL2 GPU parity. This is a *source contract*; only Actions job
results plus raw first-failure evidence can prove the real L2 matrix.
"""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/".github/workflows/axia-d06-c29-nogoal-full-two-cold-l2.yml"

class C29TwoColdL2Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=FILE.read_text()

    def test_two_real_independent_matrix_runners_not_two_fixture_loops(self):
        s=self.source
        self.assertRegex(s,r"(?m)^\s+matrix:\s*$")
        self.assertRegex(s,r"(?m)^\s+cycle:\s*\[1,\s*2\]")
        self.assertIn("max-parallel: 2",s)
        self.assertIn("runs-on: ubuntu-24.04",s)
        self.assertIn("container:",s)
        self.assertIn("ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e",s)
        self.assertIn("axia-d06-c29-cold-cycle-",s)

    def test_pins_actual_c27_student_source_and_fastdds(self):
        s=self.source
        self.assertIn("ref: 6c79c09d91f13c81961492eb30e66d99d307831c",s)
        self.assertIn("cc3c64f7ae769a11d9daad4acdbdb48141253f7c",s)
        self.assertIn("72a117d9a1b22748ffd16171d213916c095a623e",s)
        self.assertIn("RMW_IMPLEMENTATION: rmw_fastrtps_cpp",s)
        self.assertIn('nav["rmw_implementation_identifier"]=="rmw_fastrtps_cpp"',s)
        self.assertNotIn("RMW_IMPLEMENTATION: rmw_cyclonedds_cpp",s)
        self.assertNotIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '1'",s)

    def test_keeps_full_real_gazebo_nav2_cm_scan_and_fail_closed(self):
        s=self.source
        for token in (
             "Actual same-world Gazebo and official Nav2 CM NO_GOAL teardown",
             "d06_gz_scan_receipts.jsonl",
             "d06_ros_scan_receipts.jsonl",
             "d06_g07_scan_delivery_layer.json",
             "g07_wslg_sensor_truth.json",
             "g07_ordered_shutdown.json",
             "g07_shutdown_audit.json",
             'assert gap<=.300',
             '"NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE"',
             'assert nav["navigation_ack"] is True and nav["localization_ack"] is True',
             'assert audit["cm_exit_code"]==0',
             '"FORCED" not in teardown',
             'assert gz_clean and not gz_bad',
             'G07_GAZEBO_SERVER_NATIVE_EXIT0_BEFORE_GROUP_SIGINT',
             'AXIA_D06_G07_NO_GOAL_STRICT_INTEGRATED_L2_PASS_SENSOR300_NAV2_ACK_CM0_GZ0',
             'C29_L2_NOT_WSL2_NOT_WSLG_D3D12',
        ):
            self.assertIn(token,s,token)

    def test_exact_cycle_evidence_with_no_parent_ack_substitution(self):
        s=self.source
        self.assertIn("retention-days: 14",s)
        self.assertIn("matrix.cycle",s)
        self.assertIn("if: always()",s)
        self.assertIn("source_stamp_ns",s)
        self.assertIn("POST_READY_",s)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",s)
        self.assertIn("CERTIFIED_ESTOP=false",s)

if __name__=="__main__": unittest.main()
