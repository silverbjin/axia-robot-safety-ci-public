"""AXIA Cycle16 Owner one-attempt release contract (public L0, NO ROS/Goal).

The failed bc270... field attempt is immutable historical evidence and must
not be erased/replayed. This new release is for 01d45... / CI 43727149856.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
PRIVATE="01d45d46b6eb6a05b1bd313d73f1fc3549575545"
TREE="38de92dda3c17221b337f140bbc1b2aecd805da4"
CI_RUN=43727149856
HIST="bc270e28620c1909fcb34669e6036504b5cae951"
HIST_RUN=43693480829
GATE=ROOT/"d06/acceptance/g07_cycle16_owner_ci_gate_v3.json"
MODULE=ROOT/"d06/live/g07_cycle16_owner_ci_gate_v4.py"
WRAPPER=ROOT/"d06/scripts/g07_cycle16_owner_wsl2_once.sh"
P4=ROOT/"scripts/axia_g07_cycle16_p4_owner_once.sh"

class TestOwnerCycle16(unittest.TestCase):
    def load(self):
        spec=importlib.util.spec_from_file_location("g07_cycle16_owner_ci_gate_v4",MODULE)
        m=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_exact_real_l2_gate_admits_one_manual_attempt_not_acceptance(self):
        m=self.load()
        candidate=json.loads(GATE.read_text())
        r=m.verify_cycle16_gate(candidate)
        self.assertEqual(r["status"],"ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY")
        self.assertTrue(r["manual_attempt_allowed"])
        self.assertFalse(r["owner_l3_accepted"])
        self.assertFalse(r["certified_estop"])
        self.assertEqual(r["ci_run"],CI_RUN)

    def test_tampering_source_run_or_timing_release_margin_blocks(self):
        m=self.load()
        good=json.loads(GATE.read_text())
        bads=[
            {"instructor_source_sha":HIST},
            {"ci_l2_workflow_sha":"0"*40},
            {"ci_l2_run_id":HIST_RUN},
            {"cm_exit_code":1},
            {"first_guard_latch":{"reason":"UPSTREAM_STALE_AFTER_MOTION"}},
            {"native_s02_positive_contacts":1},
            {"max_intervals_ms":good["max_intervals_ms"]|{"cm":120.001}},
            {"max_intervals_ms":good["max_intervals_ms"]|{"supervisor":151.0}},
            {"max_intervals_ms":good["max_intervals_ms"]|{"scan":301.0}},
            {"owner_l3_accepted":True},
        ]
        for change in bads:
            with self.subTest(change=change):
                r=m.verify_cycle16_gate(good|change)
                self.assertFalse(r["manual_attempt_allowed"])
                self.assertFalse(r["owner_l3_accepted"])

    def test_persistent_historical_attempt_cannot_be_deleted_or_reused(self):
        wrapper=WRAPPER.read_text()
        self.assertIn(PRIVATE,wrapper)
        self.assertIn(str(CI_RUN),wrapper)
        self.assertIn('mkdir -m 700 "$ATTEMPT_ROOT/$ATTEMPT_NAME"',wrapper)
        self.assertIn("AXIA_G07_FINAL_OWNER_REPEAT_BLOCKED",wrapper)
        self.assertNotIn('rm -rf -- "$ATTEMPT_ROOT"',wrapper)
        self.assertNotIn('rmdir "$ATTEMPT_ROOT"',wrapper)
        self.assertNotIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=1',wrapper)
        self.assertNotIn("YES-P2-G07-GOAL\\n",wrapper)

    def test_exact_private_runner_and_gui_are_shared_not_forged(self):
        wrapper=WRAPPER.read_text()
        p4=P4.read_text()
        self.assertIn("g07_shared_gui_clients.sh",wrapper)
        self.assertIn("d06_rviz_sidecar.sh",wrapper)
        self.assertIn("axia_g07_cycle16_p4_owner_once.sh",wrapper)
        self.assertIn("scripts/p2_owner_l3_wsl2.sh",p4)
        self.assertIn("--case G07 --mvp-relocated-obstacle",p4)
        self.assertIn(PRIVATE,p4)
        self.assertIn(TREE,p4)
        self.assertIn(str(CI_RUN),p4)
        self.assertNotIn(HIST,p4)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",p4)

    def test_self_check_does_not_create_attempt_or_require_ros(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=subprocess.run(["bash",str(WRAPPER),"--self-check"],
                             cwd=tmp,env={**os.environ,"HOME":tmp},
                             capture_output=True,text=True,timeout=15)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertIn("NO_ROS_NO_GOAL",r.stdout)
            self.assertFalse((Path(tmp)/".axia_g07_final_owner_attempts").exists())

    def test_gate_cli_from_arbitrary_home_is_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=subprocess.run(["python3",str(MODULE),"--gate",str(GATE),
                              "--private-sha",PRIVATE,"--ci-run",str(CI_RUN)],
                              cwd=tmp,env={**os.environ,"HOME":tmp},
                              capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertIn("ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY",r.stdout)
            self.assertIn("OWNER_NOT_ACCEPTED",r.stdout)
            self.assertFalse((Path(tmp)/".axia_g07_final_owner_attempts").exists())

if __name__=="__main__":
    unittest.main()
