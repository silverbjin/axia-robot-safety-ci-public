"""Cycle37 real Goal L2 #43892204272 CM first RMW gap 130.477ms.

Measured CPU: 4core official CM={1,2}; current display-only marker=2
competes with CM; Gazebo physics={3}, GUI0, bag3. Safely move ONLY
display-only Marker subscriber to last core (3), nice15. Source/Guard/
CM scheduling, Nav2, velocities and safety TTL remain unchanged.
This is an *unproven cause candidate* until exact-source real L2.
"""
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from d06.live.d06_gui_cpu_plan import select_cpu,select_monitor_cpu

class NoDisplayMonitorOnOwnedCMMask(TestCase):
    def test_cycle37_monitor_avoids_actual_cm_mask_on_4_and_8_cpus(self):
        for cpus,cm in ((set(range(4)),{1,2}),(set(range(8)),{1,6})):
            with self.subTest(cpus=cpus),patch.dict(os.environ,
                {"AXIA_G07_GUI_SCENE_OVERLAY":"1"}):
                marker=select_monitor_cpu(cpus)
                self.assertEqual(marker,max(cpus))
                self.assertFalse({marker}&cm,
                    "AXIA_G07_C37_RENDER_MARKER_MUST_NOT_SHARE_NATIVE_CM")
                self.assertNotEqual(marker,select_cpu(cpus))
    def test_default_verified_d06_cpu_plan_unchanged_outside_optin(self):
        with patch.dict(os.environ,{"AXIA_G07_GUI_SCENE_OVERLAY":"0"}):
            self.assertEqual(select_monitor_cpu(set(range(4))),2)
            self.assertEqual(select_monitor_cpu(set(range(8))),6)
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(select_monitor_cpu(set(range(4))),2)
    def test_exact_public_sidecar_is_readonly_and_keeps_low_nice(self):
        script=(ROOT/"d06/scripts/g07_shared_gui_clients.sh").read_text()
        self.assertIn('taskset -c "$MONITOR_CPU" nice -n 15 python3',script)
        self.assertIn('taskset -c "$GUI_CPU" nice -n 19 gz sim -g',script)
        self.assertNotIn("taskset -cp",script)
        self.assertNotIn("ros2 action send_goal",script)
        self.assertNotIn("ros2 topic pub /cmd_vel",script)
    def test_ineligible_affinity_remains_fail_closed(self):
        with patch.dict(os.environ,{"AXIA_G07_GUI_SCENE_OVERLAY":"1"}):
            for bad in ({0,1,2},set(),{-1,0,1,2}):
                with self.assertRaises(ValueError):
                    select_monitor_cpu(bad)

if __name__=="__main__":
    import unittest;unittest.main()
