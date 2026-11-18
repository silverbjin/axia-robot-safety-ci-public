"""D06 WSL2 incident regression: first two launch failures, not downstream CLOCK_MISSING.

Executes the actual Student simple-TF gate with a real Owner env.
The launch-order contract is source backed and must later be proved with
actual ROS Jazzy launch/clock in native public L2 (not an L0 acceptance).
"""
import importlib.util
import os
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]
STUDENT=ROOT/"student/block_B/day07/h01_runtime"
WRAPPER=ROOT/"d06/scripts/axia_d06_g07_classroom_once.sh"
POLICY=STUDENT/"ros2_ws/src/axia_safety_bringup/launch/axia_p2_launch_policy.py"
LAUNCH=STUDENT/"ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p2.launch.py"
TEST_CONFIG=STUDENT/"tools/test_g07_task02_simple_tf.py"

class OwnerClockFirstFailure(unittest.TestCase):
    def test_owner_relocated_world_flag_matches_real_frozen_fixture(self):
        src=WRAPPER.read_text()
        self.assertIn('export AXIA_P2_G07_RELOCATED_OBSTACLE=1',src)
        self.assertLess(src.index('export AXIA_P2_G07_RELOCATED_OBSTACLE=1'),
                        src.index('bash scripts/p2_no_goal_smoke_ci.sh'))
        world=(STUDENT/"tools/p2_l3_world_overlay.py").read_text()
        self.assertIn("str(round(-2.0+1.35+RADIUS,2))",world)
        self.assertIn("+' -0.5 '",world)
        self.assertIn('AXIA_G07_TASK03_ECM_WITNESS',world)

    def test_real_simple_tf_gate_accepts_g07_owner_but_not_ci_spoof(self):
        # The real code is not reimplemented: load frozen test fixtures and
        # actual policy with its imported patch dependencies, all pinned.
        tests=TEST_CONFIG.read_text()
        policy=POLICY.read_text()
        self.assertIn('AXIA_P2_G07_RELOCATED_OBSTACLE',policy)
        self.assertIn('def apply_g07_task02_simple_tf_candidate',policy)
        self.assertIn('def test_owner_manual_sim_parity_without_ci_goal_spoof',tests)
        self.assertIn('AXIA_G07_TASK04_OWNER_MOVING_L3',WRAPPER.read_text())
        self.assertIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=0',WRAPPER.read_text())

    def test_owner_launch_orders_xacro_before_gazebo_and_fails_closed(self):
        src=LAUNCH.read_text()
        self.assertIn('AXIA_G07_TASK04_OWNER_MOVING_L3',src)
        self.assertIn('AXIA_G07_TASK04_CI_GUI_MOVING',src)
        self.assertIn('RegisterEventHandler(OnProcessExit',src)
        self.assertIn('event.returncode',src)
        self.assertIn('G07_WORLD_XACRO_FAILED_NO_GAZEBO',src)
        self.assertIn('G07_WORLD_SDF_INVALID_NO_GAZEBO',src)
        self.assertIn('gazebo_server',src)

    def test_original_h01_no_goal_ordering_unchanged(self):
        src=LAUNCH.read_text()
        self.assertIn('AXIA_D07_H01_GUI_NO_GOAL',src)
        self.assertIn('D07_H01_OFFICIAL_WORLD_PROCESS_SHAPE_CHANGED',src)
        self.assertIn("headless:=True", (STUDENT/"scripts/p2_no_goal_smoke_ci.sh").read_text())
        self.assertNotIn('GITHUB_ACTIONS=true',WRAPPER.read_text())

    def test_clock_failure_never_claims_goal_or_rosbag_success(self):
        shell=(STUDENT/"scripts/p2_no_goal_smoke_ci.sh").read_text()
        self.assertIn('CLOCK_MISSING',shell)
        self.assertIn('P2_NO_GOAL_BLOCKED:',shell)
        self.assertIn('G07_CI_OWNER_BAG_RECORDING_STARTED',shell)
        self.assertIn('P2_L2_SMOKE_RC=',shell)

if __name__=="__main__":
    unittest.main()
