"""C12 regression for field error: L0 passed while coredumpctl absent.

Use only an isolated PATH (all simulated), no ROS/Gazebo/GDB/systemd,
no WSL or hardware access. Check CLI existence, incompatible CLI and
positive toolchain matrix. A positive result is NOT WSLg readiness.
"""
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh"
REQUIRED=("python3","curl","sha256sum","git","bash","gdb","timeout","tar","glxinfo",
          "ps","grep","sed","head","mktemp","chmod","tee","cat","rm","sleep")

def invoke(*, coredumpctl=False, help_text="--json", missing=()):
    with tempfile.TemporaryDirectory() as td:
        tools=pathlib.Path(td)/"bin";tools.mkdir()
        for name in REQUIRED:
            if name not in missing:
                (tools/name).symlink_to("/usr/bin/true")
        if coredumpctl:
            cli=tools/"coredumpctl"
            cli.write_text("#!/bin/sh\nif [ \"$1\" = --help ];then\n"
                           "  echo '"+help_text+"'\n  exit 0\nfi\nexit 0\n")
            cli.chmod(0o755)
        env={"PATH":str(tools),"HOME":str(pathlib.Path(td)/"home"),
             "GITHUB_ACTIONS":"true"}
        result=subprocess.run(["/bin/bash",str(SCRIPT),"--check-tools"],
                              env=env,capture_output=True,text=True,timeout=6)
        assert not (pathlib.Path(td)/"home").exists(), "host state modified"
        return result

class C12FieldDependencyRegression(unittest.TestCase):
    def test_missing_coredumpctl_is_detected_before_ros_or_gazebo(self):
        r=invoke()
        self.assertEqual(r.returncode,3,(r.stdout,r.stderr))
        self.assertIn("D06_WSLG_CORE_ONCE_HOLD_MISSING_TOOL=coredumpctl",r.stdout+r.stderr)
        self.assertIn("D06_WSLG_CORE_ONCE_MISSING_UBUNTU_PACKAGE=systemd-coredump",
                      r.stdout+r.stderr)
        self.assertNotIn("D06_WSLG_CORE_ONCE_SINGLE_NVIDIA_NO_GOAL_FORENSIC_START",r.stdout)

    def test_unsupported_coredumpctl_json_contract_is_blocked(self):
        r=invoke(coredumpctl=True,help_text="list dump")
        self.assertEqual(r.returncode,3)
        self.assertIn("D06_WSLG_CORE_ONCE_HOLD_COREDUMPCTL_JSON_UNSUPPORTED",
                      r.stdout+r.stderr)

    def test_positive_mock_tool_presence_does_not_claim_wslg_acceptance(self):
        r=invoke(coredumpctl=True)
        self.assertEqual(r.returncode,0,(r.stdout,r.stderr))
        self.assertIn("D06_WSLG_CORE_ONCE_TOOLCHAIN_L0_OK_BACKEND_NOT_VERIFIED",r.stdout)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",r.stdout)

    def test_other_required_tool_is_detected_with_same_contract(self):
        r=invoke(coredumpctl=True,missing=("gdb",))
        self.assertEqual(r.returncode,3)
        self.assertIn("D06_WSLG_CORE_ONCE_HOLD_MISSING_TOOL=gdb",r.stdout+r.stderr)

    def test_real_noble_package_manifest_must_not_be_empty(self):
        workflow=(ROOT/".github/workflows/axia-d06-c12-coredump-cli-compat-ubuntu2404.yml").read_text()
        self.assertIn('docker run --rm',workflow)
        self.assertIn('ubuntu:24.04',workflow)
        self.assertIn('target=/workspace,readonly',workflow)
        self.assertIn('apt-get install -y -qq --no-install-recommends',workflow)
        self.assertIn('systemd-coredump gdb mesa-utils',workflow)
        self.assertIn('dpkg-query -W systemd-coredump',workflow)
        self.assertIn('grep -Eq "^systemd-coredump[[:space:]]+[^[:space:]]+"',workflow)
        self.assertIn('dpkg -s systemd-coredump | grep -Fx "Status: install ok installed"',workflow)
        self.assertNotIn('PACKAGE_VERSION=${Version}',workflow)

    def test_static_selfcheck_does_not_claim_runtime_dependency_pass(self):
        r=subprocess.run(["/bin/bash",str(SCRIPT),"--self-check"],
                         capture_output=True,text=True,timeout=6)
        self.assertEqual(r.returncode,0)
        self.assertIn("HOST_DEPENDENCIES_NOT_TESTED",r.stdout)
        src=SCRIPT.read_text()
        self.assertIn("check_required_tools",src)
        self.assertIn("--check-tools",src)
        self.assertIn("D06_GAZEBO_LIVE_RELEASE=HOLD",src)
        self.assertNotIn("apt-get install",src)
        self.assertNotIn("sudo ",src)

if __name__=="__main__":
    unittest.main()
