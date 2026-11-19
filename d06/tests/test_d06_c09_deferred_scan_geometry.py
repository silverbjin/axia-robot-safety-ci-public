"""C09: real Gazebo C08 same source stamp 48.201→48.300:
native89.281ms, independent ROS safety86.495ms, Student callback403.214ms.
Keep ROS Scan callback O(1) for monotonic arrival stamping; run unchanged
geometry validation offline, then compute strict 300ms dwell. Do not change
any safety limits / QoS / sensor Hz / Goal / official Nav2.
"""
from pathlib import Path
import importlib.util
import math
import unittest
import sys
ROOT=Path(__file__).resolve().parents[2]
STUDENT=ROOT/"student" if (ROOT/"student").is_dir() else ROOT.parent/"student"
SRC=STUDENT/"block_B/day07/h01_runtime/tools/g07_wslg_no_goal_sensor_probe.py"

def load():
    sys.path.insert(0,str(SRC.parent))
    spec=importlib.util.spec_from_file_location("c09_deferred_geometry",SRC)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

class FakeScan:
    angle_min=-math.pi
    angle_increment=2*math.pi/360
    range_min=.12
    range_max=10.
    def __init__(self,invalid=False):
        self.ranges=[float('nan')]*360 if invalid else [2.52]*360
        if not invalid:
            for i in range(174,187):self.ranges[i]=1.414

class C09DeferredScanGeometry(unittest.TestCase):
    def test_hot_callback_only_stamps_and_keeps_message_until_post_shutdown(self):
        s=SRC.read_text()
        start=s.index('    def scan_callback(msg, kind):')
        end=s.index('    def on_odom(msg):',start)
        hot=s[start:end]
        self.assertIn('now = time.monotonic()',hot)
        self.assertIn('"_laser_msg":msg',hot)
        self.assertNotIn('sector_min(msg)',hot)
        self.assertNotIn('near_ring_fraction(msg)',hot)
        self.assertNotIn('enumerate(msg.ranges)',hot)
        self.assertIn('enrich_scan_geometry(records)',s)
        self.assertLess(s.index('scan_stopped=scan_executor.shutdown'),
                        s.index('        enrich_scan_geometry(records)'))
        self.assertLess(s.index('        enrich_scan_geometry(records)'),
                        s.index('stable=select_dual_topic_window(records)'))

    def test_deferred_geometry_same_safety_clear_and_preserves_receipt(self):
        m=load()
        sample={"recv":174.943991,"stamp":48.3,"stamp_ns":48300000000,
                "_laser_msg":FakeScan()}
        data={"safety":[sample.copy()],"raw":[sample.copy()]}
        out=m.enrich_scan_geometry(data)
        self.assertEqual(out["safety"][0]["recv"],174.943991)
        self.assertEqual(out["raw"][0]["stamp_ns"],48300000000)
        self.assertAlmostEqual(out["safety"][0]["front"],1.414,places=3)
        self.assertAlmostEqual(out["safety"][0]["side"],2.52,places=2)
        self.assertTrue(0<=out["safety"][0]["near"]<=1)
        self.assertNotIn("_laser_msg",out["safety"][0])

    def test_invalid_geometry_never_enters_clear_truth(self):
        m=load()
        data={"safety":[{"recv":5.0,"stamp":48.3,"stamp_ns":48300000000,
                         "_laser_msg":FakeScan(invalid=True)}],"raw":[]}
        out=m.enrich_scan_geometry(data)
        self.assertEqual(out["safety"],[])
        self.assertIn("SCAN_TTL_SEC = .300",SRC.read_text())
        self.assertNotIn("create_publisher(",SRC.read_text())
        self.assertNotIn("send_goal_async(",SRC.read_text())

if __name__=="__main__":unittest.main()
