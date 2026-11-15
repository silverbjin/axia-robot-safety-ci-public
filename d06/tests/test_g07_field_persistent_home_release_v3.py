"""CI-first contract: sanitized prior Owner Guard TTL and persistent WSL2 attempt.
Only stdlib. No ROS, Goal, source upload or automatic lock removal.
"""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "d06/tests/fixtures/g07_field_first_guard_158ms_sanitized_v1.json"
GATE = ROOT / "d06/acceptance/g07_unified_final_owner_ci_gate_v2.json"
SOURCE = "bc270e28620c1909fcb34669e6036504b5cae951"
RUN = 43693480829

class TestFieldReleaseV3(unittest.TestCase):
    def test_field_first_safety_transition_is_guard_ttl_not_rmw_clock_step(self):
        from d06.live.g07_owner_field_preflight_v3 import classify_guard_first_failure
        evidence=json.loads(FIXTURE.read_text())
        result=classify_guard_first_failure(evidence)
        self.assertEqual(result["first_failure"], "GUARD_INTERNAL_CM_TTL_BREACH")
        self.assertEqual(result["first_transition"], "UPSTREAM_STALE_AFTER_MOTION")
        self.assertFalse(result["owner_release_allowed"])
        self.assertTrue(result["rmw_epoch_step_only_candidate"])
        self.assertEqual(result["limit_ms"], 150)
        self.assertAlmostEqual(result["actual_ms"], 158.007666)

    def test_existing_failed_attempt_blocked_readonly_before_admission(self):
        from d06.live.g07_owner_field_preflight_v3 import inspect_persistent_home
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            attempt=home/".axia_g07_final_owner_attempts"/f"{SOURCE}-{RUN}"
            attempt.mkdir(parents=True)
            (attempt/"source.txt").write_text(f"private_sha={SOURCE}\nci_run={RUN}\n")
            before=list(attempt.iterdir())
            result=inspect_persistent_home(home,SOURCE,RUN)
            self.assertEqual(result["status"],"BLOCKED_EXISTING_FAILED_ATTEMPT")
            self.assertFalse(result["owner_attempt_eligible"])
            self.assertTrue(attempt.exists())
            self.assertEqual(before,list(attempt.iterdir()))

    def test_clean_home_preflight_is_readonly(self):
        from d06.live.g07_owner_field_preflight_v3 import inspect_persistent_home
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            result=inspect_persistent_home(home,SOURCE,RUN)
            self.assertEqual(result["status"],"NO_PRIOR_ATTEMPT")
            self.assertFalse((home/".axia_g07_final_owner_attempts").exists())

    def test_symlink_attempt_is_blocked_without_following(self):
        from d06.live.g07_owner_field_preflight_v3 import inspect_persistent_home
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            root=home/".axia_g07_final_owner_attempts"
            root.mkdir()
            (root/f"{SOURCE}-{RUN}").symlink_to(home)
            result=inspect_persistent_home(home,SOURCE,RUN)
            self.assertEqual(result["status"],"BLOCKED_UNTRUSTED_ATTEMPT_STATE")
            self.assertFalse(result["owner_attempt_eligible"])

    def test_original_ci_pass_has_insufficient_120ms_cm_margin(self):
        from d06.live.g07_owner_field_preflight_v3 import evaluate_release
        gate=json.loads(GATE.read_text())
        result=evaluate_release(gate)
        self.assertEqual(result["status"],"CI_L2_PASS_LOW_MARGIN")
        self.assertFalse(result["owner_attempt_eligible"])
        self.assertEqual(result["safety_hard_cm_ms"],150)
        self.assertEqual(result["release_target_cm_ms"],120)
        self.assertGreater(gate["cm_max_ms"],120)
        self.assertLess(gate["cm_max_ms"],150)

    def test_missing_or_invalid_gate_stays_hold(self):
        from d06.live.g07_owner_field_preflight_v3 import evaluate_release
        self.assertFalse(evaluate_release({})["owner_attempt_eligible"])
        self.assertFalse(evaluate_release({"cm_max_ms":99})["owner_attempt_eligible"])

    def test_existing_v2_does_not_automatically_release_again(self):
        # Historical v2 is SHA-pinned. The new release must use a versioned
        # preflight before any print of an Owner eligibility marker.
        new=ROOT/"d06/scripts/g07_owner_field_readonly_preflight_v3.sh"
        self.assertTrue(new.is_file(), "V3_NO_GOAL_PREFLIGHT_MISSING")
        src=new.read_text()
        self.assertIn("g07_owner_field_preflight_v3.py",src)
        self.assertNotIn("YES-P2-G07-GOAL",src)
        self.assertNotIn("ros2 action send_goal",src)
        self.assertNotIn("mkdir -m 700",src)


    def test_field_cli_from_owner_home_without_repo_pythonpath(self):
        import os
        import subprocess
        from pathlib import Path
        runner=ROOT/"d06/scripts/g07_owner_field_readonly_preflight_v3.sh"
        with tempfile.TemporaryDirectory() as tmp:
            env=os.environ.copy()
            env.pop("PYTHONPATH",None)
            env["HOME"]=tmp
            result=subprocess.run(["bash",str(runner)],cwd=tmp,
                                  capture_output=True,text=True,
                                  timeout=10,env=env)
            self.assertEqual(result.returncode,3)
            self.assertIn("AXIA_G07_OWNER_FIELD_READONLY",result.stdout)
            self.assertIn("FIELD_GUARD_TTL_BREACH_OWNER_RELEASE_HOLD",result.stdout)
            self.assertFalse((Path(tmp)/".axia_g07_final_owner_attempts").exists())

    def test_no_goal_static_self_check_does_not_write_pycache(self):
        import os
        import subprocess
        script=ROOT/"d06/scripts/g07_owner_field_readonly_preflight_v3.sh"
        with tempfile.TemporaryDirectory() as tmp:
            before=set(ROOT.glob("d06/live/__pycache__/*"))
            r=subprocess.run(["bash",str(script),"--self-check"],
                             cwd=tmp,capture_output=True,text=True,
                             timeout=10,env={**os.environ,"HOME":tmp})
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertEqual(before,set(ROOT.glob("d06/live/__pycache__/*")))

if __name__ == "__main__":
    unittest.main()
