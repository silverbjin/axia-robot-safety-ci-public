"""Pre-Cycle36 GUI rollback contract: preserve actual 2026-11-15 Xvfb L2.
Never mistake Xvfb for WSLg. Pure tests do not publish ROS, send Goal,
or move the preloaded physical cylinder.
"""
import importlib.util
import pathlib
import unittest

D06=pathlib.Path(__file__).resolve().parents[1]
PROBE=D06/"live/g07_precycle36_readonly_preclear_probe.py"

spec=importlib.util.spec_from_file_location("preclear",PROBE)
probe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

def rollback_gui(source: str) -> bool:
    required=(
        'setsid taskset -c "$GUI_CPU" nice -n 19 rviz2',
        'setsid taskset -c "$GUI_CPU" nice -n 19 gz sim -g',
        'headless_server_required":True',
        'new_cmd_vel_publisher_authorized":False',
        'owner_l3_accepted":False',
        'G07_UNIFIED_GUI_DISPLAY_WINDOW_XVFB_PASS',
    )
    return all(term in source for term in required) and (
        "AXIA_G07_CYCLE36_INTEGRATED_GUI" not in source)

class FakeScan:
    angle_min=-3.14
    angle_increment=.01
    range_min=.05
    range_max=10.0
    ranges=[3.0]*630

class Baseline(unittest.TestCase):
    def test_old_gui_has_two_independent_display_clients_and_no_cycle36(self):
        source=(D06/"scripts/g07_shared_gui_clients.sh").read_text()
        self.assertTrue(rollback_gui(source))
        self.assertNotIn("G07_CYCLE36_INTEGRATED_GUI_NO_EXTERNAL_GZ",source)
    def test_current_integrated_gui_is_rejected_as_rollback(self):
        old=(D06/"scripts/g07_shared_gui_clients.sh").read_text()
        new=old.replace("gz sim -g","echo integrated-gui")
        self.assertFalse(rollback_gui(new))
    def test_scans_reuse_original_side_bearing_and_enforce_original_threshold(self):
        import math
        scan=FakeScan()
        front_idx=int(round((0-scan.angle_min)/scan.angle_increment))
        side_idx=int(round((math.atan2(.75,.19)-scan.angle_min)/scan.angle_increment))
        scan.ranges[front_idx]=1.3
        scan.ranges[side_idx]=.9
        front,side=probe.front_side(scan,math.atan2(.75,.19))
        self.assertAlmostEqual(front,1.3)
        self.assertAlmostEqual(side,.9)
        self.assertEqual(probe.label_preclear(front,side),
                         "OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE")
        self.assertEqual(probe.label_preclear(1.31,1.21),
                         "OWNER_PREGOAL_STATIC_CLEAR_CANDIDATE_NO_GOAL")
    def test_missing_real_scan_blocks_claim(self):
        self.assertEqual(probe.label_preclear(None,2.0),
                         "MISSING_REAL_SCAN")
        self.assertEqual(probe.label_preclear(.75,2.0),
                         "OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE")

if __name__=="__main__":
    unittest.main()
