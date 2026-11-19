"""Public Gazebo #44531611496: source pair 43.800 -> 43.902 s.
Student raw callback gap .427533 s, native .089121 s, ROS peer .089806 s;
Student after receipt ~.340542 s after peer. ROS /clock and /odom share
its original single-thread executor. Read-only clock/odom isolation candidate.
"""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
STUDENT=ROOT/"student" if (ROOT/"student").is_dir() else ROOT.parent/"student"
SRC=STUDENT/"block_B/day07/h01_runtime/tools/g07_wslg_no_goal_sensor_probe.py"
MOD=ROOT/"d06/tools/d06_g07_scan_rx_witness.py"

def p(stamp,t,topic=None):
    x={"source_stamp_ns":stamp,"host_monotonic_sec":t}
    if topic:x["topic"]=topic
    return x

class ClockScanCallbackIsolation(unittest.TestCase):
    def test_exact_student_first_pair_is_not_a_lidar_publisher_gap(self):
        spec=importlib.util.spec_from_file_location("scan_bottleneck",MOD)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        s0,s1=43800000000,43902000000
        native=[p(s0,342.925123),p(s1,343.014244)]
        peers=[p(s0,342.925639,"raw"),p(s1,343.015445,"raw"),
               p(s0,342.930273,"safety"),p(s1,343.019815,"safety")]
        student={"scan_receipts_compact":{"raw":{
            "before":p(s0,342.928454),"after":p(s1,343.355987),
            "gap_sec":.427533}}}
        v=m.classify_student_first(native,student,ros_observer=peers)
        self.assertEqual(v["student_first_boundary"],"AFTER_INDEPENDENT_ROS_RECEIPT")
        self.assertAlmostEqual(v["student_first_native_gap_sec"],.089121,places=6)
        self.assertAlmostEqual(v["student_first_ros_peer_gap_sec"],.089806,places=6)
        self.assertAlmostEqual(v["student_first_host_gap_sec"],.427533,places=6)
        self.assertAlmostEqual(v["student_first_ros_peer_to_student_after_sec"],.340542,places=6)
        self.assertEqual(v["student_first_decomposition"],"STUDENT_CALLBACK_ONLY_BREACH")
        self.assertEqual(v["release"],"HOLD")

    def test_student_scan_callbacks_isolated_from_high_frequency_clock_odom(self):
        src=SRC.read_text()
        self.assertIn('rclpy.create_node("axia_g07_wslg_no_goal_scan_truth")',src)
        self.assertIn('rclpy.create_node("axia_g07_wslg_no_goal_clock_odom_truth")',src)
        self.assertIn('MultiThreadedExecutor(num_threads=2)',src)
        self.assertIn('executor.add_node(scan_node)',src)
        self.assertIn('executor.add_node(aux_node)',src)
        self.assertIn('executor.spin_once(timeout_sec=.08)',src)
        self.assertIn('scan_node.create_subscription(LaserScan, "/scan"',src)
        self.assertIn('scan_node.create_subscription(LaserScan, "/safety/scan"',src)
        self.assertIn('aux_node.create_subscription(Odometry, "/odom"',src)
        self.assertIn('aux_node.create_subscription(Clock, "/clock"',src)
        self.assertIn('executor.shutdown(',src)
        self.assertNotIn('rclpy.spin_once(node, timeout_sec=.08)',src)

    def test_no_motion_and_strict_thresholds_untouched(self):
        src=SRC.read_text()
        self.assertIn('SCAN_TTL_SEC = .300',src)
        self.assertIn('MIN_MESSAGES = 20',src)
        self.assertIn('if first_scan_at and dual_ready_at is not None',src)
        self.assertIn('NO_GOAL_SENSOR_UNSAFE_HOLD',src)
        self.assertNotIn('create_publisher(',src)
        self.assertNotIn('send_goal_async(',src)
        self.assertNotIn('LIBGL_ALWAYS_SOFTWARE=',src)

if __name__=="__main__":
    unittest.main()
