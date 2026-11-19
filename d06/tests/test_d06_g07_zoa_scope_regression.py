"""Actual ZOAgryLW Owner evidence: first whole-run violation is *not*
necessarily the same as first after Nav2 READY and Student 20s sensor window.

Never upgrade a ROS callback-only startup stall into a global verdict;
separately preserve Gazebo native slowdown and SIGSEGV on shutdown.
"""
import importlib.util
import json
import pathlib
import tempfile
import subprocess
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
FILE=ROOT/"d06/tools/d06_g07_scan_rx_witness.py"
FIX=ROOT/"d06/fixtures/g07_zoa_first_boundary_20261119.json"

def mod():
    spec=importlib.util.spec_from_file_location("zoa_reader",FILE)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

class ActualZoaScope(unittest.TestCase):
    def test_global_first_is_ros_callback_only_and_before_ready(self):
        d=json.loads(FIX.read_text())
        v=mod().classify(d["native"],d["raw"],d["safety"],
                         native_clock=d["clock"])
        self.assertEqual(v["first_ros_topic"],"safety")
        self.assertAlmostEqual(v["native_gap_sec"],0.096390,places=6)
        self.assertAlmostEqual(v["safety_gap_sec"],0.379498,places=6)
        self.assertEqual(v["candidate"],"AFTER_NATIVE_TRANSPORT_RX")
        self.assertLess(v["first_ros_host_receive_sec"][1],
                        d["nav2_action_ready_host_monotonic_sec"])
        self.assertEqual(v["release"],"HOLD")

    def test_ready_proxy_first_is_native_slow_not_ros_only(self):
        d=json.loads(FIX.read_text())
        ready=d["nav2_action_ready_host_monotonic_sec"]
        v=mod().classify(d["native"],d["raw"],d["safety"],
                         native_clock=d["clock"],
                         after_host_sec=ready,
                         before_host_sec=ready+d["proxy_window_sec"])
        self.assertEqual(v["scope"],"POST_NAV2_READY_PROXY")
        self.assertEqual(v["first_ros_topic"],"raw")
        self.assertAlmostEqual(v["native_gap_sec"],0.374240,places=6)
        self.assertAlmostEqual(v["raw_gap_sec"],0.357147,places=6)
        self.assertAlmostEqual(v["safety_gap_sec"],0.364705,places=6)
        self.assertEqual(v["candidate"],"AT_OR_BEFORE_NATIVE_TRANSPORT_RX")
        self.assertEqual(v["native_clock_progress"],"SLOW")
        self.assertGreater(v["native_clock_window_rtf"],.3)
        self.assertLess(v["native_clock_window_rtf"],.4)
        self.assertFalse(v["student_probe_same_pair_proven"])
        self.assertEqual(v["cause"],"UNDETERMINED")
        self.assertEqual(v["release"],"HOLD")

    def test_real_second_failure_cm_clean_gazebo_server_minus11_stays_hold(self):
        d=json.loads(FIX.read_text())
        self.assertTrue(d["shutdown"]["navigation_ack"])
        self.assertTrue(d["shutdown"]["localization_ack"])
        self.assertEqual(d["shutdown"]["cm_exit_code"],0)
        self.assertEqual(d["shutdown"]["gazebo_server_exit_code"],-11)
        v=mod().historical_verdict({
            "raw":{"max_host_gap_sec":d["sensor_truth"]["raw_max_gap_sec"]},
            "safety":{"max_host_gap_sec":d["sensor_truth"]["safety_max_gap_sec"]},
            "process_crashes":["gazebo_server"]
        })
        self.assertEqual(v["process_crashes"],["gazebo_server"])
        self.assertFalse(v["scan_300ms_pass"])
        self.assertEqual(v["release"],"HOLD")

    def test_cli_reports_both_scopes_in_one_existing_session(self):
        d=json.loads(FIX.read_text())
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            for fn,rec in (("gz.jsonl",d["native"]),
                           ("clock.jsonl",d["clock"])):
                (root/fn).write_text(chr(10).join(json.dumps(x) for x in rec)+chr(10))
            arr=d["raw"]+d["safety"]
            arr.sort(key=lambda x:x["host_monotonic_sec"])
            (root/"ros.jsonl").write_text(chr(10).join(json.dumps(x) for x in arr)+chr(10))
            (root/"startup.json").write_text(json.dumps({"status":"SMOKE_READY",
                "stages":[{"gate":"NAV2_ACTION_READY","status":"PASS","wall_monotonic_s":
                d["nav2_action_ready_host_monotonic_sec"]}]}))
            run=subprocess.run([sys.executable,str(FILE),"--analyze",
                "--ros-jsonl",str(root/"ros.jsonl"),
                "--native-jsonl",str(root/"gz.jsonl"),
                "--native-clock-jsonl",str(root/"clock.jsonl"),
                "--startup-verdict",str(root/"startup.json"),
                "--output",str(root/"layer.json")],capture_output=True,text=True,timeout=5)
            self.assertEqual(run.returncode,0,(run.stdout,run.stderr))
            report=json.loads((root/"layer.json").read_text())
            self.assertEqual(report["candidate"],"AFTER_NATIVE_TRANSPORT_RX")
            self.assertEqual(report["post_ready_proxy"]["candidate"],
                             "AT_OR_BEFORE_NATIVE_TRANSPORT_RX")
            self.assertFalse(report["post_ready_proxy"]["student_probe_same_pair_proven"])
            self.assertEqual(report["release"],"HOLD")
            self.assertIn("D06_G07_POST_READY_PROXY",run.stdout)

if __name__=="__main__":
    unittest.main()
