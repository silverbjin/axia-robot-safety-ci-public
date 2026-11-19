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

class ExactStudentPairGazeboBoundary(unittest.TestCase):
    def test_actual_first_student_breach_matched_to_native(self):
        witness=ROOT/"d06/tools/d06_g07_scan_rx_witness.py"
        spec=importlib.util.spec_from_file_location("g07_first_student_witness",witness)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        def sample(stamp,t):
            return {"source_stamp_ns":stamp,"host_monotonic_sec":t}
        truth={"scan_receipts_compact":{"schema":"axia.g07.first_ttl_host_pair.v1",
            "raw":{"before":sample(51100000000,100.1),
                   "after":sample(51200000000,100.45),"gap_sec":.35},
            "safety":{"before":sample(51100000000,100.12),
                      "after":sample(51200000000,100.46),"gap_sec":.34}}}
        native=[sample(51100000000,100.08),sample(51200000000,100.42)]
        result=m.classify_student_first(native,truth)
        self.assertTrue(result["student_first_stamp_pair_verified"])
        self.assertEqual(result["student_first_topic"],"raw")
        self.assertEqual(result["student_first_candidate"],"AT_OR_BEFORE_NATIVE_TRANSPORT_RX")
        self.assertAlmostEqual(result["student_first_native_gap_sec"],.34)
        self.assertEqual(result["release"],"HOLD")
        self.assertFalse(result["goal_allowed"])

    def test_native_fast_student_raw_callback_slow_stays_after_native(self):
        witness=ROOT/"d06/tools/d06_g07_scan_rx_witness.py"
        spec=importlib.util.spec_from_file_location("g07_first_student_witness2",witness)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        raw={"before":{"source_stamp_ns":10100000000,"host_monotonic_sec":100.0},
             "after":{"source_stamp_ns":10200000000,"host_monotonic_sec":100.41},"gap_sec":.41}
        v=m.classify_student_first([
          {"source_stamp_ns":10100000000,"host_monotonic_sec":99.99},
          {"source_stamp_ns":10200000000,"host_monotonic_sec":100.09},
        ],{"scan_receipts_compact":{"raw":raw,"safety":None}})
        self.assertEqual(v["student_first_candidate"],"AFTER_NATIVE_TRANSPORT_RX")
        self.assertTrue(v["student_first_stamp_pair_verified"])

    def test_without_student_ttl_pair_dont_fake_first_cause(self):
        witness=ROOT/"d06/tools/d06_g07_scan_rx_witness.py"
        spec=importlib.util.spec_from_file_location("g07_first_student_witness3",witness)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        result=m.classify_student_first([],{"scan_receipts_compact":{"raw":None,"safety":None}})
        self.assertEqual(result["student_first_candidate"],"STUDENT_FIRST_PAIR_UNAVAILABLE")
        self.assertFalse(result["student_first_stamp_pair_verified"])


if __name__=="__main__":
    unittest.main()
