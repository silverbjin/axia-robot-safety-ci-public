"""Real WSL2 ZOA lacks exact Student first raw/safety source-stamp pair.

Capture only the FIRST host-receipt TTL violation per topic, preserving
existing 300ms acceptance and revealing simultaneous native Gazebo cause
without logging 100s of MB or requiring another manual grep.
"""
import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
SRC_ROOT=(ROOT/"student" if (ROOT/"student").is_dir() else ROOT.parent/"student")
SRC=SRC_ROOT/"block_B/day07/h01_runtime/tools/g07_wslg_no_goal_sensor_probe.py"

def load():
    spec=importlib.util.spec_from_file_location("g07_student_first_pair",SRC)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

class StudentFirstHostGap(unittest.TestCase):
    def test_source_header_and_host_clock_first_ttl_same_pair(self):
        m=load()
        def row(recv,stamp):
            return {"recv":recv,"stamp":stamp,
                    "front":1.4,"side":2.5,"near":.1,"beams":160}
        records={
           "raw":[row(100.,50.0),row(100.1,50.1),row(100.43,50.2)],
           "safety":[row(100.005,50.0),row(100.107,50.1),row(100.512,50.2)],
           "odom":[{"vx":0,"wz":0} for _ in range(3)],
           "clock":[50,50.1,50.2],
        }
        report=m.assess_window(records)
        self.assertEqual(report["status"],"NO_GOAL_SENSOR_UNSAFE_HOLD")
        self.assertIn("SAFETY_RECEIPT_TTL_300MS_BLOCKED",report["reasons"])
        self.assertIn("RAW_RECEIPT_TTL_300MS_BLOCKED",report["reasons"])
        witness=report["scan_receipts_compact"]
        self.assertEqual(witness["schema"],"axia.g07.first_ttl_host_pair.v1")
        self.assertEqual(witness["safety"]["before"]["source_stamp_ns"],50100000000)
        self.assertEqual(witness["safety"]["after"]["source_stamp_ns"],50200000000)
        self.assertAlmostEqual(witness["safety"]["gap_sec"],.405,places=5)
        self.assertAlmostEqual(witness["raw"]["gap_sec"],.33,places=5)
        self.assertAlmostEqual(witness["raw"]["after"]["host_monotonic_sec"],100.43,places=5)
        self.assertEqual(report["metrics"]["safety"]["first_receipt_ttl_breach_at_index"],2)

    def test_no_first_breach_does_not_invent_evidence(self):
        m=load()
        records={"safety":[{"recv":100+i*.1,"stamp":50+i*.1,"front":1.4,"side":2.5,"near":.1} for i in range(22)],
                 "raw":[{"recv":100+i*.1,"stamp":50+i*.1} for i in range(22)],
                 "clock":[1,2], "odom":[{"vx":0,"wz":0} for _ in range(3)]}
        v=m.assess_window(records)
        self.assertIsNone(v["scan_receipts_compact"]["safety"])
        self.assertIsNone(v["scan_receipts_compact"]["raw"])
        self.assertEqual(v["status"],"NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE")

if __name__=="__main__":
    unittest.main()
