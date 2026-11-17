"""Owner D07 WSLg GPU experiment: no Gazebo on L0, no motion admission."""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_d07_h01_gpu_gui_owner_wsl2_once.sh"
PRIVATE_SHA="7306b27bc1d146d99d1657308549db45c9878407"

class OwnerGpuTrialContract(unittest.TestCase):
    def test_owner_pins_real_shared_l2_and_does_not_enable_ci_xvfb(self):
        source=SCRIPT.read_text()
        self.assertIn("7306b27bc1d146d99d1657308549db45c9878407",source)
        self.assertIn("43997663084",source)
        self.assertIn("CI_SAME_SHA_GAZEBO_XVFB_L2",source)
        self.assertIn("WSLG_D3D12_GUI_NOT_VERIFIED",source)
        self.assertIn("unset AXIA_D07_H01_CI_SOFTWARE_GUI",source)
        self.assertNotIn("AXIA_D07_H01_PRIOR_PUBLIC_L2_IS_SOFTWARE_BASELINE_NOT_GPU_GUI_TRIAL",source)

    def test_owner_scene_runtime_contract_precedes_visual_hold(self):
        script=SCRIPT.read_text()
        self.assertIn("D07_H01_SCENE_BROADCASTER_SOURCE_OR_RUNTIME_NOT_PROVEN",script)
        self.assertIn("scene_world_source_verified",script)
        self.assertIn("scene_transport_observed",script)
        self.assertIn("d07_gui_scene_world_manifest.json",script)
        self.assertIn("d07_gui_transport_topics.txt",script)
        self.assertIn("gazebo_3d_scene_render_proven':False",script)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",script)

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

    def test_real_first_gui_failure_survives_missing_phase_evidence(self):
        # Owner mVW: empty watcher log + absent GUI stage files. A later
        # FileNotFoundError is NEVER the first failure if GUI failed first.
        code=SCRIPT.read_text()
        start=code.rfind("<<'PY'\n")+len("<<'PY'\n")
        end=code.index("\nPY\nVERDICT_RC=",start)
        self.assertIn("owner_first_gui_boundary.txt",code)
        private_tools=ROOT.parent/"instructor"/"tools"
        self.assertTrue(private_tools.is_dir(),"sealed private test utilities missing")
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            first="D07_H01_GUI_WATCHER_SPAWN_ACK_ABSENT"
            (p/"owner_first_gui_boundary.txt").write_text(first+"\n")
            result=subprocess.run(["python3","-",str(private_tools),str(p),
                 PRIVATE_SHA,"2","43997663084"],input=code[start:end],
                 text=True,capture_output=True,timeout=12)
            verdict=json.loads((p/"owner_l3_verdict.json").read_text())
            self.assertEqual(result.returncode,3,result.stderr)
            self.assertEqual(verdict["first_missing_visual_boundary"],first)
            self.assertEqual(verdict["reason"],first)
            self.assertFalse(verdict["owner_wsl2_gui_l3_accepted"])

    def test_first_native_localization_failure_outweighs_watcher(self):
        # Owner gx74: watcher was never launched because LOCALIZATION_START
        # had already failed. Never mislabel the first failure.
        code=SCRIPT.read_text()
        start=code.rfind("<<'PY'\n")+len("<<'PY'\n")
        end=code.index("\nPY\nVERDICT_RC=",start)
        private_tools=ROOT.parent/"instructor"/"tools"
        self.assertTrue(private_tools.is_dir())
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            gate="LOCALIZATION_START: G07_NATIVE_LIFECYCLE_STARTUP_SERVICE_TIMEOUT:request_sent=True"
            (p/"owner_first_staged_boundary.txt").write_text(gate+"\n")
            (p/"owner_first_gui_boundary.txt").write_text(
                "D07_H01_GUI_WATCHER_SPAWN_ACK_ABSENT\n")
            result=subprocess.run(["python3","-",str(private_tools),str(p),
                PRIVATE_SHA,"2","43997663084"],input=code[start:end],
                text=True,capture_output=True,timeout=12)
            verdict=json.loads((p/"owner_l3_verdict.json").read_text())
            self.assertEqual(result.returncode,3,result.stderr)
            self.assertEqual(verdict["reason"],gate)
            self.assertEqual(verdict["first_staged_boundary"],gate)
            self.assertEqual(verdict["first_missing_visual_boundary"],gate)
            self.assertFalse(verdict["owner_wsl2_gui_l3_accepted"])

    def test_gpu_trial_failclosed_pre_ros_and_baseline_not_promoted(self):
        s=SCRIPT.read_text()
        self.assertIn(PRIVATE_SHA,s)
        self.assertIn("env -u LIBGL_ALWAYS_SOFTWARE",s)
        self.assertIn('MESA_D3D12_DEFAULT_ADAPTER_NAME=',s)
        self.assertIn("AXIA_D07_GPU_PREFLIGHT_HOLD_NOT_D3D12_ACCELERATED",s)
        self.assertIn("AXIA_D07_H01_GPU_GUI_TRIAL=1",s)
        self.assertIn("AXIA_D07_H01_CI_SAME_SHA_GAZEBO_XVFB_L2_PASS_WSLG_D3D12_GUI_NOT_VERIFIED",s)
        self.assertIn("D07_H01_OWNER_GUI_VISUAL_HOLD",s)
        self.assertNotIn("NavigateToPose.Goal()",s)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",s)
        self.assertLess(s.index("AXIA_D07_GPU_PREFLIGHT_HOLD_NOT_D3D12_ACCELERATED"),
                        s.index('bash "$PRIVATE_RUNNER" --run'))

    def test_owner_zokaxnwf_gazebo_software_and_first_sigsegv_precedes_watcher_entered(self):
        # Real Owner zoKAxNwF: watcher entered, then gz GUI SIGSEGV 139,
        # later no RViz subscriber and blocked teardown. Startup marker
        # MUST NOT be reported as the first fault.
        s=SCRIPT.read_text()
        self.assertIn("export AXIA_D07_H01_OWNER_GZ_SOFTWARE_ONLY=1",s)
        self.assertIn("D07_H01_OWNER_GZ_SOFTWARE_ONLY=1",s)
        self.assertIn("D07_H01_GUI_FIRST_NATIVE_GZ_RENDER_SIGSEGV_139",s)
        self.assertIn("'^D07_H01_GUI_FIRST_NATIVE_GZ_RENDER_SIGSEGV_139'",s)
        self.assertIn("D07_H01_GUI_CHILD_TERMINATED_BEFORE_PHASE_COMPLETE",s)
        self.assertNotIn("grep -m1 -E 'D07_H01_GUI_(CHILD_TERMINATED|WATCHER_",s)
        self.assertLess(s.index("D07_H01_GUI_FIRST_NATIVE_GZ_RENDER_SIGSEGV_139"),
                        s.index("D07_H01_GUI_CHILD_TERMINATED_BEFORE_PHASE_COMPLETE"))
        self.assertLess(s.index("export AXIA_D07_H01_OWNER_GZ_SOFTWARE_ONLY=1"),
                        s.index('bash "$PRIVATE_RUNNER" --run'))


    def test_owner_s75_finished_gui_rc0_never_first_error_and_fault_injector_audit_visible(self):
        # Owner S75hTDrR: before/intrusion/restored 52/52/52 PASS,
        # watcher RViz SIGINT exits 0, subsequent launch budget misses
        # fault injector. This must NOT blame the successful GUI close.
        s=SCRIPT.read_text()
        self.assertIn("D07_H01_CHILD_SHUTDOWN_BLOCKED",s)
        self.assertIn("owner_first_teardown_boundary.txt",s)
        self.assertIn("WATCHER_EXIT rc=[1-9]",s)
        self.assertNotIn("WATCHER_EXIT rc=)'",s)
        code=s[s.rfind("<<'PY'\n")+len("<<'PY'\n"):s.index("\nPY\nVERDICT_RC=",s.rfind("<<'PY'\n"))]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            tool=p/"tool"
            tool.mkdir()
            (tool/"d07_h01_path_visual.py").write_text(
                "def assess_gui_stages(*a,**k): return {'ready':False}\n")
            evidence=p/"real-l2"
            evidence.mkdir()
            (p/"owner_first_teardown_boundary.txt").write_text(
                "D07_H01_CHILD_SHUTDOWN_BLOCKED:fault_injector_node\n")
            result=subprocess.run(
                ["python3","-",str(tool),str(p),PRIVATE_SHA,"3","43997663084"],
                input=code,text=True,capture_output=True,timeout=12)
            self.assertEqual(result.returncode,3,result.stderr)
            v=json.loads((p/"owner_l3_verdict.json").read_text())
            self.assertEqual(v["reason"],"D07_H01_CHILD_SHUTDOWN_BLOCKED:fault_injector_node")
            self.assertIsNone(v["first_gui_boundary"])
            self.assertFalse(v["owner_wsl2_gui_l3_accepted"])
