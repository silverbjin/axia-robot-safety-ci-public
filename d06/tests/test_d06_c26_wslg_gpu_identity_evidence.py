"""C26: preserve actual WSLg D3D12 GPU identity without confusing GLX
with Gazebo server adapter, and journal-dir existence with core persistence.
Pure L0 regression, ROS/Gazebo/WSLg not executed in CI.
"""
import importlib.util, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
DOCTOR=ROOT/"d06/tools/d06_c23_core_index_readonly_doctor.py"

def load():
    spec=importlib.util.spec_from_file_location("c26_d06_doctor",DOCTOR)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

class C26GpuIdentityEvidence(unittest.TestCase):
    def test_intel_d3d12_is_explicit_and_glx_model_preserved(self):
        m=load()
        raw=("Extended renderer info (GLX_MESA_query_renderer):\n"
             "Device: D3D12 (Intel(R) Iris(R) Xe Graphics) (0xffffffff)\n"
             "OpenGL renderer string: D3D12 (Intel(R) Iris(R) Xe Graphics)\n")
        info=m.summarize_wsl2_layers("6.18-microsoft-standard-wsl2","systemd",
          True,True,raw,True,True)
        self.assertEqual(info["renderer_class"],"D3D12_INTEL")
        self.assertEqual(info["gl_renderer_line"],
          "D3D12 (Intel(R) Iris(R) Xe Graphics)")
        self.assertIn("Intel",info["gl_device_line"])
        self.assertFalse(info["nvidia_glx_confirmed"])
        self.assertFalse(info["gazebo_renderer_proven"])

    def test_nvidia_d3d12_is_not_gazebo_exit_proof(self):
        m=load()
        raw=("Device: D3D12 (NVIDIA GeForce RTX 2060 with Max-Q Design)\n"
             "OpenGL renderer string: D3D12 (NVIDIA GeForce RTX 2060 with Max-Q Design)\n")
        info=m.summarize_wsl2_layers("6.18-microsoft-standard-wsl2","systemd",
          True,True,raw,True,False)
        self.assertEqual(info["renderer_class"],"D3D12_NVIDIA")
        self.assertTrue(info["nvidia_glx_confirmed"])
        self.assertFalse(info["gazebo_renderer_proven"])
        self.assertFalse(info["gazebo_exit0_proven"])

    def test_unknown_d3d12_must_remain_ambiguous_not_intel_guessed(self):
        m=load()
        info=m.summarize_wsl2_layers("6.18-microsoft-standard-wsl2","systemd",
          True,True,"OpenGL renderer string: D3D12 (Adapter Unknown)\n",
          True,False)
        self.assertEqual(info["renderer_class"],"D3D12_OTHER")
        self.assertEqual(info["gl_renderer_line"],"D3D12 (Adapter Unknown)")
        self.assertFalse(info["nvidia_glx_confirmed"])
        self.assertFalse(info["core_capture_proven"])

    def test_persistent_journal_directory_does_not_prove_event_recovery(self):
        m=load()
        info=m.summarize_wsl2_layers("6.18-microsoft-standard-wsl2","systemd",
          True,True,"",True,False)
        self.assertEqual(info["journal_storage_class"],"PERSISTENT_DIR_PRESENT")
        self.assertFalse(info["journal_persistence_proven"])
        self.assertFalse(info["core_capture_proven"])

    def test_active_doctor_exposes_adapter_evidence_without_overrides(self):
        s=DOCTOR.read_text()
        for expected in ("D06_C26_GLX_RENDERER=", "D06_C26_GLX_DEVICE=",
                         "D06_C26_NVIDIA_GLX_CONFIRMED=",
                         "D06_C26_JOURNAL_PERSISTENCE_PROVEN=false",
                         "MESA_D3D12_DEFAULT_ADAPTER_NAME",
                         "nvidia_glx_confirmed",
                         "journal_persistence_proven"):
            self.assertIn(expected,s)
        for forbidden in ("gz sim","ros2 launch","kill -s SEGV",
                          "sysctl -w","apt-get","GALLIUM_DRIVER=",
                          "MESA_D3D12_DEFAULT_ADAPTER_NAME=",
                          "wsl --shutdown"):
            self.assertNotIn(forbidden,s)

if __name__=="__main__":unittest.main()
