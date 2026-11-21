"""Real native L2 regression: raw /scan 400.119ms gap despite RTF 0.984.

A safety /safety/scan gap-free window NEVER excuses one raw scan TTL
violation. This test captures first timing violation without threshold change.
"""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"student/block_B/day07/h01_runtime/tools"))
from g07_wslg_no_goal_sensor_probe import assess_window, analyze_timing_separately

class NativeFirstRawGap(unittest.TestCase):
    def test_raw_third_callback_400ms_with_normal_rtf_must_hold(self):
        safety=[{"recv":10.0+i*.1,"stamp":5.0+i*.1,
                 "front":1.414,"side":2.52,"near":.298,"beams":360}
                for i in range(30)]
        raw=[dict(row) for row in safety]
        raw[3]["recv"]=raw[2]["recv"]+.400119
        # Remaining source header timestamps are untouched at 10Hz.
        for i in range(4,len(raw)):raw[i]["recv"]+=.21
        clocks=[{"recv":10.+i*.1,"sim":5.+i*.0984428}
                for i in range(30)]
        d={"safety":safety,"raw":raw,
           "clock":[5.,5.1,5.2],
           "clock_receipts":clocks,
           "odom":[{"vx":0.0,"wz":0.0} for _ in range(3)]}
        verdict=assess_window(d)
        rtf=analyze_timing_separately(d)
        self.assertEqual(verdict["status"],"NO_GOAL_SENSOR_UNSAFE_HOLD")
        self.assertIn("RAW_RECEIPT_TTL_300MS_BLOCKED",verdict["reasons"])
        self.assertNotIn("SAFETY_RECEIPT_TTL_300MS_BLOCKED",verdict["reasons"])
        self.assertEqual(verdict["metrics"]["raw"]["first_receipt_ttl_breach_at_index"],3)
        self.assertAlmostEqual(verdict["metrics"]["raw"]["max_source_stamp_delta_sec"],.1,places=4)
        self.assertAlmostEqual(verdict["metrics"]["raw"]["max_receipt_gap_sec"],.400119,places=4)
        self.assertAlmostEqual(rtf["ros_clock_rtf"],.984428,places=4)
        self.assertEqual(rtf["timing_pattern"],"RTF_NORMAL")
        self.assertFalse(rtf["distance_unsafe_independent_of_rtf"])
        self.assertFalse(verdict["goal_sent"])

if __name__=="__main__":
    unittest.main()
