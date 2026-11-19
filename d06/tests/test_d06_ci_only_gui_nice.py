"""G07 #44535830485 real Gazebo: post-READY native Scan .300409s,
native Clock local RTF .374704. Try one CI-only performance hypothesis:
lower only GUI clients' CPU priority under Xvfb to favor physics/Nav2.
Never renice Gazebo server, CM, Guard, Supervisor or NVIDIA Owner WSLg.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
STUDENT=ROOT/"student" if (ROOT/"student").is_dir() else ROOT.parent/"student"
SRC=STUDENT/"block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh"
WF=ROOT/".github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml"

class ScopedCiGuiPriority(unittest.TestCase):
    def test_scope_only_real_ci_sensor_no_goal_and_leave_wslg_owner_default(self):
        src=SRC.read_text()
        self.assertIn('AXIA_D06_L2_GUI_NICE_ONLY',src)
        self.assertIn('"${GITHUB_ACTIONS:-}" == true',src)
        self.assertIn('"${AXIA_G07_CI_SENSOR_TRUTH_NO_GOAL:-0}" == 1',src)
        self.assertIn('"$SENSOR_NO_GOAL" == 1',src)
        self.assertIn('setsid nice -n 15 gz sim -g',src)
        self.assertIn('setsid nice -n 15 rviz2 -d',src)
        self.assertIn('setsid gz sim -g',src)
        self.assertIn('setsid rviz2 -d',src)
        gui_only=src[src.index('  # CI Xvfb-only single hypothesis:'):
                     src.index('\n  sleep 3',src.index('  # CI Xvfb-only single hypothesis:'))]
        # Historical Task03 code elsewhere contains taskset; don't reject
        # unrelated, already-proven paths while auditing CI viewer branch.
        self.assertNotIn('renice -n -',gui_only)
        self.assertNotIn('taskset -c',gui_only)
        self.assertNotIn('nice -n -',gui_only)
        self.assertIn('  else\n     setsid gz sim -g',gui_only)

    def test_actual_l2_explicitly_opts_in_nice_without_safety_change(self):
        w=WF.read_text()
        self.assertIn("AXIA_D06_L2_GUI_NICE_ONLY: '15'",w)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '0'",w)
        self.assertIn("AXIA_G07_NO_GOAL_ORDERED_SHUTDOWN: '1'",w)
        self.assertIn("assert gap<=.300",w)

if __name__=="__main__":unittest.main()
