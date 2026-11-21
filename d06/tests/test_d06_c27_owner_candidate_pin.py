"""C27 field Owner gate: preserve default frozen WSL2 evidence code and
only opt in exact no-goal Gazebo native exit guard after source authentication.
"""
from pathlib import Path
import os, subprocess, unittest
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh"
class C27OwnerCandidatePin(unittest.TestCase):
    def test_candidate_and_baseline_selfcheck_have_distinct_student_commits(self):
        env=os.environ.copy()
        for mode,pin in (("0","0565e580f5b7c80d719960a6046de3e45c8ea477"),
                         ("1","6c79c09d91f13c81961492eb30e66d99d307831c")):
            env["AXIA_D06_GAZEBO_C27_CANDIDATE"]=mode
            p=subprocess.run(["bash",str(SRC),"--self-check"],env=env,
                capture_output=True,text=True,timeout=7)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn(pin,p.stdout)
            self.assertIn("NO_ROS_NO_GAZEBO_NO_GOAL",p.stdout)

    def test_invalid_candidate_gate_must_fail_without_any_ros(self):
        env={**os.environ,"AXIA_D06_GAZEBO_C27_CANDIDATE":"unknown"}
        p=subprocess.run(["bash",str(SRC),"--self-check"],env=env,
            capture_output=True,text=True,timeout=7)
        self.assertNotEqual(p.returncode,0)
        self.assertIn("G07_C27_CANDIDATE_SCOPE_INVALID_NO_GOAL",p.stdout+p.stderr)

    def test_explicit_nvidia_wslg_preflight_before_student_clone(self):
        s=SRC.read_text()
        self.assertIn('AXIA_D06_GAZEBO_C27_CANDIDATE',s)
        self.assertIn('G07_C27_CANDIDATE_REQUIRES_EXPLICIT_NVIDIA_GPU',s)
        self.assertIn('G07_C27_CANDIDATE_ACTUAL_GLX_NVIDIA_D3D12_REQUIRED',s)
        self.assertIn('cc3c64f7ae769a11d9daad4acdbdb48141253f7c',s)
        self.assertIn('81adb67b40b3c7ee937bc2c695c4906282391774',s)
        self.assertIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=0',s)
        self.assertLess(s.index("G07_C27_CANDIDATE_ACTUAL_GLX_NVIDIA_D3D12_REQUIRED"),
                        s.index('git clone --quiet'))

if __name__=="__main__": unittest.main()
