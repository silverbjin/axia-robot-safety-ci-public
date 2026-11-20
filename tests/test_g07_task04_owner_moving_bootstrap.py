"""Task04 Owner immutable one-shot bootstrap L0; never sends a ROS Goal."""
from pathlib import Path
import subprocess
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/axia_g07_task04_owner_moving_l3_once.sh"
SHA="5c7983598fa3bcd7148433a06f37a4e78b091273"
RUN=44652361407
REVIEW_SHA='362da68e31dd163a8d321601e191069c0d0a438b'

class OwnerMovingBootstrap(unittest.TestCase):
    def test_static_self_check_instant_no_ros(self):
        r=subprocess.run(["bash",str(SCRIPT),"--self-check"],
                         text=True,capture_output=True,timeout=8)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("AXIA_G07_TASK04_OWNER_MOVING_BOOTSTRAP_L0_PASS",r.stdout)
        self.assertIn(SHA,r.stdout)
        self.assertIn(f"l2_run={RUN}",r.stdout)
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",r.stdout)

    def test_owner_run_never_uses_ci_goal_permissions_or_global_kill(self):
        s=SCRIPT.read_text()
        self.assertIn("AXIA_G07_TASK04_OWNER_MOVING_L3=1",s)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED=0",s)
        self.assertIn("AXIA_P2_G07_RELOCATED_OBSTACLE=1",s)
        self.assertIn("AXIA_G07_CI_OWNER_BAG_PARITY=1",s)
        self.assertIn("AXIA_NAV2_USE_COMPOSITION=False",s)
        self.assertNotIn("GITHUB_ACTIONS=true",s)
        self.assertNotIn("pkill -f",s)
        self.assertNotIn("killall",s)
        self.assertNotIn("wsl --shutdown",s)

    def test_foreground_timeout_cannot_background_manual_tty_reader(self):
        # GNU timeout without --foreground creates a different process group.
        # The Owner's actual /dev/tty consent must NOT be sent SIGTTIN.
        s=SCRIPT.read_text()
        self.assertIn("timeout --foreground --signal=TERM",s)
        self.assertIn("OWNER_CONTROLLING_TTY_REQUIRED",s)
        self.assertNotIn("setsid timeout",s)

    def test_wslg_gpu_env_is_only_assigned_to_verified_gui_children(self):
        s=SCRIPT.read_text()
        self.assertIn('AXIA_G07_TASK04_GUI_D3D12_ADAPTER',s)
        self.assertIn('export LIBGL_ALWAYS_SOFTWARE=1',s)
        self.assertIn('unset GALLIUM_DRIVER MESA_D3D12_DEFAULT_ADAPTER_NAME',s)
        self.assertNotIn('export GALLIUM_DRIVER=d3d12',s)
        self.assertIn('MESA_D3D12_DEFAULT_ADAPTER_NAME="$adapter"',s)

    def test_pinned_source_and_private_evidence_archive(self):
        s=SCRIPT.read_text()
        self.assertIn(SHA,s)
        self.assertIn(str(RUN),s)
        self.assertIn(REVIEW_SHA,s)
        self.assertIn("p2_g07_task04_moving_review.py",s)
        self.assertIn("AXIA_G07_TASK04_ARCHIVE=",s)
        self.assertIn("AXIA_G07_TASK04_SHA256=",s)
        self.assertIn("task04_owner_verdict.json",s)
        self.assertIn("SHA256SUMS",s)
        self.assertIn("CORE_PARITY_PASS",s)

    def test_small_separate_diagnostic_zip_without_raw_bag(self):
        s=SCRIPT.read_text()
        self.assertIn("AXIA_G07_TASK04_DIAGNOSTIC_ZIP=",s)
        self.assertIn("zipfile.ZipFile",s)
        self.assertIn("pregoal_baseline.json",s)
        self.assertIn("SHA256SUMS",s)
        self.assertIn("diagnostics.zip",s)

    def test_owner_preserves_first_pregoal_failure_not_outer_generic_wrapper(self):
        s=SCRIPT.read_text()
        self.assertIn('native/g07_ci_pregoal/pregoal_baseline.json',s)
        self.assertIn('ORIGINAL_FIRST_FAILURE',s)
        self.assertIn('FIRST_FAILURE="$ORIGINAL_FIRST_FAILURE"',s)
        self.assertIn('hold "$FIRST_FAILURE"',s)

    def test_mvp_visual_fallback_remains_explicitly_formal_hold(self):
        s=SCRIPT.read_text()
        self.assertIn("axia_g07_mvp_visual_verdict.py",s)
        self.assertIn("MVP_OWNER_NUMERICAL_CANDIDATE_FORMAL_SHUTDOWN_HOLD",s)
        self.assertIn("FORMAL_LOCALIZATION_SHUTDOWN_TIMEOUT_AFTER_DEMO",s)
        self.assertIn('"owner_moving_l3_accepted":False',s)
        self.assertIn('"axia_mvp_demo_accepted":False',s)
        self.assertIn('"certified_estop":False',s)

    def test_bad_argument_fails_without_any_goal(self):
        r=subprocess.run(["bash",str(SCRIPT),"--bad-mode"],
                         text=True,capture_output=True,timeout=8)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("BAD_ARGUMENTS",r.stderr+r.stdout)

if __name__=="__main__":
    unittest.main()
