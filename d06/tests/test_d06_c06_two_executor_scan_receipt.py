"""C06: exact real L2 #44538452186 Student callback arrives 327.465ms
after independent ROS Safety peer, same source stamp 36.600 -> 36.702.
Test one bounded hypothesis: no shared callback task queue between Scan
and high-frequency /clock,/odom. Do not change TTL, ROS topics or safety.
"""
from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[2]
STUDENT=(ROOT/"student" if (ROOT/"student").is_dir() else ROOT.parent/"student")
SRC=STUDENT/"block_B/day07/h01_runtime/tools/g07_wslg_no_goal_sensor_probe.py"
WITNESS=ROOT/"d06/tools/d06_g07_scan_rx_witness.py"

def pt(stamp,at,topic=None):
    d={"source_stamp_ns":stamp,"host_monotonic_sec":at}
    if topic:d["topic"]=topic
    return d

class C06TwoExecutorReceipts(unittest.TestCase):
    def test_c05_exact_first_safety_gap_is_student_queue_not_lidar_publish(self):
        spec=importlib.util.spec_from_file_location("c06_rx_compare",WITNESS)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        a,b=36600000000,36702000000
        student={"scan_receipts_compact":{"safety":{
            "before":pt(a,499.061499),"after":pt(b,499.503779),
            "gap_sec":.442280}}}
        native=[pt(a,499.057340),pt(b,499.171147)]
        peer=[pt(a,499.057832,"raw"),pt(b,499.173139,"raw"),
              pt(a,499.059103,"safety"),pt(b,499.176314,"safety")]
        got=m.classify_student_first(native,student,ros_observer=peer)
        self.assertEqual(got["student_first_boundary"],"AFTER_INDEPENDENT_ROS_RECEIPT")
        self.assertEqual(got["student_first_decomposition"],"STUDENT_CALLBACK_ONLY_BREACH")
        self.assertAlmostEqual(got["student_first_native_gap_sec"],.113807,places=6)
        self.assertAlmostEqual(got["student_first_ros_peer_gap_sec"],.117211,places=6)
        self.assertAlmostEqual(got["student_first_host_gap_sec"],.442280,places=6)
        self.assertAlmostEqual(got["student_first_ros_peer_to_student_after_sec"],.327465,places=6)
        self.assertEqual(got["release"],"HOLD")

    def test_scan_dispatch_does_not_share_clock_odom_executor_queue(self):
        s=SRC.read_text()
        self.assertIn("from rclpy.executors import SingleThreadedExecutor",s)
        self.assertIn("scan_executor=SingleThreadedExecutor()",s)
        self.assertIn("aux_executor=SingleThreadedExecutor()",s)
        self.assertIn("scan_executor.add_node(scan_node)",s)
        self.assertIn("aux_executor.add_node(aux_node)",s)
        self.assertIn("scan_executor.spin_once(timeout_sec=.08)",s)
        self.assertIn("aux_executor.spin_once(timeout_sec=.08)",s)
        self.assertIn("aux_thread.join(timeout=3.0)",s)
        self.assertIn("G07_READONLY_AUX_EXECUTOR_DID_NOT_STOP",s)
        self.assertNotIn("MultiThreadedExecutor(num_threads=2)",s)
        self.assertNotIn("    executor.add_node(scan_node)",s)

    def test_strict_no_goal_and_topic_contract_unchanged(self):
        s=SRC.read_text()
        self.assertIn("SCAN_TTL_SEC = .300",s)
        self.assertIn("NO_GOAL_SENSOR_UNSAFE_HOLD",s)
        self.assertIn('"/safety/scan"',s)
        self.assertIn('"/scan"',s)
        self.assertIn('"/clock"',s)
        self.assertIn('"/odom"',s)
        self.assertNotIn("create_publisher(",s)
        self.assertNotIn("send_goal_async(",s)
        self.assertNotIn("SCAN_TTL_SEC = .5",s)

if __name__=="__main__":unittest.main()
