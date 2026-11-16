"""Cycle33 public Owner WSL2 one-attempt release admission; no ROS, no Goal.

Real Jazzy/Harmonic/Nav2 GUI L2 Run 43824411236 with CM 118.762ms and
RMW 119.499ms is scoped. Historical Owner Guard 174.185ms remains held
for the OLD source. Never bypass prior SAME source attempt or claim WSLg.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from d06.live.g07_cycle33_owner_ci_gate_v1 import (
    PRIVATE,TREE,CI_RUN,verify_gate,assess_owner_home)
GATE=ROOT/"d06/acceptance/g07_cycle33_owner_ci_gate_v1.json"

class Cycle33OwnerRelease(unittest.TestCase):
    def load(self):return json.loads(GATE.read_text(encoding="utf-8"))
    def test_real_l2_cm_and_rmw_under_120_and_formal_owner_hold(self):
        d=self.load()
        s=verify_gate(d)
        self.assertTrue(s["manual_attempt_allowed"])
        self.assertFalse(s["owner_l3_accepted"])
        self.assertFalse(s["full_demo_accepted"])
        self.assertFalse(s["certified_estop"])
        self.assertEqual(s["ci_run"],43824411236)
        self.assertAlmostEqual(d["max_intervals_ms"]["cm"],118.761562)
        self.assertAlmostEqual(d["cm_rmw_source_max_ms"],119.499)
        self.assertEqual(d["native_s02_positive_contacts"],0)
        self.assertEqual(d["native_s02_observed_iterations"],28087)
        self.assertTrue(d["previous_owner_first_guard_cm_ttl_breach_acknowledged"])
        self.assertFalse(d["new_source_field_fix_causality_proven"])
    def test_tampered_source_run_contact_or_margin_denied(self):
        import copy
        for key,value in (
            ("ci_l2_run_id",43823740312),
            ("instructor_source_sha","0"*40),
            ("native_s02_positive_contacts",1),
            ("first_guard_latch",{"reason":"UPSTREAM_STALE_AFTER_MOTION"}),
            ("cm_rmw_source_max_ms",120.0),
            ("cm_rmw_source_max_ms",float("nan")),
            ("previous_owner_first_guard_cm_ttl_breach_acknowledged",False),
        ):
            with self.subTest(key=key,value=value):
                r=copy.deepcopy(self.load());r[key]=value
                self.assertFalse(verify_gate(r)["manual_attempt_allowed"])
        d=self.load();d["max_intervals_ms"]["cm"]=120
        self.assertFalse(verify_gate(d)["manual_attempt_allowed"])
    def test_old_field_attempt_is_preserved_but_new_source_can_try_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            root=home/".axia_g07_final_owner_attempts"
            old=root/("01d45d46b6eb6a05b1bd313d73f1fc3549575545-43727149856")
            old.mkdir(parents=True)
            (old/"source.txt").write_text("PRIVATE_OLD_OWNER_DO_NOT_DELETE")
            before=(old/"source.txt").read_bytes()
            result=assess_owner_home(self.load(),home)
            self.assertTrue(result["manual_attempt_allowed"])
            self.assertEqual(result["status"],"ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY")
            self.assertEqual(before,(old/"source.txt").read_bytes())
            self.assertFalse((root/(PRIVATE+"-"+str(CI_RUN))).exists())
    def test_same_new_source_and_run_attempt_is_blocked_no_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            existing=home/".axia_g07_final_owner_attempts"/(PRIVATE+"-"+str(CI_RUN))
            existing.mkdir(parents=True)
            (existing/"source.txt").write_text("EXISTING_ATTEMPT")
            s=assess_owner_home(self.load(),home)
            self.assertEqual(s["status"],"CYCLE33_ALREADY_ATTEMPTED_SAME_SOURCE_RUN_HOLD")
            self.assertFalse(s["manual_attempt_allowed"])
            self.assertEqual((existing/"source.txt").read_text(),"EXISTING_ATTEMPT")
    def test_attempt_store_symlink_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            (home/".axia_g07_final_owner_attempts").symlink_to(home)
            s=assess_owner_home(self.load(),home)
            self.assertEqual(s["status"],"CYCLE33_ATTEMPT_STATE_UNTRUSTED_HOLD")
            self.assertFalse(s["manual_attempt_allowed"])
    def test_new_owner_readonly_preflight_no_ros_or_goal(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=ROOT/"d06/live/g07_cycle33_owner_ci_gate_v1.py"
            r=subprocess.run(["python3",str(p),"--home",tmp,
              "--gate",str(GATE),"--private-sha",PRIVATE,
              "--private-tree",TREE,"--ci-run",str(CI_RUN)],
              capture_output=True,text=True,timeout=10,
              env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",r.stdout)
            self.assertIn("manual_attempt_allowed\": true",r.stdout)
            self.assertFalse((Path(tmp)/".axia_g07_final_owner_attempts").exists())
    def test_owner_scripts_same_exact_pin_ci_source_and_no_auto_tty_goal(self):
        p4=ROOT/"scripts/axia_g07_cycle33_p4_owner_once.sh"
        owner=ROOT/"d06/scripts/g07_cycle33_owner_wsl2_once.sh"
        bootstrap=ROOT/"scripts/axia_g07_cycle33_owner_wsl2_bootstrap.sh"
        for p in (p4,owner,bootstrap):
            self.assertTrue(p.is_file(),str(p))
            s=p.read_text(encoding="utf-8")
            for pin in (PRIVATE,str(CI_RUN)):
                self.assertIn(pin,s,str(p))
            self.assertNotIn("AXIA_G07_CI_SIM_GOAL_ALLOWED=1",s)
            self.assertNotIn("rm -rf -- \"$HOME/.axia_g07_final_owner_attempts",s)
            r=subprocess.run(["bash","-n",str(p)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
        p=owner.read_text()
        self.assertIn("g07_cycle33_owner_ci_gate_v1.py",p)
        self.assertLess(p.index("FIELD_GATE="),p.index('ATTEMPT_ROOT="$HOME/'))
        self.assertIn("YES-P2-G07-GOAL",p4.read_text())
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",p4.read_text())
    def test_exact_ci_public_marker_cpu_matches_owner_profile(self):
        from d06.live.d06_gui_cpu_plan import select_monitor_cpu
        self.assertEqual(select_monitor_cpu([0,1,2,3]),3)
        self.assertEqual(select_monitor_cpu(list(range(8))),2)
    def test_owner_self_check_no_ros_p4(self):
        p=ROOT/"scripts/axia_g07_cycle33_p4_owner_once.sh"
        r=subprocess.run(["bash",str(p),"--self-check"],
                         capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn(PRIVATE,r.stdout)
        self.assertIn("NO_ROS_NO_GOAL",r.stdout)


    def test_bootstrap_pinned_checkout_has_actual_gate_and_checker(self):
        """Regression: never advertise Owner release if pinned checkout lacks dependencies."""
        import re
        bootstrap=(ROOT/"scripts/axia_g07_cycle33_owner_wsl2_bootstrap.sh").read_text()
        for variable in ("GATE","CHECK","OWNER"):
            match=re.search(r'(?m)^'+variable+r'="\\$WORK/([^"]+)"    unittest.main()
,bootstrap)
            self.assertIsNotNone(match,f"missing pinned {variable} binding")
            required=ROOT/match.group(1)
            self.assertTrue(required.is_file(),f"pinned checkout missing {variable}: {required}")
        self.assertIn('readonly RELEASE_SHA=',bootstrap)
        self.assertIn('readonly RELEASE_TREE=',bootstrap)

if __name__=="__main__":
    unittest.main()
