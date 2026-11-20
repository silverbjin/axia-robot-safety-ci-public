"""C23 read-only investigation of missing synthetic WSL2 core journal record.
Do not generate a second SIGSEGV or start Gazebo to diagnose one.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import os

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/tools/d06_c23_core_index_readonly_doctor.py"

def classify(data):
    with tempfile.TemporaryDirectory() as td:
        file=Path(td)/"fixture.json"
        file.write_text(json.dumps(data),encoding="utf-8")
        return subprocess.run([sys.executable,str(SCRIPT),"--classify-fixture",str(file)],capture_output=True,text=True,timeout=6)

class C23CoreIndexReadOnly(unittest.TestCase):
    def test_self_check_and_ci_blocks_real_probing(self):
        with tempfile.TemporaryDirectory() as td:
            e={**os.environ,"HOME":td,"GITHUB_ACTIONS":"true"}
            p=subprocess.run([sys.executable,str(SCRIPT),"--self-check"],env=e,capture_output=True,text=True,timeout=6)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn("D06_C23_STATIC_L0_PASS_NO_CORE_NO_GAZEBO",p.stdout)
            p=subprocess.run([sys.executable,str(SCRIPT),"--doctor"],env=e,capture_output=True,text=True,timeout=6)
            self.assertEqual(p.returncode,3,(p.stdout,p.stderr))
            self.assertIn("D06_C23_CI_DENIED_READONLY_NO_CRASH",p.stdout)
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_socket_active_no_record_does_not_claim_root_cause(self):
        p=classify({"pid":1424,"socket_active":True,"journal_access":True,"journal_records":[],"info_text":"No coredumps found."})
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("D06_C23_NO_PID_RECORD_CURRENT_BOOT_HOLD_ROOT_CAUSE_UNKNOWN",p.stdout)
        self.assertIn("D06_C23_OFFLINE_FIXTURE_NOT_HARDWARE_PROOF",p.stdout)

    def test_journal_entry_but_coredumpctl_info_unavailable_is_distinct(self):
        p=classify({"pid":1424,"socket_active":True,"journal_access":True,
             "journal_records":[{"COREDUMP_PID":"1424","COREDUMP_SIGNAL":"11","COREDUMP_EXE":"/usr/bin/bash"}],
             "info_text":"No coredumps found."})
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("D06_C23_JOURNAL_RECORD_PRESENT_INFO_MISSING_HOLD",p.stdout)

    def test_info_present_while_legacy_c22_failed_requires_matcher_review(self):
        p=classify({"pid":1424,"socket_active":True,"journal_access":True,"journal_records":[],
              "info_text":"PID: 1424 (bash)\nSignal: 11 (SEGV)\nExecutable: /usr/bin/bash\n"})
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("D06_C23_INFO_PRESENT_C22_MATCHER_OR_TIMING_CANDIDATE_HOLD",p.stdout)

    def test_socket_inactive_and_permission_denied_have_separate_holds(self):
        a=classify({"pid":1424,"socket_active":False,"journal_access":True,"journal_records":[],"info_text":""})
        b=classify({"pid":1424,"socket_active":True,"journal_access":False,"journal_records":[],"info_text":""})
        self.assertIn("D06_C23_SOCKET_NOT_LISTENING_HOLD",a.stdout)
        self.assertIn("D06_C23_JOURNAL_PERMISSION_UNVERIFIED_HOLD",b.stdout)

    def test_scope_is_bounded_and_never_starts_simulation(self):
        s=SCRIPT.read_text(encoding="utf-8")
        for needed in ("COREDUMP_PID=1424","systemd-coredump.socket","journalctl",
            "coredumpctl","--boot","--no-pager",
            "D06_C23_FORENSIC_ARCHIVE=","D06_C23_FORENSIC_SHA256=",
            "CERTIFIED_ESTOP=false","core_not_archived=true"):
            self.assertIn(needed,s)
        for forbidden in ("gz sim","ros2 launch","kill -s SEGV","raise(SIGSEGV)",
            "sysctl -w","apt-get","LD_PRELOAD=","RMW_IMPLEMENTATION=",
            "--nvidia-causal","sudo systemctl start"):
            self.assertNotIn(forbidden,s)

if __name__=="__main__":unittest.main()
