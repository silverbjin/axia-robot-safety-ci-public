#!/usr/bin/env python3
"""D08 exact isolated ROS first-source stall: keep disk I/O out of callbacks."""
import ast
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))

class BufferedIndependentScanTests(unittest.TestCase):
    def test_first_sample_ready_then_flush_only_at_shutdown(self):
        from d08_ros_isolated_scan_probe import IsolatedScanEvidence
        recorder=IsolatedScanEvidence(4)
        class Stream:
            def __init__(self): self.lines=[]
            def write(self,text): self.lines.append(text)
        dst=Stream()
        self.assertTrue(recorder.add(1.0,101000000000))
        recorder.write_remaining(dst,start=0,stop=1)
        self.assertEqual(len(dst.lines),1,"first sample must make readiness file nonempty")
        self.assertFalse(recorder.add(1.1,101100000000))
        self.assertFalse(recorder.add(1.2,101200000000))
        self.assertEqual(len(dst.lines),1,"callback must not flush every LaserScan")
        recorder.write_remaining(dst,start=1)
        self.assertEqual(len(dst.lines),3)
        import json
        rows=[json.loads(x) for x in dst.lines]
        self.assertEqual([x["source_stamp_ns"] for x in rows],
                         [101000000000,101100000000,101200000000])
        self.assertEqual([x["host_monotonic_sec"] for x in rows],
                         [1.0,1.1,1.2])

    def test_bounded_and_no_synthetic_samples(self):
        from d08_ros_isolated_scan_probe import IsolatedScanEvidence
        recorder=IsolatedScanEvidence(3)
        self.assertFalse(recorder.add(1.0,-1))
        self.assertTrue(recorder.add(1.1,1000000001))
        self.assertFalse(recorder.add(1.2,1000000002))
        self.assertFalse(recorder.add(1.3,1000000003))
        self.assertFalse(recorder.add(1.4,1000000004))
        self.assertEqual(len(recorder.rows),3)
        self.assertEqual(recorder.dropped,1)

    def test_original_sensor_subscription_and_single_process_writer_preserved(self):
        source=(ROOT/"d08/harness/d08_ros_isolated_scan_probe.py").read_text()
        tree=ast.parse(source)
        self.assertIn("qos_profile_sensor_data",source)
        self.assertIn('LaserScan,"/scan"',source)
        self.assertIn('rclpy.spin_once(node,timeout_sec=.05)',source)
        self.assertIn("dst",source)
        self.assertNotIn("cmd_vel",source)
        self.assertNotIn("LIBGL_ALWAYS_SOFTWARE",source)
        self.assertIn("IsolatedScanEvidence",source)

    def test_ros_shutdown_exception_flushes_buffer_before_teardown(self):
        # Real CI #44670938997 original isolated log: ExternalShutdownException
        # in rclpy.spin_once on SIGTERM bypassed normal post-loop flush.
        source=(ROOT/"d08/harness/d08_ros_isolated_scan_probe.py").read_text()
        self.assertIn("ExternalShutdownException",source)
        parsed=ast.parse(source)
        run=next(x for x in parsed.body if isinstance(x,ast.FunctionDef)
                 and x.name=="run")
        finally_flush=False
        for node in ast.walk(run):
            if isinstance(node,ast.Try):
                for item in node.finalbody:
                    if isinstance(item,ast.Expr) and isinstance(item.value,ast.Call):
                        call=item.value
                        if isinstance(call.func,ast.Attribute) and call.func.attr=="write_remaining":
                            finally_flush=True
        self.assertTrue(finally_flush,
           "SIGTERM can raise ExternalShutdownException before normal flush; "
           "write_remaining MUST execute in finally while output file is open")

if __name__=="__main__":
    unittest.main()
