"""D06 native Gazebo transport 13 teardown (read-only diagnostic only).

L0 simulates C++ pybind Node destructor aborting if /scan or /clock remain
subscribed at SIGTERM. No ROS, GPU, or Gazebo launch is performed.
"""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
PROBE=ROOT/"d06/tools/d06_gz_native_scan_probe_safe.py"
OLD=ROOT/"d06/docs/AXIA_D06_G07_FR1_NO_GOAL_SENSOR_PASS_NATIVE_SHUTDOWN_HOLD_20261119_KO.md"

STUB= r'''
import os
class Node:
    def __init__(self): self.topics=set()
    def subscribe(self, typ, topic, callback):
        self.topics.add(topic)
        return True
    def unsubscribe(self,topic):
        if topic not in self.topics: return False
        self.topics.remove(topic)
        print("STUB_UNSUBSCRIBED="+topic,flush=True)
        return True
    def __del__(self):
        if self.topics:
            print("STUB_PYBIND_NODE_DESTRUCTOR_ACTIVE="+str(self.topics),flush=True)
            os._exit(134)
'''

class NativeUnsubscribeBeforeInterpreterShutdown(unittest.TestCase):
    def test_sigterm_two_topics_removed_before_node_deallocation(self):
        self.assertTrue(PROBE.is_file(),str(PROBE))
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for pkg in ("gz","gz/msgs10"):
                path=root/pkg
                path.mkdir(parents=True)
                (path/"__init__.py").write_text("")
            (root/"gz/transport13.py").write_text(STUB)
            for name in ("laserscan_pb2.py","clock_pb2.py"):
                (root/"gz/msgs10"/name).write_text(
                    "class "+("LaserScan" if name.startswith("laser") else "Clock")+": pass\n")
            out=root/"scan.jsonl";clock=root/"clock.jsonl"
            env=dict(os.environ,PYTHONPATH=str(root))
            p=subprocess.Popen([sys.executable,"-u",str(PROBE),
                "--topic","/scan","--out",str(out),"--clock-out",str(clock)],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env,text=True)
            try:
                time.sleep(.35)
                self.assertIsNone(p.poll(),"receiver exited before SIGTERM")
                p.send_signal(signal.SIGTERM)
                stdout,_=p.communicate(timeout=8)
                self.assertEqual(p.returncode,0,stdout)
                self.assertIn("STUB_UNSUBSCRIBED=/scan",stdout)
                self.assertIn("STUB_UNSUBSCRIBED=/clock",stdout)
                self.assertIn("D06_GZ_NATIVE_SUBSCRIPTIONS_RELEASED",stdout)
                self.assertNotIn("STUB_PYBIND_NODE_DESTRUCTOR_ACTIVE",stdout)
            finally:
                if p.poll() is None:
                    p.kill();p.wait(timeout=5)

    def test_real_fr1_boundary_does_not_claim_gazebo_server_fixed(self):
        self.assertIn("exit134",OLD.read_text().replace(" ",""))
        source=PROBE.read_text()
        self.assertIn('for subscribed in ("/scan","/clock"):',source)
        self.assertIn("node.unsubscribe(subscribed)",source)
        self.assertIn("D06_GZ_NATIVE_SUBSCRIPTIONS_RELEASED",source)
        self.assertNotIn("os._exit(0)",source)
        self.assertNotIn("SIGKILL",source)

if __name__=="__main__":unittest.main()
