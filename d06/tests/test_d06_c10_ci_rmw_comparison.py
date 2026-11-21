"""C10 strict public Gazebo Linux Xvfb RMW vendor diagnostic.
Actual rmw_fastrtps_cpp C09: Student Safety 365.478ms vs independent ROS
102.191ms, localization manage_nodes no ACK after 30s. A single
CI-only rmw_cyclonedds_cpp candidate can discriminate RMW behavior.
NO WSLg Owner defaults, DDS QoS, sensor Hz, Scan300 or Goal changes.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml"
OWNER=ROOT/"d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh"
OUTER=ROOT/"d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh"

class C10RmwTrial(unittest.TestCase):
    def test_ci_only_actual_rmw_switch_with_existing_signed_apt(self):
        s=WF.read_text()
        self.assertIn("RMW_IMPLEMENTATION: rmw_cyclonedds_cpp",s)
        self.assertIn("CI_ONLY_RMW_CYCLONEDDS_L2_NO_GOAL",s)
        self.assertIn("ros-jazzy-rmw-cyclonedds-cpp",s)
        self.assertIn("apt-get update",s)
        self.assertNotIn("Acquire::AllowInsecureRepositories",s)
        self.assertNotIn("trusted=yes",s)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '0'",s)

    def test_same_run_actual_rmw_proof_before_pass(self):
        s=WF.read_text()
        self.assertIn('nav["rmw_implementation_identifier"]=="rmw_cyclonedds_cpp"',s)
        self.assertIn("AXIA_D06_C10_RMW_CYCLONEDDS_ACTUAL_L2_VERIFIED",s)
        self.assertLess(s.index('nav["rmw_implementation_identifier"]'),
                        s.index('assert rc==0'))
        self.assertIn("POST_READY_NATIVE_SCAN300_FIRST_BREACH",s)
        self.assertIn("POST_READY_SAFETY_SCAN300_FIRST_BREACH",s)
        self.assertIn("GAZEBO_SERVER_EXIT0_NOT_PROVEN_L2",s)
        self.assertIn("AXIA_D06_L2_GUI_PRE_NAV2_READY: '1'",s)

    def test_wslg_owner_source_unchanged_with_no_rmw_vendor_override(self):
        for p in (OWNER,OUTER):
            s=p.read_text()
            self.assertNotIn("RMW_IMPLEMENTATION=rmw_cyclonedds_cpp",s)
            self.assertNotIn("export RMW_IMPLEMENTATION=",s)
            self.assertNotIn("SCAN_TTL_SEC=.5",s)

if __name__=="__main__":
    unittest.main()
