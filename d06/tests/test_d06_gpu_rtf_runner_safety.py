"""The GPU comparison is precisely one no-goal session per verified adapter."""
import pathlib
import re
import subprocess
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh"
OWNER=ROOT/"d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh"

class WslgABOneShotSafety(unittest.TestCase):
    def test_true_no_goal_only_and_last_case_intel(self):
        s=SCRIPT.read_text()
        self.assertIn('adapters=(NVIDIA Intel)',s)
        self.assertIn('MESA_D3D12_DEFAULT_ADAPTER_NAME="$gpu"',s)
        self.assertIn('glxinfo -B',s)
        self.assertIn('D06_GPU_RTF_ACTUAL_RENDERER_MISMATCH',s)
        self.assertIn('D06_GPU_RTF_WORLD_OR_WAFFLE_NOT_IDENTICAL',s)
        self.assertIn('D06_GPU_RTF_NVIDIA_SHUTDOWN_CRASH_ABORT_SECOND_RUN',s)
        self.assertIn('--run > "$RUN_DIR/$lc.run.log"',s)
        self.assertNotIn('YES-P2-G07-GOAL',s)
        self.assertNotIn('export GITHUB_ACTIONS=true',s)
        self.assertIn('D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false',s)

    def test_nvidia_single_no_goal_d08_reuse_never_runs_intel_or_goal(self):
        s=SCRIPT.read_text()
        self.assertIn('--nvidia-only', s)
        self.assertIn('--nvidia-causal', s)
        self.assertIn('AXIA_D06_G07_RX_WITNESS=', s)
        self.assertIn('D06_G07_NATIVE_RX_NO_LAYER_REPORT_NO_GOAL', s)
        self.assertIn('for gpu in "${adapters[@]}";do', s)
        self.assertIn('adapters=(NVIDIA)', s)
        self.assertIn('D06_GPU_RTF_NVIDIA_ONLY_NO_GOAL', s)
        self.assertIn('D06_GPU_RTF_NVIDIA_SENSOR_CANDIDATE_NOT_ACCEPTED', s)
        self.assertIn('D06_GAZEBO_LIVE_RELEASE=HOLD', s)
        self.assertNotIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=1', s)

    def test_no_goal_native_segv_is_separate_failure_even_with_good_sensor(self):
        s=SCRIPT.read_text()
        self.assertIn('D06_GPU_RTF_NATIVE_SHUTDOWN_SEGV_HOLD', s)
        self.assertIn('exit code -11', s)
        self.assertIn('D06_GPU_RTF_NVIDIA_ONLY_NO_GOAL', s)

    def test_pin_source_commit_and_git_blobs(self):
        s=SCRIPT.read_text()
        self.assertIn("50464f39b2c37dd631768c4ea98c9bdad2d1127c",s)
        self.assertIn("d441c1e5b59287a23270884c759f9671895b1c0b",s)
        self.assertIn("171aad7ce8abe97c93a42f19787042619c06b65e",s)
        self.assertIn('git hash-object "$TMP/owner.sh"',s)
        self.assertIn('git hash-object "$TMP/compare.py"',s)
        o=OWNER.read_text()
        self.assertIn("50464f39b2c37dd631768c4ea98c9bdad2d1127c",o)
        self.assertIn("1f00c7118f55ed72257155b92e83a98d6dcbc017",o)

    def test_fr1_native_gz_witness_pinned_unsubscribe_and_proven_before_nav2(self):
        o=OWNER.read_text()
        self.assertIn("D06_GZ_SAFE_RECEIVER_SHA='7b4b6b553d13c07dd8fc60f4f9a065500cf1cb9a'",o)
        self.assertIn("D06_GZ_SAFE_RECEIVER_BLOB='653ec644e80eb832f32c4db6ed46a5a0db02b60d'",o)
        self.assertIn("d06/tools/d06_gz_native_scan_probe_safe.py",o)
        self.assertIn("D06_GZ_NATIVE_SUBSCRIPTIONS_RELEASED",o)
        self.assertIn("D06_GZ_NATIVE_RX_UNSUBSCRIBE_BEFORE_NAV2_SHUTDOWN_PASS",o)
        self.assertIn("export AXIA_G07_NO_GOAL_GZ_STOP_BEFORE_SIGINT=1",o)
        self.assertIn("50464f39b2c37dd631768c4ea98c9bdad2d1127c",o)
        self.assertIn("ca4af428c59716b46b9bc6bde6f25ea47d6d4e68",o)
        self.assertNotIn("D08_RECEIVER_BLOB",o)
        probe=ROOT/"d06/tools/d06_gz_native_scan_probe_safe.py"
        check=subprocess.run(["git","hash-object",str(probe)],capture_output=True,text=True,check=True)
        self.assertEqual(check.stdout.strip(),"653ec644e80eb832f32c4db6ed46a5a0db02b60d")

    def test_tcljt2qc_student_source_probe_hash_matches_actual_checkout(self):
        """Regression: TCljt2Qc first error was frozen source blob mismatch.

        L0 CI explicitly checks out the exact Student commit. Validate all
        three blobs against actual bytes so future pin drift fails before
        another physical WSL2 launch.
        """
        text=OWNER.read_text()
        expected_ref="50464f39b2c37dd631768c4ea98c9bdad2d1127c"
        self.assertIn("readonly STUDENT_SHA='"+expected_ref+"'",text)
        student=ROOT/"student"
        self.assertTrue(student.is_dir(),
                        "PUBLIC_CI_STUDENT_PINNED_CHECKOUT_REQUIRED")
        manifest={
            "PROBE_BLOB":"tools/g07_wslg_no_goal_sensor_probe.py",
            "SMOKE_BLOB":"scripts/p2_no_goal_smoke_ci.sh",
            "LAUNCH_BLOB":"ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p2.launch.py"
        }
        runtime=student/"block_B/day07/h01_runtime"
        for name,relative in manifest.items():
            match=re.search(r"readonly "+name+r"='([0-9a-f]{40})'",text)
            self.assertIsNotNone(match,name)
            target=runtime/relative
            self.assertTrue(target.is_file(),relative)
            proc=subprocess.run(["git","hash-object",str(target)],
                                text=True,capture_output=True,timeout=5,
                                check=True)
            self.assertEqual(match.group(1),proc.stdout.strip(),
                             "D06_TCLJT2QC_PIN_DRIFT_"+name+" "+relative)

    def test_single_wslg_owner_stops_external_witnesses_before_official_shutdown(self):
        o=OWNER.read_text()
        self.assertIn("export AXIA_G07_NO_GOAL_WITNESS_HANDOFF=1",o)
        self.assertIn('g07_witness_probe_complete.signal',o)
        self.assertIn('g07_witness_stopped.ack',o)
        self.assertIn('G07_READONLY_WITNESSES_STOPPED',o)
        self.assertIn('SMOKE_PID=$!',o)
        self.assertIn('wait "$SMOKE_PID"',o)
        self.assertIn('D06_G07_WSLG_READONLY_WITNESS_HANDOFF_DONE_BEFORE_SHUTDOWN',o)
        self.assertNotIn('export AXIA_G07_CI_SIM_GOAL_ALLOWED=1',o)
        self.assertEqual(subprocess.run(["bash","-n",str(OWNER)],
                                      capture_output=True,text=True).returncode,0)

    def test_bash_syntax_self_check_and_ci_owner_denial(self):
        chk=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True,timeout=5)
        self.assertEqual(chk.returncode,0,chk.stderr)
        valid=subprocess.run(["bash",str(SCRIPT),"--self-check"],capture_output=True,text=True,timeout=5)
        self.assertEqual(valid.returncode,0,valid.stderr)
        self.assertIn("NO_GAZEBO_NO_GOAL",valid.stdout)
        for mode in ("--compare","--nvidia-only","--nvidia-causal"):
            denied=subprocess.run(["bash",str(SCRIPT),mode],capture_output=True,text=True,timeout=5,
                                 env={"PATH":"/usr/bin:/bin","GITHUB_ACTIONS":"true"})
            self.assertEqual(denied.returncode,3,(mode,denied.stdout,denied.stderr))
            self.assertIn("D06_GPU_RTF_REAL_WSLG_REQUIRED",denied.stderr)

if __name__=="__main__":
    unittest.main()
