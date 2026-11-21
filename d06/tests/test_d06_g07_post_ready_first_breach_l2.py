"""Reproduce public real Gazebo L2 #44528260284 pre-qualified Scan300.
The normal Student 20s window cannot erase a strict Nav2 READY receipt breach.
No ROS/Gazebo, Goal or safety TTL changes.
"""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
MOD=ROOT/"d06/tools/d06_g07_scan_rx_witness.py"
WF=ROOT/".github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml"

def classifier():
    spec=importlib.util.spec_from_file_location("ready_first_scan",MOD)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def scan(stamp,host,topic=None):
    o={"source_stamp_ns":stamp,"host_monotonic_sec":host}
    if topic is not None:o["topic"]=topic
    return o

class PostReadyFirstBreachGate(unittest.TestCase):
    def test_real_l2_first_after_nav2_ready_native_and_ros(self):
        m=classifier()
        s0,s1=31200000000,31302000000
        native=[scan(s0,461.818412),scan(s1,462.119853)]
        ros=[scan(s0,461.819390,"raw"),scan(s1,462.121407,"raw"),
             scan(s0,461.819735,"safety"),scan(s1,462.122273,"safety")]
        r=m.classify(native,[x for x in ros if x["topic"]=="raw"],
                     [x for x in ros if x["topic"]=="safety"],
                     after_host_sec=461.066,before_host_sec=481.066)
        self.assertEqual(r["candidate"],"AT_OR_BEFORE_NATIVE_TRANSPORT_RX")
        self.assertAlmostEqual(r["native_gap_sec"],.301441,places=6)
        self.assertAlmostEqual(r["raw_gap_sec"],.302017,places=6)
        self.assertAlmostEqual(r["safety_gap_sec"],.302538,places=6)
        self.assertFalse(r["goal_allowed"])
        self.assertEqual(r["release"],"HOLD")

    def test_real_l2_must_deny_post_ready_gap_even_if_student_20s_clear(self):
        src=WF.read_text()
        # Historical real L2 had 198/198 Student CLEAR after the first
        # post-ready 301.441ms native /scan gap. No false integrated PASS.
        self.assertIn('post_ready=paired["post_ready_proxy"]',src)
        self.assertIn('POST_READY_NATIVE_SCAN300_FIRST_BREACH',src)
        self.assertIn('POST_READY_RAW_SCAN300_FIRST_BREACH',src)
        self.assertIn('POST_READY_SAFETY_SCAN300_FIRST_BREACH',src)
        self.assertLess(src.index('POST_READY_NATIVE_SCAN300_FIRST_BREACH'),
                        src.index('assert rc==0'))
        self.assertIn('assert not post_ready["goal_allowed"]',src)

    def test_one_time_gui_window_probe_after_both_verified(self):
        src=WF.read_text()
        self.assertIn('if [[ "$rviz_seen" == 0 || "$gazebo_seen" == 0 ]];then',src)
        self.assertIn('grep -Eiq \'RViz\'',src)
        self.assertIn('grep -Eiq \'Gazebo\'',src)
        self.assertNotIn('AXIA_SCAN_TTL_SEC=.5',src)
        self.assertNotIn('AXIA_G07_CI_SIM_GOAL_ALLOWED: \'1\'',src)

if __name__=="__main__":
    unittest.main()
