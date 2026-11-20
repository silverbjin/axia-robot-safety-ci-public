"""C13 release-readiness contract: test the actual shipped owner core launcher
on a REAL clean Noble image with dependencies installed. A package-only
coredumpctl smoke check does not verify every program in its bash preflight.

L0 static RED -> L1 container actual binary execution GREEN -> report HOLD
for WSLg backend and Gazebo timing until those are separately verified.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/axia-d06-c12-coredump-cli-compat-ubuntu2404.yml"
SRC=ROOT/"d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh"
class C13PackagedCliReadiness(unittest.TestCase):
    def test_real_container_invokes_exact_shipped_owner_script(self):
        s=WF.read_text()
        self.assertIn('actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683',s)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',s)
        self.assertIn('test -r "$GITHUB_WORKSPACE/d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh"',s)
        self.assertLess(s.index('actions/checkout@'),s.index('docker run --rm'))
        self.assertIn('type=bind,source=$GITHUB_WORKSPACE,target=/workspace,readonly',s)
        self.assertIn('bash -n /workspace/d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh',s)
        self.assertIn('bash /workspace/d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh --check-tools',s)
        self.assertIn('D06_WSLG_CORE_ONCE_TOOLCHAIN_L0_OK_BACKEND_NOT_VERIFIED',s)
        self.assertIn('D06_C13_ACTUAL_NOBLE_PINNED_LAUNCHER_CLI_GREEN',s)
        self.assertIn('bash /workspace/d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh --self-check',s)
        self.assertIn('HOST_DEPENDENCIES_NOT_TESTED',s)
        self.assertNotIn('bash /workspace/d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh --run-once',s)

    def test_install_all_release_required_cli_without_host_changes(self):
        s=WF.read_text()
        for pkg in ('systemd-coredump','gdb','mesa-utils','curl','git',
                    'python3','procps','coreutils','grep','sed','tar'):
            self.assertIn(pkg,s)
        self.assertIn('docker run --rm',s)
        self.assertIn('ubuntu:24.04',s)
        self.assertIn('readonly',s)
        self.assertIn('D06_C13_NOT_WSLG_GPU_NOT_REAL_CORE_NOT_GAZEBO',s)
        self.assertNotIn('sudo apt-get install',s)
        self.assertNotIn('Acquire::AllowInsecureRepositories',s)

    def test_current_launcher_check_tools_is_shared_with_real_run(self):
        s=SRC.read_text()
        self.assertIn('check_required_tools()',s)
        self.assertIn('if [[ "$MODE" == --check-tools ]];then',s)
        self.assertIn('check_required_tools\n',s)
        self.assertIn('D06_WSLG_CORE_ONCE_MISSING_UBUNTU_PACKAGE=systemd-coredump',s)
        self.assertNotIn('apt-get install',s)

if __name__=='__main__':
    unittest.main()
