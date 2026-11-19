"""Reproduces *actual* Owner UCMOonHr first Scan300 wall gap and shutdown rclpy bug.

Real-Gazebo native /scan ROS scan and /clock read from uploaded verified compact TAR,
sanitized to a handful of source timestamp pairs. NO_GOAL L0 only.
"""
import importlib.util,json,pathlib,sys,types,tempfile,unittest
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[2]
SRC=ROOT/"d06/tools/d06_g07_scan_rx_witness.py"
FIX=ROOT/"d06/fixtures/g07_owner_nvidia_native_scan_clock_first_gap_20261119.json"
def load():
    sp=importlib.util.spec_from_file_location("d06_g07_clock",SRC)
    m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m

class ActualNativeFirstBreach(unittest.TestCase):
    def test_real_clock_gap_has_transient_progress_loss_not_ros_only(self):
        d=json.loads(FIX.read_text())
        m=load()
        r=m.classify(d["scan_native"],d["scan_raw"],d["scan_safety"],
                     native_clock=d["native_clock"])
        self.assertEqual(r["candidate"],"AT_OR_BEFORE_NATIVE_TRANSPORT_RX")
        self.assertAlmostEqual(r["native_gap_sec"],0.314467,places=6)
        self.assertAlmostEqual(r["raw_gap_sec"],0.312642,places=6)
        self.assertAlmostEqual(r["safety_gap_sec"],0.322424,places=6)
        self.assertEqual(r["native_clock_progress"],"SLOW")
        self.assertGreater(r["native_clock_window_rtf"],.3)
        self.assertLess(r["native_clock_window_rtf"],.6)
        self.assertLess(r["native_clock_max_host_gap_sec"],.1)
        self.assertFalse(r["publisher_send_timing_proven"])
        self.assertEqual(r["cause"],"UNDETERMINED")
        self.assertEqual(r["release"],"HOLD")

    def test_normal_clock_plus_slow_native_remains_transport_candidate_only(self):
        d=json.loads(FIX.read_text());m=load()
        d["native_clock"]=[
            {"host_monotonic_sec":104.822859,"sim_stamp_ns":51300000000},
            {"host_monotonic_sec":104.90,"sim_stamp_ns":51378000000},
            {"host_monotonic_sec":104.98,"sim_stamp_ns":51455000000},
            {"host_monotonic_sec":105.06,"sim_stamp_ns":51540000000},
            {"host_monotonic_sec":105.161897,"sim_stamp_ns":51635000000},
        ]
        r=m.classify(d["scan_native"],d["scan_raw"],d["scan_safety"],
                     native_clock=d["native_clock"])
        self.assertEqual(r["native_clock_progress"],"NORMAL_OR_FAST")
        self.assertEqual(r["cause"],"UNDETERMINED")
        self.assertEqual(r["release"],"HOLD")

    def test_missing_native_clock_unmeasured_no_false_sim_slow_claim(self):
        d=json.loads(FIX.read_text());m=load()
        r=m.classify(d["scan_native"],d["scan_raw"],d["scan_safety"],native_clock=[])
        self.assertEqual(r["native_clock_progress"],"UNMEASURED")
        self.assertIsNone(r["native_clock_window_rtf"])

    def test_external_shutdown_must_not_raise_second_rcl_shutdown(self):
        m=load()
        class ExternalShutdownException(Exception):pass
        called={"try":0,"shutdown":0}
        class Node:
            def create_subscription(self,*args,**kwargs):return object()
            def destroy_subscription(self,sub):pass
            def destroy_node(self):pass
        rclpy=types.ModuleType("rclpy")
        rclpy.init=lambda:None
        rclpy.create_node=lambda _:Node()
        rclpy.spin_once=lambda *_a,**_k:(_ for _ in ()).throw(ExternalShutdownException())
        def try_shutdown():
            called["try"]+=1
        def wrong_shutdown():
            called["shutdown"]+=1
            raise RuntimeError("rcl_shutdown already called")
        rclpy.try_shutdown=try_shutdown
        rclpy.shutdown=wrong_shutdown
        rclpy.executors=types.ModuleType("rclpy.executors")
        rclpy.executors.ExternalShutdownException=ExternalShutdownException
        rclpy.qos=types.ModuleType("rclpy.qos")
        rclpy.qos.qos_profile_sensor_data=object()
        sensor=types.ModuleType("sensor_msgs")
        sensor.msg=types.ModuleType("sensor_msgs.msg")
        sensor.msg.LaserScan=type("LaserScan",(),{})
        mods={"rclpy":rclpy,"rclpy.executors":rclpy.executors,
              "rclpy.qos":rclpy.qos,"sensor_msgs":sensor,"sensor_msgs.msg":sensor.msg}
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(sys.modules,mods),mock.patch.object(m.signal,"signal"):
            result=m.observe(pathlib.Path(td)/"ros.jsonl",max_seconds=1)
        self.assertEqual(result,3)
        self.assertEqual(called["try"],1)
        self.assertEqual(called["shutdown"],0)

    def test_actual_owner_cm_crash_remains_hold_after_clock_diagnosis(self):
        d=json.loads(FIX.read_text());self.assertEqual(d["owner"]["process_crashes"],["collision_monitor"])
        self.assertEqual(d["owner"]["teardown"],"P2_L2_FORCED_TEARDOWN")
        self.assertEqual(d["owner"]["ros_witness_exit"],1)
        self.assertFalse(d["owner"]["goal_sent"])
        self.assertGreater(d["owner"]["safety_max_gap_sec"],.3)

if __name__=="__main__":unittest.main()
