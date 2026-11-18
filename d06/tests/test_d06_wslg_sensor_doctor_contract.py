"""Exact-source fail-closed owner NO_GOAL candidate, never motion release."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT/"d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh"

class WslgDoctorSafety(unittest.TestCase):
    def test_only_no_goal_modes_and_no_ci_spoof(self):
        t=SCRIPT.read_text()
        self.assertIn('MODE="${1:---run}"',t)
        self.assertIn('D06_WSLG_NO_GOAL_MOTION_AUTHORITY_DENIED',t)
        self.assertIn('D06_WSLG_NO_GOAL_REAL_OWNER_WSLG_REQUIRED',t)
        self.assertIn('AXIA_G07_OWNER_SENSOR_TRUTH_NO_GOAL=1',t)
        self.assertIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=0',t)
        self.assertIn('AXIA_G07_TASK04_OWNER_MOVING_L3=0',t)
        self.assertIn('AXIA_D07_H01_GUI_NO_GOAL=0',t)
        self.assertNotIn('YES-P2-G07-GOAL',t)
        self.assertNotIn('export GITHUB_ACTIONS=true',t)

    def test_g07_real_wslg_original_world_and_no_noise_free_profile(self):
        t=SCRIPT.read_text()
        self.assertIn('AXIA_P2_G07_PHYSICAL_PREFLIGHT=1',t)
        self.assertIn('AXIA_P2_G07_RELOCATED_OBSTACLE=1',t)
        self.assertIn('AXIA_G07_OWNER_STARTUP_PARITY=1',t)
        self.assertIn('AXIA_G07_TASK02_SIMPLE_TF_CANDIDATE=0',t)
        self.assertIn('AXIA_P2_G07_OWNER_PARITY_CHECK=0',t)
        self.assertIn('AXIA_G07_CI_SENSOR_TRUTH_NO_GOAL=0',t)
        self.assertIn('AXIA_G07_TASK03_ECM_WITNESS=0',t)
        self.assertIn('D06_WSLG_SOFTWARE_RENDERER_OVERRIDE_DENIED',t)
        self.assertNotIn('LIBGL_ALWAYS_SOFTWARE=1',t)
        self.assertNotIn('GALLIUM_DRIVER=llvmpipe',t)

    def test_exact_student_commit_and_runtime_file_pins(self):
        t=SCRIPT.read_text()
        self.assertIn('9862353e7116bc4a14a5bb365ae356642e83ef0e',t)
        for blob in ('f795f9b6456df75546ab22988b53c953c53345a5',
                     '48203661d92b92517f5ea44f4a0b14cc26b24630',
                     'b2886cdf509d99ea62528cd013669258764b05e0'):
            self.assertIn(blob,t)
        self.assertIn('git -C "$GIT_ROOT/student" rev-parse HEAD',t)
        self.assertIn('git hash-object "$RUNTIME/tools/g07_wslg_no_goal_sensor_probe.py"',t)
        self.assertIn('d06-wslg-sensor-XXXXXXXX',t)

    def test_archive_custody_on_both_unsafe_and_clear(self):
        t=SCRIPT.read_text()
        self.assertIn('tar -C "$EVIDENCE_ROOT" -czf "$RUN_DIR.tar.gz"',t)
        self.assertIn('sha256sum "$RUN_DIR.tar.gz"',t)
        self.assertIn('D06_WSLG_NO_GOAL_SENSOR_HOLD_NATIVE_RC_',t)
        self.assertIn('D06_WSLG_NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE_OWNER_GOAL_NOT_RUN',t)
        self.assertIn('D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false',t)
        self.assertNotIn('AXIA_MVP_DEMO_ACCEPTED=PASS',t)

if __name__=="__main__":
    unittest.main()
