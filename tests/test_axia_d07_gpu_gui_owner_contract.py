"""Owner D07 WSLg GPU experiment: no Gazebo on L0, no motion admission."""
from pathlib import Path
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_d07_h01_gpu_gui_owner_wsl2_once.sh"
PRIVATE_SHA="bea66767961416e3b0154447eb2ab38405122cd3"

class OwnerGpuTrialContract(unittest.TestCase):
    def test_bootstrap_l0_executes_without_gazebo(self):
        x=subprocess.run(["bash",str(SCRIPT),"--self-check"],text=True,
                         capture_output=True,timeout=25)
        self.assertEqual(x.returncode,0,x.stderr)
        self.assertIn("AXIA_D07_H01_WATCH_SENTINEL_LIFECYCLE_L0_PASS",x.stdout)
        self.assertIn("AXIA_D07_H01_FAILURE_BUNDLE_L0_PASS",x.stdout)
        self.assertIn("OWNER_WSL2_L3_NOT_RUN",x.stdout)

    def test_gui_gpu_backend_scoped_without_bashrc_global_exports(self):
        s=SCRIPT.read_text()
        self.assertIn("GALLIUM_DRIVER=d3d12",s)
        self.assertIn("unset GALLIUM_DRIVER MESA_D3D12_DEFAULT_ADAPTER_NAME",s)
        self.assertIn("AXIA_D07_GPU_GUI_SERVER_RENDER_ENV_ISOLATED",s)
        self.assertLess(s.index("unset GALLIUM_DRIVER MESA_D3D12_DEFAULT_ADAPTER_NAME"),
                        s.index('bash "$PRIVATE_RUNNER" --run'))
        self.assertNotIn("source ~/.bashrc",s)
        self.assertNotIn("wsl --shutdown",s)

    def test_gpu_trial_failclosed_pre_ros_and_baseline_not_promoted(self):
        s=SCRIPT.read_text()
        self.assertIn(PRIVATE_SHA,s)
        self.assertIn("env -u LIBGL_ALWAYS_SOFTWARE",s)
        self.assertIn('MESA_D3D12_DEFAULT_ADAPTER_NAME=',s)
        self.assertIn("AXIA_D07_GPU_PREFLIGHT_HOLD_NOT_D3D12_ACCELERATED",s)
        self.assertIn("AXIA_D07_H01_GPU_GUI_TRIAL=1",s)
        self.assertIn("AXIA_D07_H01_PRIOR_PUBLIC_L2_IS_SOFTWARE_BASELINE_NOT_GPU_GUI_TRIAL",s)
        self.assertIn("D07_H01_OWNER_GUI_VISUAL_HOLD",s)
        self.assertNotIn("NavigateToPose.Goal()",s)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",s)
        self.assertLess(s.index("AXIA_D07_GPU_PREFLIGHT_HOLD_NOT_D3D12_ACCELERATED"),
                        s.index('bash "$PRIVATE_RUNNER" --run'))
