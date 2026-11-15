"""AXIA G07 Owner v2: exact CI-real-Gazebo source SHA and a single manual L3.

No ROS/Goal invoked in CI. Old P4 and v1 gate remain immutable.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/g07_unified_final_owner_wsl2_v2_once.sh"
GATE=ROOT/"d06/acceptance/g07_unified_final_owner_ci_gate_v2.json"
PRIVATE_SHA="bc270e28620c1909fcb34669e6036504b5cae951"
PRIVATE_TREE="59c35abb651cdce18d3131b28497a500ca692cc2"
RELEASE_SHA="6a5ffa4486d0f60a8d39838b8a939b2ff1abee88"
L2_SHA="29dfd7a1a36e45d130d803e1b8a46cad191de50f"
RUN_ID=43693480829

class G07FinalOwnerV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from d06.live.g07_unified_final_owner_gate_v2 import verify_gate
        cls.verify_gate=staticmethod(verify_gate)
    def test_actual_same_runner_l2_metadata_only_grants_wslg_attempt(self):
        data=json.loads(GATE.read_text())
        result=self.verify_gate(data)
        self.assertEqual(result["status"],"ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY")
        self.assertTrue(result["manual_attempt_allowed"])
        self.assertFalse(result["owner_l3_accepted"])
        self.assertFalse(result["full_demo_accepted"])
        self.assertFalse(result["certified_estop"])
        self.assertEqual(data["instructor_source_sha"],PRIVATE_SHA)
        self.assertEqual(data["instructor_tree_sha"],PRIVATE_TREE)
        self.assertEqual(data["public_p4_release_sha"],RELEASE_SHA)
        self.assertEqual(data["ci_gui_l2_run_id"],RUN_ID)
        self.assertEqual(data["ci_gui_l2_workflow_sha"],L2_SHA)
        self.assertFalse(data["actual_wslg_verified"])
        self.assertEqual(data["original_rosbag_topic_count"],14)
        self.assertTrue(data["navigation_shutdown_ack"])
        self.assertTrue(data["localization_shutdown_ack"])
        self.assertEqual(data["cm_exit_code"],0)
    def test_any_missing_or_exceeded_ttl_or_first_latch_fails_closed(self):
        good=json.loads(GATE.read_text())
        for k,bad in (("ci_gui_l2_conclusion","failure"),
                      ("cm_max_ms",151),("cm_rmw_source_max_ms",151),
                      ("guard_max_ms",152),("scan_max_ms",301),
                      ("odom_max_ms",301),("clock_max_ms",300),
                      ("supervisor_max_ms",150),
                      ("first_guard_latch","CM_EXCEEDS_SUPERVISOR"),
                      ("odom_stopped_dwell_sec",.3),
                      ("native_s02_positive_contacts",1),
                      ("original_rosbag_topic_count",13),
                      ("navigation_shutdown_ack",False),
                      ("localization_shutdown_ack",False),
                      ("cm_exit_code",-11),
                      ("instructor_source_sha","db1eec05e01e1db0d0d2e0c05610806ef4e499f9"),
                      ("ci_gui_l2_run_id",43690918618),
                      ("owner_l3_accepted",True),
                      ("actual_wslg_verified",True)):
            data=copy.deepcopy(good)
            data[k]=bad
            with self.subTest(k=k):
                self.assertFalse(self.verify_gate(data)["manual_attempt_allowed"])
    def test_absent_data_is_never_accepted(self):
        good=json.loads(GATE.read_text())
        for k in ("first_guard_latch","cm_max_ms","cm_rmw_source_max_ms",
                  "public_p4_release_sha","ci_gui_l2_workflow_sha",
                  "actual_wslg_verified"):
            data=copy.deepcopy(good);data.pop(k)
            with self.subTest(missing=k):
                self.assertFalse(self.verify_gate(data)["manual_attempt_allowed"])
    def test_v2_owner_wrapper_always_collects_private_custody_and_parity(self):
        self.assertTrue(SCRIPT.is_file())
        src=SCRIPT.read_text()
        self.assertIn(PRIVATE_SHA,src)
        self.assertIn(PRIVATE_TREE,src)
        self.assertIn(RELEASE_SHA,src)
        self.assertIn("scripts/axia_g07_unified_p4_owner_once.sh",src)
        self.assertIn("g07_shared_gui_clients.sh",src)
        self.assertIn("AXIA_G07_UNIFIED_GUI_SIDECAR=1",src)
        self.assertIn("AXIA_G07_GUI_READY_ATTESTATION_PATH=",src)
        self.assertIn("g07_owner_evidence_bundle.py",src)
        self.assertIn("G07_OWNER_FINAL_SINGLE_ATTEMPT_RESERVED",src)
        self.assertIn("43693480829",src)
        self.assertIn("YES-P2-G07-GOAL",src)
        self.assertNotIn('printf "YES-P2-G07-GOAL"',src)
        self.assertNotIn("AXIA_P2_GUARD_BYPASS=1",src)
        self.assertEqual(subprocess.run(["bash","-n",str(SCRIPT)],
                         capture_output=True,text=True).returncode,0)
    def test_readonly_cli_and_no_tty_block_before_ros(self):
        for option in ("--self-check","--admission-check"):
            r=subprocess.run(["bash",str(SCRIPT),option],
                capture_output=True,text=True,timeout=12)
            self.assertEqual(r.returncode,0,option+" "+r.stdout+r.stderr)
            self.assertIn("OWNER",r.stdout)
        r=subprocess.run(["bash",str(SCRIPT)],capture_output=True,text=True,
            env={"PATH":os.environ.get("PATH",""),"HOME":os.environ.get("HOME","/tmp")},
            timeout=8)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("AXIA_G07_FINAL_OWNER_TTY_REQUIRED_NO_ROS_NO_GOAL",r.stdout+r.stderr)

if __name__=="__main__":
    unittest.main()
