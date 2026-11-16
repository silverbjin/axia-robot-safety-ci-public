"""TDD: WSL2 Gazebo/RViz resources, no Goal/no mutation, L0 fixtures only."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/axia_wsl2_gui_resource_monitor.py"

def load():
    spec=importlib.util.spec_from_file_location("axia_wsl2_gui_resource_monitor",SCRIPT)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module

class WSL2ResourceMonitorContract(unittest.TestCase):
    def test_meminfo_reports_wsl_vm_not_full_windows_ram(self):
        m=load()
        info=m.parse_meminfo("MemTotal: 16384000 kB\nMemAvailable: 8192000 kB\nSwapTotal: 4194304 kB\n")
        self.assertAlmostEqual(info["ram_total_gib"],15.625,places=3)
        self.assertAlmostEqual(info["ram_available_gib"],7.8125,places=3)
        self.assertAlmostEqual(info["swap_total_gib"],4.0,places=3)
        self.assertNotIn("windows_total_gib",info)

    def test_process_roles_and_partitions_mismatch_are_not_gui_pass(self):
        m=load()
        self.assertEqual(m.classify_process(["/usr/bin/gz","sim","-g"]),"gazebo_gui")
        self.assertEqual(m.classify_process(["/usr/bin/gz","sim","-s","world.sdf"]),"gazebo_server")
        self.assertEqual(m.classify_process(["/usr/libexec/gz-sim8/gz-sim-server"]),"gazebo_server")
        self.assertEqual(m.classify_process(["/opt/ros/jazzy/lib/rviz2/rviz2"]),"rviz2")
        processes=[{"role":"gazebo_server","gz_partition":"axia_a"},{"role":"gazebo_gui","gz_partition":"axia_b"}]
        x=m.assess_gz_partitions(processes)
        self.assertEqual(x["status"],"MISMATCH")
        self.assertFalse(x["gui_connection_verified"])
        self.assertEqual(m.assess_gz_partitions([])["status"],"NO_SERVER_OR_GUI_PROCESS")

    def test_real_owner_ruby_gz_wrappers_do_not_disappear_from_monitor(self):
        # Owner cNAPf8A0 genuine ps captured Gazebo-server PID 4581 and
        # GUI PID 5767 as 'ruby' processes, not 'gz-sim-server' binaries.
        # This models /proc/PID/cmdline's Ruby launcher arguments; exact
        # historical argv was NOT preserved in the evidence bundle.
        m=load()
        simulated=[
            (["/usr/bin/ruby","/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz",
              "sim","-s","world.sdf"],"gazebo_server"),
            (["/usr/bin/ruby","/usr/bin/gz","sim","-g"],"gazebo_gui"),
            (["/usr/bin/ruby","/usr/bin/gz","sim","-r","-s","world.sdf"],
             "gazebo_server"),
            (["/usr/bin/ruby","/tmp/unrelated-task.rb"],None),
        ]
        for argv,role in simulated:
            with self.subTest(argv=argv):
                self.assertEqual(m.classify_process(argv),role)
        processes=[{"role":m.classify_process(argv),
                    "gz_partition":"axia_owner_sim_95"} for argv,role
                   in simulated[:2]]
        diagnosis=m.assess_gz_partitions(processes)
        self.assertEqual(diagnosis["status"],"MATCH_NOT_CONNECTION_PROOF")
        self.assertEqual(diagnosis["servers"],1)
        self.assertEqual(diagnosis["guis"],1)
        self.assertFalse(diagnosis["gui_connection_verified"])

    def test_missing_gpu_tool_does_not_equal_zero_gpu(self):
        m=load()
        self.assertEqual(m.assess_renderer("OpenGL renderer string: llvmpipe (LLVM 17)",True)["status"],"SOFTWARE_RENDERER")
        self.assertEqual(m.assess_renderer("OpenGL renderer string: D3D12 (NVIDIA)",False)["status"],"WSLG_D3D12_RENDERER")
        self.assertEqual(m.assess_renderer("",False)["status"],"RENDERER_UNKNOWN")
        self.assertFalse(m.assess_renderer("",False)["gpu_utilization_proven"])

    def test_cpu_percentage_no_division_zero(self):
        m=load()
        self.assertIsNone(m.cpu_percent((10,100),(10,100)))
        self.assertAlmostEqual(m.cpu_percent((10,100),(30,200)),20.0)

    def test_self_check_and_one_short_live_host_sample_emit_no_acceptance(self):
        self.assertTrue(SCRIPT.is_file())
        p=subprocess.run([sys.executable,str(SCRIPT),"--self-check"],
                         capture_output=True,text=True,timeout=15)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("AXIA_WSL2_MONITOR_L0_PASS_NO_ROS_NO_GUI",p.stdout)
        with tempfile.TemporaryDirectory() as tmp:
            r=subprocess.run([sys.executable,str(SCRIPT),"--duration","1",
                   "--interval","0.5","--outdir",tmp,"--no-external"],
                   capture_output=True,text=True,timeout=15)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn("AXIA_WSL2_RESOURCE_MONITOR_BUNDLE=",r.stdout)
            bundles=list(Path(tmp).glob("*.tar.gz"))
            self.assertEqual(len(bundles),1)
            self.assertTrue(Path(str(bundles[0])+".sha256").is_file())
            records=list(Path(tmp).rglob("summary.json"))
            self.assertEqual(len(records),1)
            summary=json.loads(records[0].read_text())
            self.assertEqual(summary["validation_level"],"HOST_METRICS_ONLY")
            self.assertFalse(summary["gazebo_gui_render_pass"])
            self.assertFalse(summary["safety_accepted"])
            self.assertGreaterEqual(summary["sample_count"],1)

if __name__=="__main__":
    unittest.main()
