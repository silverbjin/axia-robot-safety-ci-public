"""Bounded WSLg existing-core triage contract. Never executes Gazebo or ROS."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/axia_d06_g07_wslg_existing_core_once.sh"

class ExistingGazeboCoreScope(unittest.TestCase):
    def test_script_selfcheck_has_no_ros_or_gazebo(self):
        self.assertTrue(SCRIPT.is_file(),"CORE_TRIAGE_SCRIPT_MISSING_RED")
        source=SCRIPT.read_text()
        self.assertNotIn("ros2 launch",source)
        self.assertNotIn("gz sim",source)
        self.assertNotIn("pkill",source)
        self.assertNotIn("LD_PRELOAD=",source)
        self.assertIn("thread apply all bt",source)
        self.assertIn("NO_GAZEBO_RUN",source)
        with tempfile.TemporaryDirectory() as td:
            e=os.environ.copy();e["HOME"]=td
            r=subprocess.run(["bash",str(SCRIPT),"--self-check"],
                             env=e,text=True,capture_output=True,timeout=10)
            self.assertEqual(r.returncode,0,(r.stdout,r.stderr))
            self.assertIn("D06_WSLG_CORE_TRIAGE_L0_PASS_NO_GAZEBO_RUN",r.stdout)

    def test_invalid_core_inputs_fail_closed_without_gdb(self):
        self.assertTrue(SCRIPT.is_file(),"CORE_TRIAGE_SCRIPT_MISSING_RED")
        with tempfile.TemporaryDirectory() as td:
            e=os.environ.copy();e["HOME"]=td
            r=subprocess.run(["bash",str(SCRIPT),"--core","/does-not-exist",
                              "--exe","/does-not-exist"],
                             env=e,text=True,capture_output=True,timeout=10)
            self.assertNotEqual(r.returncode,0,(r.stdout,r.stderr))
            self.assertIn("D06_WSLG_CORE_TRIAGE_HOLD",r.stdout+r.stderr)
            self.assertIn("CERTIFIED_ESTOP=false",r.stdout+r.stderr)

    def test_never_archive_core_or_claim_resolved_root(self):
        self.assertTrue(SCRIPT.is_file(),"CORE_TRIAGE_SCRIPT_MISSING_RED")
        s=SCRIPT.read_text()
        self.assertIn("ROOT_CAUSE=UNCONFIRMED",s)
        self.assertIn("core_not_archived",s)
        self.assertIn("sha256sum",s)
        self.assertIn("SIGSEGV",s)

if __name__=="__main__":
    unittest.main()
