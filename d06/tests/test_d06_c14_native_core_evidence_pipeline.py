"""C14: real GDB-generated synthetic SIGSEGV core is fed into the
already shipped --core --exe triage script inside disposable Noble CI.
Static L0 contract first; Linux-native core->GDB->small TAR is a L1
integration, NOT WSLg/Gazebo GPU proof.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/axia-d06-c12-coredump-cli-compat-ubuntu2404.yml"
TRIAGE=ROOT/"d06/scripts/axia_d06_g07_wslg_existing_core_once.sh"
class C14CoreToEvidence(unittest.TestCase):
    def test_ci_generates_real_crash_core_and_runs_actual_triage(self):
        s=WF.read_text()
        self.assertIn('gcc libc6-dev',s)
        self.assertIn('gcc -g -O0 -o /tmp/axia-c14-synthetic-sigsegv',s)
        self.assertIn('raise(SIGSEGV)',s)
        self.assertIn('generate-core-file /tmp/axia-c14-synthetic.core',s)
        self.assertIn('test -s /tmp/axia-c14-synthetic.core',s)
        self.assertIn('bash /workspace/d06/scripts/axia_d06_g07_wslg_existing_core_once.sh',s)
        self.assertIn('--core /tmp/axia-c14-synthetic.core --exe /tmp/axia-c14-synthetic-sigsegv',s)
        self.assertIn('D06_WSLG_CORE_TRIAGE_STACK=CAPTURED',s)
        self.assertIn('D06_C14_REAL_GDB_SIGSEGV_CORE_AND_TEXT_TAR_GREEN',s)

    def test_actual_archive_checksum_and_no_core_memory(self):
        s=WF.read_text()
        self.assertIn('sha256sum -c',s)
        self.assertIn('tar -tzf',s)
        self.assertIn('tar -xOzf',s)
        self.assertIn('gdb_backtrace.log',s)
        self.assertIn('core_not_archived=true',s)
        self.assertIn('D06_C14_NOT_WSLG_GPU_NOT_REAL_GAZEBO_SERVER_CORE',s)
        self.assertNotIn('sudo sysctl -w kernel.core_pattern',s)

    def test_triage_remains_existing_core_only_with_fail_closed_result(self):
        s=TRIAGE.read_text()
        self.assertIn('EXISTING_CORE_ONLY NO_GAZEBO_RUN',s)
        self.assertIn('D06_WSLG_CORE_TRIAGE_STACK=CAPTURED',s)
        self.assertIn('D06_GAZEBO_SIGSEGV_ROOT_CAUSE=UNCONFIRMED',s)
        self.assertIn('core_not_archived=true',s)
        self.assertIn('timeout 45s gdb',s)
        self.assertNotIn('gz sim',s)
        self.assertNotIn('apt-get install',s)

if __name__=='__main__':unittest.main()
