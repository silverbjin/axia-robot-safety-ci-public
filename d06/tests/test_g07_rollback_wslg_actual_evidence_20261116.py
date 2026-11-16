"""Actual owner WSLg ZIP 2026-11-16 regression: no ROS, no Goal.

Evidence from owner-uploaded axia_g07_rollback_gui_evidence_5aAPfVy9.zip:
gz_services contains world control + waffle sensor, ROS monitor /safety/scan
front~=0.52m, while gz model --list timed out. Gazebo GUI logs:
'MESA-EGL: warning: Not allowed to force software rendering when API
explicitly selects a hardware device.' Never claim rendered WSLg pixels.
"""
import importlib.util
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]
PROBE=BASE/"live/g07_wslg_actual_evidence_contract.py"
SIDE=BASE/"scripts/g07_shared_gui_clients.sh"
WRAPPER=Path(__file__).resolve().parents[2]/"scripts/axia_g07_rollback_dual_gui_wsl2_no_goal_once.sh"

def module():
    spec=importlib.util.spec_from_file_location("actual_wslg",PROBE)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

# Minimal sanitized excerpts from actual Owner ZIP, not a fabricated full run.
SERVICES="/world/default/control\n/world/default/model/turtlebot3_waffle/link/camera_link/sensor/intel_realsense_r200_depth/depth_image/set_rate\n/world/default/gui/info\n"
MODELS="Requesting state for world [default]...\nService call to [/world/default/state] timed out\n"
MONITOR='D06_EDU_OBSERVATION_ZONE {"zone":"SLOWDOWN","front_m":0.5227654576301575,"cm_vx":null,"odom_vx":0.0,"evidence_only":true}'
EGL="MESA-EGL: warning: Not allowed to force software rendering when API explicitly selects a hardware device."

class ActualOwnerRollbackRegressions(unittest.TestCase):
    def test_world_and_waffle_evidence_not_erased_by_model_cli_timeout(self):
        d=module().interpret_world_probe(SERVICES,MODELS,MONITOR)
        self.assertEqual(d["status"],"MODEL_QUERY_TIMEOUT_WITH_LIVE_ROS_AND_WORLD_SERVICES_NO_GOAL")
        self.assertTrue(d["gazebo_world_service_seen"])
        self.assertTrue(d["waffle_sensor_service_seen"])
        self.assertTrue(d["ros_scan_seen"])
        self.assertFalse(d["world_absence_proven"])
        self.assertFalse(d["wslg_pixels_verified"])
    def test_missing_world_service_remains_hold_even_with_scan(self):
        d=module().interpret_world_probe("/gazebo/worlds\n",MODELS,MONITOR)
        self.assertEqual(d["status"],"WORLD_TRANSPORT_OR_MODEL_UNVERIFIED_HOLD")
    def test_legacy_forced_mesa_software_is_no_longer_used_in_wslg(self):
        s=SIDE.read_text()
        self.assertIn('if [[ "$MODE" == ci ]];then',s)
        self.assertIn('unset LIBGL_ALWAYS_SOFTWARE GALLIUM_DRIVER',s)
        self.assertIn('LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe',s)
        self.assertNotIn('export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe\nunset QT_QPA_PLATFORM',s)
    def test_native_wslg_runtime_evidence_and_no_goal(self):
        s=WRAPPER.read_text()
        self.assertIn("g07_wslg_actual_evidence_contract.py",s)
        self.assertIn("AXIA_G07_ROLLBACK_WSLG_PIXEL_CONFIRMATION_REQUIRED",s)
        self.assertNotIn("YES-P2-G07-GOAL",s)
        self.assertIn("AXIA_G07_ROLLBACK_GAZEBO_HEADLESS_SERVER_SEPARATE_GZ_GUI_AND_RVIZ_NO_GOAL",s)
    def test_gui_warning_does_not_certify_visuals(self):
        self.assertEqual(module().classify_renderer_warning(EGL),"FORCED_SOFTWARE_EGL_CONFLICT_CANDIDATE")
        self.assertNotEqual(module().classify_renderer_warning(EGL),"WSLG_GUI_ACCEPTED")

if __name__=="__main__":
    unittest.main()
