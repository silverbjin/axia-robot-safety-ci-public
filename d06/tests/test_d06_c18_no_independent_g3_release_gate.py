"""C18: independent GPU host removed from mandatory release gates;
existing physical WSL2 fail-closed Scan300/Nav2/native checks remain mandatory.
Only tests policy and pinned existing Owner interface; no ROS/Gazebo started.
"""
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
POLICY=ROOT/"d06/docs/AXIA_D06_C18_NO_G3_OWNER_WSL2_DIRECT_ACCEPTANCE_20261120_KO.md"
OWNER=ROOT/"d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh"

class C18Policy(unittest.TestCase):
    def policy(self):
        return POLICY.read_text(encoding="utf-8")

    def test_no_independent_wslg_g3_release_dependency(self):
        s=self.policy()
        for required in (
            "INDEPENDENT_WSLG_G3_REQUIRED=false",
            "OWNER_WSL2_NO_GOAL_REQUIRED=true",
            "OWNER_WSL2_NATIVE_EXIT0_REQUIRED=true",
            "OWNER_WSL2_SCAN300_REQUIRED=true",
            "D06_GAZEBO_LIVE_RELEASE=HOLD",
            "MAIN_MERGED=false",
        ):
            self.assertIn(required,s)
        self.assertNotIn("G3_HOST_CANDIDATE_NOT_ACCEPTED\n\n## 필수",s)

    def test_preserves_first_failure_and_l3_motion_hold(self):
        s=self.policy()
        for required in (
            "NO_GOAL_ONLY",
            "Scan300ms",
            "CM120ms",
            "Guard150ms",
            "Localization",
            "Gazebo",
            "SIGSEGV",
            "D06_FORENSIC_ARCHIVE",
            "D06_FORENSIC_SHA256",
            "NO_FIELD_REPEAT_ON_SAME_FAILURE=true",
            "MOVING_GOAL_ALLOWED=false",
            "CERTIFIED_ESTOP=false",
        ):
            self.assertIn(required,s)

    def test_one_pin_one_nvidia_session_and_readonly_preflight(self):
        s=self.policy()
        self.assertIn("86c68a121bedffbf1d2bb91e1efac6a40b88c798",s)
        self.assertIn("0592044ade101dfdff7682e127953c976778e6fc",s)
        for required in ('git hash-object "$SCRIPT"','bash "$SCRIPT" --self-check',
                         'bash "$SCRIPT" --nvidia-causal'):
            self.assertIn(required,s)
        owner=OWNER.read_text()
        self.assertIn("D06_OWNER_NO_GOAL_NATIVE_GATE_START",owner)
        self.assertIn("D06_GAZEBO_LIVE_RELEASE=HOLD",owner)
        self.assertIn("CERTIFIED_ESTOP=false",owner)
        self.assertEqual(subprocess.run(["bash","-n",str(OWNER)]).returncode,0)

if __name__=="__main__": unittest.main()
