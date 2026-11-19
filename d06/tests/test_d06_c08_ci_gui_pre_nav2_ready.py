"""C08 single hypothesis: C07 first Scan300 gap while the Xvfb GUI
clients start *after* Nav2 READY. Attach the exact two CI-only viewers
during staged startup instead; preserve original Owner WSLg behavior,
one Gazebo server, unmodified Scan TTL/CM/Guard/Goal and full L2 gate.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
STUDENT=ROOT/"student" if (ROOT/"student").is_dir() else ROOT.parent/"student"
SRC=STUDENT/"block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh"
WF=ROOT/".github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml"

class PreNav2ViewerCandidate(unittest.TestCase):
    def test_actual_ci_opt_in_before_staged_nav2_ready(self):
        s=SRC.read_text()
        self.assertIn('CI_PRE_READY_GUI=0',s)
        self.assertIn('AXIA_D06_L2_GUI_PRE_NAV2_READY',s)
        self.assertIn('D06_CI_L2_GUI_PRE_NAV2_STARTED',s)
        self.assertIn('D06_CI_L2_GUI_EARLY_REUSED_NOT_SPAWNED',s)
        self.assertLess(s.index('D06_CI_L2_GUI_PRE_NAV2_STARTED'),
                        s.index('if "${STAGED_START[@]}"'))
        self.assertLess(s.index('if "${STAGED_START[@]}"'),
                        s.index('D06_CI_L2_GUI_EARLY_REUSED_NOT_SPAWNED'))
        self.assertIn('if [[ "$CI_PRE_READY_GUI" == 1 ]];then',s)
        self.assertIn('MOVING_GAZEBO_GUI_PID=$!',s)
        self.assertIn('MOVING_RVIZ_PID=$!',s)
        self.assertIn('setsid nice -n 15 gz sim -g',s)
        self.assertIn('setsid nice -n 15 rviz2 -d',s)
        self.assertIn('D06_CI_ONLY_SOFTWARE_GUI_PRIORITY_15_ENABLED',s)

    def test_only_public_no_goal_viewers_and_no_safety_bypass(self):
        s=SRC.read_text()
        self.assertIn('"${GITHUB_ACTIONS:-}" == true',s)
        self.assertIn('"${AXIA_G07_CI_SENSOR_TRUTH_NO_GOAL:-0}" == 1',s)
        self.assertIn('"${AXIA_D06_L2_GUI_NICE_ONLY:-0}" == 15',s)
        self.assertIn('"${AXIA_D06_L2_GUI_PRE_NAV2_READY:-0}" == 1',s)
        self.assertIn('"$SENSOR_NO_GOAL" == 1',s)
        self.assertIn('setsid gz sim -g',s)
        self.assertIn('setsid rviz2 -d',s)
        self.assertNotIn('SCAN_TTL_SEC=.5',s)
        self.assertNotIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=1',s)
        self.assertNotIn('LIBGL_ALWAYS_SOFTWARE=1',s)

    def test_real_gazebo_l2_enables_only_one_trial_and_keeps_strict_gate(self):
        s=WF.read_text()
        self.assertIn("AXIA_D06_L2_GUI_NICE_ONLY: '15'",s)
        self.assertIn("AXIA_D06_L2_GUI_PRE_NAV2_READY: '1'",s)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '0'",s)
        self.assertIn('assert gap<=.300',s)
        self.assertIn('POST_READY_NATIVE_SCAN300_FIRST_BREACH',s)
        self.assertIn('GAZEBO_SERVER_EXIT0_NOT_PROVEN_L2',s)

if __name__=="__main__":
    unittest.main()
