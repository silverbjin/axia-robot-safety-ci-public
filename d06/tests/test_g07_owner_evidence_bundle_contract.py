"""Owner failure collection: all private supporting evidence in ONE local directory.
Only synthetic fixtures; CI never accesses or uploads Owner raw.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
COLLECTOR=ROOT/"d06/live/g07_owner_evidence_bundle.py"
WRAPPER=ROOT/"d06/scripts/g07_unified_final_owner_wsl2_once.sh"

class OwnerBundle(unittest.TestCase):
    def test_synthetic_failed_owner_bundle_is_private_atomic_tar_with_sha_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp)
            owner=home/"axia_p2_private_evidence"/"p2-l3-owner-synthetic"
            gui=home/"axia_d06_gazebo_rviz_owner_synthetic"
            (owner/"G07"/"live").mkdir(parents=True)
            gui.mkdir()
            (owner/"G07"/"live"/"ci_moving_goal_result.json").write_text(
                '{"status":"BLOCKED","first_guard_latch":{"reason":"CM_EXCEEDS_SUPERVISOR"}}')
            (owner/"G07"/"live"/"actual_ros_events.jsonl").write_text('{"kind":"guard"}\n')
            (owner/"source.sha").write_text("private-source-placeholder\n")
            (gui/"rviz.log").write_text("OpenGl version: 4.5\n")
            (gui/"sidecar.log").write_text("D06_RVIZ_STARTED\n")
            custody=home/".axia_p4_g11_session_custody"/"reviews"
            custody.mkdir(parents=True)
            (custody/"g07-synthetic.json").write_text('{"status":"HOLD"}')
            with tarfile.open(owner.with_suffix(".tar.gz"),"w:gz") as tf:
                tf.add(owner,arcname=owner.name)
            result=subprocess.run([sys.executable,str(COLLECTOR),
                "--home",str(home),"--owner-root",str(owner),"--gui-root",str(gui),
                "--status-code","3"],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn("AXIA_G07_OWNER_SUPPORT_BUNDLE=",result.stdout)
            roots=list((home/".axia_g07_owner_support").iterdir())
            self.assertEqual(len(roots),1)
            out=roots[0]
            self.assertTrue((out/"support_evidence.tar.gz").is_file())
            self.assertTrue((out/"SHA256SUMS").is_file())
            manifest=json.loads((out/"manifest.json").read_text())
            self.assertEqual(manifest["owner_wrapper_rc"],3)
            self.assertFalse(manifest["owner_l3_accepted"])
            self.assertFalse(manifest["uploaded"])
            with tarfile.open(out/"support_evidence.tar.gz") as tf:
                files=tf.getnames()
            self.assertTrue(any(x.endswith("ci_moving_goal_result.json") for x in files))
            self.assertTrue(any(x.endswith("rviz.log") for x in files))
            self.assertTrue(any(x.endswith(".tar.gz") for x in files))
            self.assertFalse(any(x.startswith("/") for x in files))
    def test_missing_owner_still_saves_gui_and_marks_incomplete(self):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp);gui=home/"axia_d06_gazebo_rviz_owner_test"
            gui.mkdir();(gui/"sidecar.log").write_text("G07 failure\n")
            p=subprocess.run([sys.executable,str(COLLECTOR),"--home",str(home),
                "--gui-root",str(gui),"--status-code","3"],
                capture_output=True,text=True,timeout=15)
            self.assertEqual(p.returncode,0,p.stderr)
            out=next((home/".axia_g07_owner_support").iterdir())
            self.assertEqual(json.loads((out/"manifest.json").read_text())["status"],
                             "INCOMPLETE_OWNER_ORIGINAL_UNAVAILABLE")
    def test_real_owner_wrapper_always_collects_on_exit_without_changing_exit(self):
        s=WRAPPER.read_text()
        self.assertIn("g07_owner_evidence_bundle.py",s)
        self.assertIn("AXIA_G07_OWNER_SUPPORT_BUNDLE",s)
        self.assertIn('cleanup() {',s)
        self.assertLess(s.index('cleanup() {'),s.index('trap cleanup EXIT'))
        self.assertNotIn("upload-to-public",s)

if __name__=="__main__":unittest.main()
