"""The GPU comparison is precisely one no-goal session per verified adapter."""
import pathlib
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
        self.assertIn("e4c2007064bec2103bb743bd27cdbdf0955961b7",s)
        self.assertIn("d06c0be29ff0ad6cd0c3dc08f86be9ea17287719",s)
        self.assertIn("171aad7ce8abe97c93a42f19787042619c06b65e",s)
        self.assertIn('git hash-object "$TMP/owner.sh"',s)
        self.assertIn('git hash-object "$TMP/compare.py"',s)
        o=OWNER.read_text()
        self.assertIn("e4c2007064bec2103bb743bd27cdbdf0955961b7",o)
        self.assertIn("f7534b191b78cba4f20aac55e9d227268504a25f",o)

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
