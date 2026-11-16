"""CI-first regression for exact Owner WSL2 Guard 174ms / CM RMW 186ms failure.

Covers the real no-Goal repeat block and the PREVIOUS actual Owner Goal.
No private ROS bag, personal Goal UUID, ROS or Gazebo. Ubuntu 24.04 L0 only.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/"d06/tests/fixtures/g07_cycle17_wsl2_guard_174ms_rmw_186ms_sanitized.json"
GATE=ROOT/"d06/acceptance/g07_cycle16_owner_ci_gate_v3.json"
MODULE=ROOT/"d06/live/g07_cycle18_field_owner_admission_v5.py"
SCRIPT=ROOT/"scripts/axia_g07_cycle18_owner_readonly_preflight.sh"
PRIVATE="01d45d46b6eb6a05b1bd313d73f1fc3549575545"
RUN=43727149856

class TestRealFirstOwnerFieldFailure(unittest.TestCase):
    def fixture(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def gate(self):
        return json.loads(GATE.read_text(encoding="utf-8"))

    def load(self):
        from d06.live.g07_cycle18_field_owner_admission_v5 import assess_field_admission
        return assess_field_admission

    def make_lock(self,home):
        attempt=home/".axia_g07_final_owner_attempts"/f"{PRIVATE}-{RUN}"
        attempt.mkdir(parents=True)
        (attempt/"source.txt").write_text(f"private_sha={PRIVATE}\nci_run={RUN}\n")
        return attempt

    def test_sanitized_actual_174ms_guard_and_186ms_cm_are_not_ci_success(self):
        e=self.fixture()
        self.assertEqual(e["source_sha"],PRIVATE)
        self.assertEqual(e["first_guard_transition"],"UPSTREAM_STALE_AFTER_MOTION")
        self.assertGreater(e["first_guard_cm_age_ms"],e["guard_cm_hard_ttl_ms"])
        self.assertGreater(e["first_cm_rmw_source_gap_ms"],e["guard_cm_hard_ttl_ms"])
        self.assertEqual(e["supervisor_publications_inside_cm_gap"],4)
        self.assertLess(e["ci_l2_max_cm_observer_ms"],e["cm_release_target_ms"])
        self.assertTrue(e["previous_goal_observed"])
        self.assertFalse(e["owner_l3_accepted"])

    def test_same_sha_run_previous_actual_goal_forbids_new_owner_release(self):
        assess=self.load()
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            attempt=self.make_lock(home)
            before=(attempt/"source.txt").read_bytes()
            d=assess(self.gate(),self.fixture(),home)
            self.assertEqual(d["status"],"FIELD_PREVIOUS_GOAL_CM_TTL_BREACH_HOLD")
            self.assertEqual(d["first_safety_transition"],"UPSTREAM_STALE_AFTER_MOTION")
            self.assertAlmostEqual(d["first_cm_rmw_source_gap_ms"],186.714207)
            self.assertEqual(d["supervisor_publications_inside_cm_gap"],4)
            self.assertTrue(d["previous_same_source_attempt_exists"])
            self.assertFalse(d["manual_attempt_allowed"])
            self.assertFalse(d["owner_l3_accepted"])
            self.assertTrue(d["no_ros_no_goal"])
            self.assertEqual(before,(attempt/"source.txt").read_bytes())

    def test_removing_lock_cannot_overrule_known_field_ttl_breach(self):
        assess=self.load()
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            d=assess(self.gate(),self.fixture(),home)
            self.assertEqual(d["status"],"FIELD_PREVIOUS_GOAL_CM_TTL_BREACH_HOLD")
            self.assertFalse(d["manual_attempt_allowed"])
            self.assertFalse((home/".axia_g07_final_owner_attempts").exists())

    def test_prior_lock_without_first_failure_data_still_hold(self):
        assess=self.load()
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            attempt=self.make_lock(home)
            d=assess(self.gate(),None,home)
            self.assertEqual(d["status"],"FIELD_PREVIOUS_ATTEMPT_UNVERIFIED_HOLD")
            self.assertFalse(d["manual_attempt_allowed"])
            self.assertTrue(attempt.is_dir())

    def test_missing_previous_field_history_on_clean_home_does_not_create_permission(self):
        assess=self.load()
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            d=assess(self.gate(),None,home)
            self.assertEqual(d["status"],"FIELD_HISTORY_UNVERIFIED_HOLD")
            self.assertFalse(d["manual_attempt_allowed"])
            self.assertFalse((home/".axia_g07_final_owner_attempts").exists())

    def test_symlink_attempt_store_fails_closed(self):
        assess=self.load()
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            (home/".axia_g07_final_owner_attempts").symlink_to(home)
            d=assess(self.gate(),self.fixture(),home)
            self.assertEqual(d["status"],"FIELD_ATTEMPT_STATE_UNTRUSTED_HOLD")
            self.assertFalse(d["manual_attempt_allowed"])

    def test_tampered_ci_gate_is_rejected_before_field_release(self):
        assess=self.load()
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            d=assess(self.gate()|{"max_intervals_ms":self.gate()["max_intervals_ms"]|{"cm":150.0}},
                     self.fixture(),home)
            self.assertEqual(d["status"],"CI_L2_EVIDENCE_INVALID_HOLD")
            self.assertFalse(d["manual_attempt_allowed"])

    def test_cli_same_owner_home_first_transition_without_any_ros(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            attempt=self.make_lock(home)
            before=(attempt/"source.txt").read_bytes()
            r=subprocess.run(["python3",str(MODULE),"--home",str(home),
                "--ci-gate",str(GATE),"--field-evidence",str(FIXTURE)],
                cwd=tmp,capture_output=True,text=True,timeout=10,
                env={**os.environ,"HOME":tmp,"PYTHONDONTWRITEBYTECODE":"1"})
            self.assertEqual(r.returncode,3,r.stdout+r.stderr)
            self.assertIn("FIELD_PREVIOUS_GOAL_CM_TTL_BREACH_HOLD",r.stdout)
            self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",r.stdout)
            self.assertNotIn("D06_RVIZ_NOT_CONFIRMED",r.stdout)
            self.assertNotIn("ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY",r.stdout)
            self.assertEqual(before,(attempt/"source.txt").read_bytes())

    def test_real_owner_wrapper_and_bootstrap_gate_field_history_before_ci_admission(self):
        wrapper=(ROOT/"d06/scripts/g07_cycle16_owner_wsl2_once.sh").read_text()
        bootstrap=(ROOT/"scripts/axia_g07_cycle16_owner_wsl2_bootstrap.sh").read_text()
        field="g07_cycle18_field_owner_admission_v5.py"
        self.assertIn(field,wrapper)
        self.assertIn(field,bootstrap)
        self.assertLess(bootstrap.index(field),
                        bootstrap.index('echo "AXIA_G07_CYCLE16_CI_REAL_GUI_L2_PASS_RUN='))
        self.assertLess(wrapper.index(field),
                        wrapper.index("ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY previous_"))
        self.assertLess(wrapper.index(field),wrapper.index('ATTEMPT_ROOT="$HOME/'))
        self.assertIn("FIELD_PREVIOUS_GOAL_CM_TTL_BREACH_HOLD",bootstrap)

    def test_actual_owner_readonly_entrypoint_matches_ci_and_has_no_goal(self):
        src=SCRIPT.read_text(encoding="utf-8")
        self.assertIn("g07_cycle18_field_owner_admission_v5.py",src)
        self.assertIn("g07_cycle17_wsl2_guard_174ms_rmw_186ms_sanitized.json",src)
        self.assertNotIn("ros2 action send_goal",src)
        self.assertNotIn("YES-P2-G07-GOAL",src)
        self.assertNotIn("rm -rf",src)
        with tempfile.TemporaryDirectory() as tmp:
            r=subprocess.run(["bash",str(SCRIPT),"--self-check"],cwd=tmp,
                capture_output=True,text=True,timeout=10,
                env={**os.environ,"HOME":tmp})
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertIn("NO_ROS_NO_GOAL",r.stdout)
            self.assertFalse((Path(tmp)/".axia_g07_final_owner_attempts").exists())

if __name__=="__main__":
    unittest.main()
