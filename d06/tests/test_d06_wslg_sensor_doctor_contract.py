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
        self.assertIn('D06_WSLG_SOFTWARE_RENDERER_OVERRIDE_DENIED',t)
        self.assertNotIn('LIBGL_ALWAYS_SOFTWARE=1',t)
        self.assertNotIn('GALLIUM_DRIVER=llvmpipe',t)

    def test_exact_student_commit_and_runtime_file_pins(self):
        t=SCRIPT.read_text()
        self.assertIn('3c6292a97e2e2f670f126500abaf6d24c03d9add',t)
        for blob in ('c1f2e2d705737090172bc083aa074b592add2e95',
                     'c498fbe527249c0b5482f18b893227396d99166a',
                     '120058b11c9a3cecee4905806d022314e5979f60'):
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
