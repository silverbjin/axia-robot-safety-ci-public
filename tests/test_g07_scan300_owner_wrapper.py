"""Fail-closed offline Owner candidate; no Gazebo, WSLg, or Goal."""
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WRAPPER=ROOT/'scripts/axia_g07_stabilization_wsl2_final_once.sh'

class StrictOwnerScanWrapper(unittest.TestCase):
    def test_candidate_pin_matches_failed_new_source_and_strict_l2(self):
        s=WRAPPER.read_text()
        self.assertIn("readonly STUDENT_SHA='803cdd99fa0f781998442fbc37be9f59fde82364'",s)
        self.assertIn('readonly CI_L2_RUN=44764186378',s)
        self.assertIn("readonly CI_L2_HEAD='57b70acbc1e6a549d64cf5508b199634ac2cd4cd'",s)
        self.assertIn('export AXIA_G07_SCAN_PREFLIGHT_STRICT=1',s)
        self.assertIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=0',s)
        self.assertIn('OWNER_CONTROLLING_TTY_REQUIRED',s)
        self.assertIn('PASS_TWO_STRICT_REAL_GAZEBO_GOALS_OWNER_WSL2_NOT_RUN',s)
        self.assertLess(s.index('export AXIA_G07_SCAN_PREFLIGHT_STRICT=1'),
                        s.index('source /opt/ros/jazzy/setup.bash',s.index("OUT=''")))

    def test_compact_six_and_zip_size_limit(self):
        s=WRAPPER.read_text()
        for name in ("first_scan_timing_boundary.json","scan_wall_sim_rtf_summary.json",
                     "scan_pipeline_first_failure.json",
                     "guard_supervisor_first_state_transition.json",
                     "native_shutdown_verdict.json","release_scope.json"):
            self.assertIn(name,s)
        self.assertIn('g07_scan_compact_bundle.py',s)
        self.assertIn('8*1024*1024',s)
        self.assertIn('SHA256SUMS',s)
        self.assertNotIn('pkill -f',s)

    def test_bootstrap_no_ros_no_goal(self):
        subprocess.run(['bash','-n',str(WRAPPER)],check=True)
        p=subprocess.run(['bash',str(WRAPPER),'--self-check'],
                         capture_output=True,text=True,timeout=9)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn('NO_ROS_NO_GAZEBO_NO_GOAL',p.stdout)
        self.assertIn('OWNER_MOVING_L3=NOT_RUN',p.stdout)
        self.assertIn('CERTIFIED_ESTOP=false',p.stdout)

if __name__=='__main__':unittest.main()
