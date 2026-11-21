"""G07: proven GUI-present 2-cycle retains GUI optional in the formal gate.

Previous headless 0/2 failed Clock/Odom or read-only Scan reception; reverting\nunsupported experimental CI profile is NOT masking or waiving the safety\ngate. GUI optional on Owner remains essential. Do not change actual safety
limits, TTY, native exact robot, or depth-off temporary Waffle. GUI
windows are diagnostics ONLY and may be completely absent.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml"
OWNER=ROOT/"scripts/axia_g07_stabilization_wsl2_final_once.sh"

class NativeHeadlessOnlyG07(unittest.TestCase):
    def test_native_release_uses_proven_profile_not_failed_headless_trial(self):
        src=WORKFLOW.read_text()
        self.assertIn("cycle: [1, 2]",src)
        self.assertIn("AXIA_G07_TASK04_CI_GUI_MOVING: '1'",src)
        self.assertIn("QT_QPA_PLATFORM: xcb",src)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '1'",src)
        self.assertIn("AXIA_G07_DEPTH_SENSOR_ENABLED: '0'",src)
        self.assertIn("AXIA_G07_SCAN_PREFLIGHT_STRICT: '1'",src)
        self.assertIn("AXIA_G07_STARTUP_READONLY_RECONCILE: '1'",src)
        self.assertIn("AXIA_G07_NATIVE_DEPTH_OFF_LIDAR_SAFETY_SCAN_PASS",src)\n        self.assertTrue((ROOT/'docs/operations/AXIA_G07_HEADLESS_NATIVE_FIRST_FAILURE_20261121_KO.md').is_file())

    def test_owner_fallback_keeps_tty_manual_goal_and_no_gui_gate(self):
        src=OWNER.read_text()
        for text in ("OWNER_CONTROLLING_TTY_REQUIRED","YES-P2-G07-GOAL",
                     "AXIA_G07_GUI_DIAGNOSTIC_ONLY=1",
                     "AXIA_G07_DEPTH_SENSOR_ENABLED=0"):
            self.assertIn(text,src)
        self.assertNotIn("hold WSLG_GUI_REQUIRED",src)
        self.assertNotIn("hold WSLG_D3D12_ADAPTER_NOT_VERIFIED",src)
        self.assertNotIn("hold MOVING_GUI_WINDOWS_MISSING",src)
        self.assertIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=0',src)

    def test_native_success_depends_on_safety_not_window_count(self):
        src=WORKFLOW.read_text()
        self.assertIn("AXIA_G07_NATIVE_L2_GUARD_SUPERVISOR_ACTUAL_CHILD_EXIT0_PASS",src)
        self.assertIn("AXIA_G07_REAL_OWNER_AMCL_PRIMARY_PATH_PASS",src)
        self.assertIn("AXIA_G07_FV17_REAL_GAZEBO_GUARD_INTERNAL_TTL_PASS",src)
        self.assertIn("AXIA_G07_TASK04_NATIVE_MOVING_HEADLESS_SAFETY_L2_PASS",src)

if __name__=="__main__": unittest.main()
