"""C24 WSL2/WSLg-specific cause boundaries for C23 core index diagnosis.
All CI tests are pure/offline; never trigger SIGSEGV, Gazebo or ROS.
"""
import importlib.util
from pathlib import Path
import subprocess,sys,tempfile,json,unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"d06/tools/d06_c23_core_index_readonly_doctor.py"

def module():
    spec=importlib.util.spec_from_file_location("c23_wsl2",SRC)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

class C24Wsl2NativeParity(unittest.TestCase):
    def test_wsl2_previous_run_boot_unknown_must_not_be_storage_failure(self):
        m=module()
        s={"pid":1424,"socket_active":False,"journal_access":True,
           "journal_records":[],"info_text":"","event_boot_known":False,
           "wsl2_kernel":True}
        self.assertEqual(m.classify(s),"D06_C24_WSL2_PREVIOUS_EVENT_BOOT_UNVERIFIED_HOLD")

    def test_wsl2_live_systemd_journal_context_is_distinct_from_wslg_graphics(self):
        m=module()
        c=m.summarize_wsl2_layers("5.15.167.4-microsoft-standard-WSL2",
             "systemd",True,True,
             "OpenGL renderer string: D3D12 (NVIDIA GeForce RTX 2060 with Max-Q Design)\n",
             True,False)
        self.assertEqual(c["environment"],"WSL2_UBUNTU2404")
        self.assertEqual(c["renderer_class"],"D3D12_NVIDIA")
        self.assertTrue(c["dxg_present"])
        self.assertTrue(c["wslg_visible"])
        self.assertEqual(c["journal_storage_class"],"PERSISTENT_DIR_PRESENT")
        self.assertFalse(c["core_capture_proven"])
        self.assertFalse(c["gazebo_exit0_proven"])

    def test_software_renderer_is_not_promoted_to_nvidia_d3d12(self):
        m=module()
        c=m.summarize_wsl2_layers("5.15.153.1-microsoft-standard-WSL2",
             "systemd",False,False,
             "OpenGL renderer string: llvmpipe (LLVM 15.0.7)\n",
             False,True)
        self.assertEqual(c["renderer_class"],"SOFTWARE_LLVMPIPE")
        self.assertEqual(c["journal_storage_class"],"VOLATILE_DIR_ONLY")
        self.assertFalse(c["core_capture_proven"])

    def test_wsl2_doctor_does_not_assume_native_linux_or_start_crash(self):
        s=SRC.read_text()
        for required in ("summarize_wsl2_layers","/dev/dxg","/mnt/wslg",
           "glxinfo","/run/log/journal","/var/log/journal",
           "event_boot_known", "D06_C24_WSL2_PREVIOUS_EVENT_BOOT_UNVERIFIED_HOLD",
           "D06_C24_WSL2_LAYER_DIAGNOSTIC_ONLY_NOT_GAZEBO_ACCEPTANCE"):
            self.assertIn(required,s)
        for forbidden in ("gz sim","ros2 launch","kill -s SEGV","raise(SIGSEGV)",
                          "sysctl -w","apt-get","wsl --shutdown",
                          "MESA_D3D12_DEFAULT_ADAPTER_NAME="):
            self.assertNotIn(forbidden,s)

if __name__=="__main__":unittest.main()
