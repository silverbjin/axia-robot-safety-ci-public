"""D06's classroom-only wrapper must reuse G07 evidence without faking Owner authority."""
from pathlib import Path
import subprocess
import tempfile
import os
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'd06/scripts/axia_d06_g07_classroom_once.sh'


class D06ClassroomReuse(unittest.TestCase):
    def test_real_task03_and_task04_source_pins(self):
        src = RUNNER.read_text()
        for expected in (
            '01752add2e30c90c4d3286ef3a450f97746ecb55',
            '6bc8b0711ab056e63e100f3eede2c5f06cdf3856',
            '44223320904',
            '5bb0cd72086f2f1a057f382649b773fff106f1f9',
            '44238643061',
            'a15cf37e1a1d2a0253029c0a1dd8e2530e307c25',
        ):
            self.assertIn(expected, src)

    def test_no_local_goal_or_ci_permission_spoof(self):
        src = RUNNER.read_text()
        for forbidden in (
            'GITHUB_ACTIONS=true', 'export GITHUB_ACTIONS',
            'AXIA_G07_CI_SIM_GOAL_ALLOWED=1', 'ros2 action send_goal',
            'ros2 topic pub', 'pkill -f', 'killall', 'wsl --shutdown',
        ):
            self.assertNotIn(forbidden, src)
        self.assertIn('D06_G07_OWNER_REAL_TTY_REQUIRED_NO_GOAL', src)
        self.assertIn('AXIA_MVP_DEMO_ACCEPTED=HOLD', src)

    def test_static_self_check_is_offline_and_no_goal(self):
        result = subprocess.run(['bash', str(RUNNER), '--self-check'], text=True,
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('D06_G07_CLASSROOM_STATIC_PASS', result.stdout)
        self.assertIn('NO_ROS_NO_GOAL', result.stdout)

    def test_owner_live_without_tty_fails_closed_before_download(self):
        result = subprocess.run(['bash', str(RUNNER), '--live'], text=True,
                                capture_output=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('D06_G07_OWNER_REAL_TTY_REQUIRED_NO_GOAL',
                      result.stdout + result.stderr)
        self.assertIn('AXIA_MVP_DEMO_ACCEPTED=HOLD',
                      result.stdout + result.stderr)

    def test_owner_gui_path_rejects_github_actions_before_download(self):
        result = subprocess.run(['bash', str(RUNNER), '--gui-only'], text=True,
                                capture_output=True, timeout=5,
                                env={'GITHUB_ACTIONS':'true','PATH':'/usr/bin:/bin'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('D06_G07_CLASSROOM_OWNER_WSL2_ONLY',
                      result.stdout + result.stderr)

    def test_ci_status_explicitly_says_no_gui_launched(self):
        src = RUNNER.read_text()
        self.assertIn('D06_G07_CLASSROOM_VERIFICATION_ONLY_NO_GAZEBO_NO_RVIZ', src)
        self.assertIn('D06_G07_CLASSROOM_MOVING_ACTION=--live_MANUAL_TTY_OWNER_CANDIDATE', src)

    def test_last_green_task04_pinned_with_all_native_l2_gates(self):
        src = RUNNER.read_text()
        for exact in (
            '44249348860',
            '6b98a18fa7abc80401a129f715ace7703ab54286',
            '1129cd8804954fd6481d1b6b4ebf0e0b98c68c3c',
        ):
            self.assertIn(exact, src)
        self.assertIn('TASK04_MOVING', src)

    def test_owner_live_reuses_proven_g07_manual_runner(self):
        src = RUNNER.read_text()
        self.assertIn('run_verified_owner', src)
        self.assertIn('AXIA_G07_TASK04_OWNER_MOVING_L3=1', src)
        self.assertIn('AXIA_G07_TASK04_EXPECTED_STUDENT_SHA', src)
        self.assertIn('scripts/p2_no_goal_smoke_ci.sh', src)
        self.assertIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=0', src)
        self.assertNotIn('export GITHUB_ACTIONS=true', src)
        self.assertNotIn('ros2 action send_goal', src)

    def test_live_evidence_exit_trap_survives_function_return(self):
        src = RUNNER.read_text()
        self.assertIn('D06_OWNER_OUT=', src)
        self.assertIn('trap finish_owner EXIT', src)
        self.assertIn('sha256sum "$D06_OWNER_OUT.tar.gz"', src)

    def test_ci_status_uses_exact_three_success_run_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            gh = Path(tmp) / "gh"
            gh.write_text("""#!/bin/sh
case "$2" in
  */44223320904) echo '6bc8b0711ab056e63e100f3eede2c5f06cdf3856 completed success' ;;
  */44238643061) echo '5bb0cd72086f2f1a057f382649b773fff106f1f9 completed success' ;;
  */44249348860) echo '6b98a18fa7abc80401a129f715ace7703ab54286 completed success' ;;
  *) exit 2 ;;
esac
""")
            gh.chmod(0o755)
            env = {**os.environ, "PATH":tmp+os.pathsep+os.environ.get("PATH","")}
            env.pop("GITHUB_ACTIONS",None)
            r = subprocess.run(["bash",str(RUNNER),"--ci-status"],env=env,
                               text=True,capture_output=True,timeout=7)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('TASK04_MOVING_HISTORICAL_CI_PASS run=44249348860',r.stdout)
            self.assertIn('VERIFICATION_ONLY_NO_GAZEBO_NO_RVIZ',r.stdout)
            self.assertIn('OWNER_MOVING_L3=NOT_RUN',r.stdout)

    def test_ci_status_rejects_stale_green_source_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            gh = Path(tmp) / "gh"
            gh.write_text("""#!/bin/sh
case "$2" in
  */44223320904) echo '6bc8b0711ab056e63e100f3eede2c5f06cdf3856 completed success' ;;
  */44238643061) echo '5bb0cd72086f2f1a057f382649b773fff106f1f9 completed success' ;;
  */44249348860) echo '09b2c7cf54ff1074ff4439008a3cb1a6fb1355de completed failure' ;;
  *) exit 2 ;;
esac
""")
            gh.chmod(0o755)
            env = {**os.environ, "PATH":tmp+os.pathsep+os.environ.get("PATH","")}
            env.pop("GITHUB_ACTIONS",None)
            r = subprocess.run(["bash",str(RUNNER),"--ci-status"],env=env,
                               text=True,capture_output=True,timeout=7)
            self.assertEqual(r.returncode,3)
            self.assertIn('TASK04_MOVING_CI_SOURCE_OR_CONCLUSION_MISMATCH',r.stderr)

    def test_owner_embedded_readonly_verifier_compiles(self):
        src = RUNNER.read_text()
        marker = """python3 - "$runtime" "$out/native" "$out/owner_readonly_gate.json" <<'PY'\n"""
        self.assertIn(marker,src)
        body = src.split(marker,1)[1].split("\nPY\n",1)[0]
        compile(body,"d06_owner_readonly_gate.py","exec")
        self.assertIn("audit_guard_internal_cm_age",body)
        self.assertIn("GUARD_NATIVE_CM_AGE_TTL150_PASS",body)
        self.assertIn('w.get("missing_iterations")==0',body)
        self.assertIn('root/"rosbag2"',body)
        self.assertIn('"owner_l3_accepted":False',body)

    def test_owner_raw_archive_failure_and_candidate_verdict_separated(self):
        src = RUNNER.read_text()
        self.assertIn('D06_G07_OWNER_CUSTODY_ARCHIVE_UNVERIFIED_HOLD',src)
        self.assertIn('D06_G07_OWNER_L3=HOLD_FAILED_OR_BLOCKED',src)
        self.assertIn('D06_G07_OWNER_L3=RAW_REVIEW_REQUIRED_NOT_ACCEPTED',src)
        self.assertIn('[[ -s "$D06_OWNER_OUT.tar.gz" ]]',src)

    def test_unknown_flags_fail_closed(self):
        result = subprocess.run(['bash', str(RUNNER), '--foo'], text=True,
                                capture_output=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('D06_G07_CLASSROOM_USAGE', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
