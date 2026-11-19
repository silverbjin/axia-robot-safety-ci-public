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
# Match Student's own test import layout (pure assess_window; no ROS started).
import sys
sys.path.insert(0,str(SRC.parent))

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

class DualTopicReadinessGate(unittest.TestCase):
    """Warmup is NOT clearance; prove 20s of raw+safe only after both active."""
    def test_real_ci_first_raw_gap_pre_safety_does_not_truncate_dual_topic_dwell(self):
        m=load()
        def row(t,stamp):
            return {"recv":t,"stamp":stamp,"front":1.42,"side":2.52,"near":.05,"beams":360}
        raw=[row(200+i*.1,40+i*.1) for i in range(4)]
        raw += [row(200.74,40.4),row(200.84,40.5),row(201.00,40.6)]
        raw += [row(201.1+i*.1,40.7+i*.1) for i in range(206)]
        safety=[row(201.15+i*.1,40.8+i*.1) for i in range(205)]
        inp={"raw":raw,"safety":safety,"clock":[1,2,3],
             "odom":[{"vx":0,"wz":0} for _ in range(4)]}
        self.assertIn("RAW_RECEIPT_TTL_300MS_BLOCKED",m.assess_window(inp)["reasons"])
        win=m.select_dual_topic_window(inp)
        self.assertTrue(win["both_topics_ready"])
        self.assertGreater(win["start_host_monotonic_sec"],201.)
        self.assertGreaterEqual(win["observed_dwell_sec"],20.)
        self.assertGreater(win["pre_ready_raw_first_gap_sec"],.3)
        self.assertTrue(win["pre_ready_breach_evidence_retained"])
        result=m.assess_window(win["records"])
        self.assertNotIn("RAW_RECEIPT_TTL_300MS_BLOCKED",result["reasons"])
        self.assertEqual(result["status"],"NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE")

    def test_real_44473547759_first_safety_355ms_is_not_qualified_ready(self):
        m=load()
        def row(recv,stamp):
            return {"recv":recv,"stamp":stamp,"front":1.414,"side":2.520,
                    "near":.05,"beams":360}
        raw=[row(538+i*.1,44.6+i*.1) for i in range(240)]
        safety=[row(538.049124,44.700),row(538.404659,44.802)]
        safety += [row(538.504659+i*.1,44.903+i*.1) for i in range(220)]
        records={"raw":raw,"safety":safety,
                 "odom":[{"vx":0,"wz":0} for _ in range(4)],
                 "clock":[1,2,3]}
        self.assertIn("SAFETY_RECEIPT_TTL_300MS_BLOCKED",
                      m.assess_window(records)["reasons"])
        window=m.select_dual_topic_window(records)
        self.assertTrue(window["both_topics_ready"])
        self.assertGreaterEqual(window["start_host_monotonic_sec"],538.504659)
        self.assertGreaterEqual(window["observed_dwell_sec"],20)
        self.assertTrue(window["pre_ready_breach_evidence_retained"])
        self.assertAlmostEqual(window["startup_safety_first_breach"]["gap_sec"],
                               .355535,places=5)
        self.assertFalse(window["goal_allowed"])
        self.assertEqual(m.assess_window(window["records"])["status"],
                         "NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE")

    def test_first_qualified_two_topic_receipts_then_late_safety_355ms_blocks(self):
        m=load()
        def row(t):return {"recv":t,"stamp":t,"front":1.414,"side":2.52,"near":.05}
        raw=[row(100+i*.1) for i in range(240)]
        safe=[row(100.01+i*.1) for i in range(10)]
        safe += [row(101.265535+i*.1) for i in range(220)]
        window=m.select_dual_topic_window({"raw":raw,"safety":safe,
                     "odom":[{"vx":0,"wz":0} for _ in range(4)],
                     "clock":[1,2]})
        self.assertTrue(window["both_topics_ready"])
        self.assertIn("SAFETY_RECEIPT_TTL_300MS_BLOCKED",
                      m.assess_window(window["records"])["reasons"])

    def test_after_dual_topic_ready_any_gap_over_300ms_still_blocks(self):
        m=load()
        def row(t,stamp):
            return {"recv":t,"stamp":stamp,"front":1.42,"side":2.52,"near":.05}
        raw=[row(10+i*.1,10+i*.1) for i in range(3)]
        raw += [row(10.7,10.3)]
        raw += [row(10.8+i*.1,10.4+i*.1) for i in range(202)]
        safe=[row(10.03+i*.1,10.03+i*.1) for i in range(215)]
        inp={"raw":raw,"safety":safe,"clock":[1,2,3],
             "odom":[{"vx":0,"wz":0} for _ in range(4)]}
        w=m.select_dual_topic_window(inp)
        self.assertTrue(w["both_topics_ready"])
        self.assertIn("RAW_RECEIPT_TTL_300MS_BLOCKED",m.assess_window(w["records"])["reasons"])

    def test_missing_safety_topic_never_establishes_window(self):
        m=load()
        v=m.select_dual_topic_window({"raw":[{"recv":1,"stamp":1}], "safety":[],
                                       "odom":[],"clock":[]})
        self.assertFalse(v["both_topics_ready"])
        self.assertEqual(v["status"],"BOTH_TOPIC_READINESS_MISSING")
        self.assertFalse(v["goal_allowed"])

    def test_live_probe_waits_full_dwell_after_both_topics_are_live(self):
        s=SRC.read_text()
        self.assertIn("dual_ready_at",s)
        self.assertIn("select_dual_topic_window(records)",s)
        self.assertIn("first_scan_at and",s)  # original liveness start retained
        self.assertIn("time.monotonic() - dual_ready_at >= duration",s)
        self.assertIn("startup_pre_both_scan_diagnostics",s)


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
