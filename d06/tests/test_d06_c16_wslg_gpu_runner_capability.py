"""C16 G3 runner admission: NEVER promote hosted Linux Xvfb, Intel D3D12,
generic NVIDIA CUDA, or absent core backend as an equivalent WSLg GPU.
Public L0 tests synthetic capability facts only, never a real GPU.
"""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"d06/tools/d06_g3_wslg_gpu_capability.py"
WF=ROOT/".github/workflows/axia-d06-g07-wslg-lidar-rtf-isolation-l0-20261118.yml"
def load():
    spec=importlib.util.spec_from_file_location("axia_g3_capability",SRC)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
def ideal():
    return dict(kernel="6.6.87.2-microsoft-standard-WSL2",
                os_id="ubuntu",os_version="24.04",display=":0",wayland="wayland-0",
                glxinfo="OpenGL renderer string: D3D12 (NVIDIA GeForce RTX 2060 with Max-Q Design)",
                nvidia="NVIDIA GeForce RTX 2060 with Max-Q Design",
                binaries={"glxinfo":True,"nvidia-smi":True,"gdb":True,
                          "coredumpctl":True,"gz":True,"ros2":True},
                jazzy_overlay=True,
                core_pattern="|/usr/lib/systemd/systemd-coredump %P %u %g %s %t %c %h")
class G3CapabilityReadOnly(unittest.TestCase):
    def test_matched_gpu_only_candidate_never_l3_pass(self):
        q=load().assess(ideal())
        self.assertEqual(q["decision"],"G3_HOST_CANDIDATE_NOT_ACCEPTED")
        self.assertEqual(q["issues"],[])
        self.assertFalse(q["gazebo_l2_executed"])
        self.assertFalse(q["wslg_sigsegv_resolved"])
    def test_standard_linux_xvfb_is_not_wslg(self):
        d=ideal()
        d.update(kernel="6.8.0-aws",display=":99",wayland="",
                 glxinfo="OpenGL renderer string: llvmpipe (LLVM 17.0.6)")
        r=load().assess(d)
        self.assertEqual(r["decision"],"G3_CAPABILITY_HOLD")
        self.assertIn("NOT_WSL2_KERNEL",r["issues"])
        self.assertIn("D3D12_NVIDIA_RENDERER_NOT_PROVEN",r["issues"])
    def test_wslg_intel_renderer_with_nvidia_cuda_is_rejected(self):
        d=ideal();d["glxinfo"]="OpenGL renderer string: D3D12 (Intel Iris Xe Graphics)"
        self.assertIn("D3D12_NVIDIA_RENDERER_NOT_PROVEN",
                      load().assess(d)["issues"])
    def test_gpu_model_drift_or_missing_core_handler_hold(self):
        d=ideal();d["nvidia"]="NVIDIA Tesla T4"
        self.assertIn("RTX2060_REFERENCE_GPU_NOT_MATCHED",
                      load().assess(d)["issues"])
        d=ideal();d["core_pattern"]="core"
        self.assertIn("CORE_SYSTEMD_HANDLER_NOT_CONFIGURED",
                      load().assess(d)["issues"])
    def test_missing_jazzy_and_coredumpctl_hold(self):
        d=ideal();d["jazzy_overlay"]=False;d["binaries"]["coredumpctl"]=False
        res=load().assess(d)
        self.assertIn("ROS_JAZZY_NOT_PRESENT",res["issues"])
        self.assertIn("MISSING_TOOL_coredumpctl",res["issues"])
    def test_public_repo_remains_hosted_only(self):
        s=WF.read_text()
        self.assertIn("test_d06_c16_wslg_gpu_runner_capability.py",s)
        self.assertNotIn("runs-on: self-hosted",s)
        self.assertNotIn("pull_request_target:",s)
        c=SRC.read_text()
        self.assertIn("G3_HOST_CANDIDATE_NOT_ACCEPTED",c)
        self.assertIn("G3_CAPABILITY_HOLD",c)
        self.assertNotIn("sudo ",c)
        self.assertNotIn("apt-get install",c)
        self.assertNotIn("send_goal",c)
if __name__=="__main__":unittest.main()
