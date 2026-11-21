"""C17: pure offline G3 bundle classifier. Synthetic fixtures are never real WSLg proof."""
import hashlib, io, os, subprocess, tarfile, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "d06/scripts/axia_d06_g3_independent_wslg_nogoal_once.sh"

class C17G3Proof(unittest.TestCase):
    def make_bundle(self, folder, summary, owner, stack=""):
        archive = Path(folder) / "trace-fixture.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for name, value in (("summary.txt",summary),("owner_tail.log",owner),
                                ("gdb_backtrace.log",stack)):
                payload=value.encode()
                meta=tarfile.TarInfo(name)
                meta.size=len(payload)
                tar.addfile(meta,io.BytesIO(payload))
        (Path(str(archive)+".sha256")).write_text(
            hashlib.sha256(archive.read_bytes()).hexdigest()+"  "+str(archive)+"\n")
        return archive

    def check(self, summary, owner, stack=""):
        with tempfile.TemporaryDirectory() as td:
            archive=self.make_bundle(td,summary,owner,stack)
            return subprocess.run(["bash",str(SCRIPT),"--classify-bundle",str(archive)],
                                  capture_output=True,text=True,timeout=12)

    def test_clean_scoped_bundle_not_hardware_pass(self):
        r=self.check("D06_WSLG_CORE_ONCE_SINGLE_NVIDIA_NO_GOAL_FORENSIC_START\nowner_rc=0\n",
          "D06_OWNER_NO_GOAL_NATIVE_COMPLETE_CANDIDATE SCAN300_DUAL_20S_PASS NAV2_ACK_PASS CM_CHILD_EXIT0 GZ_CHILD_EXIT0\n"
          "D06_GPU_RTF_NVIDIA_ONLY_FIRST_BLOCK=NONE\n")
        self.assertEqual(r.returncode,0,(r.stdout,r.stderr))
        self.assertIn("D06_G3_OFFLINE_BUNDLE_CLEAN_CONTRACT_HARDWARE_NOT_PROVEN",r.stdout)
        self.assertNotIn("D06_G3_NATIVE_NO_GOAL_CLEAN_CANDIDATE_NOT_MOVING_L3",r.stdout)
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",r.stdout)

    def test_first_server_stack_stays_hold(self):
        r=self.check("D06_WSLG_CORE_ONCE_EXISTING_GZ_SIGSEGV_PID=999 NO_REPLAY\n"
          "D06_WSLG_CORE_STACK_CAPTURED_NOT_RESOLVED\nowner_rc=NOT_RUN\n","",
          "Program terminated with signal SIGSEGV\n#0 0xabcdef in gzServer\n")
        self.assertEqual(r.returncode,3)
        self.assertIn("D06_G3_FIRST_SERVER_SIGSEGV_STACK_CAPTURED_HOLD",r.stdout)

    def test_owner_rc_zero_without_native_evidence_is_hold(self):
        r=self.check("D06_WSLG_CORE_ONCE_SINGLE_NVIDIA_NO_GOAL_FORENSIC_START\nowner_rc=0\n",
                     "D06_GPU_RTF_NVIDIA_ONLY_FIRST_BLOCK=NONE\n")
        self.assertEqual(r.returncode,3)
        self.assertIn("D06_G3_NO_GOAL_NATIVE_PROOF_MISSING_HOLD",r.stdout)

    def test_invalid_sidecar_sha_holds(self):
        with tempfile.TemporaryDirectory() as td:
            archive=self.make_bundle(td,"owner_rc=0\n","")
            Path(str(archive)+".sha256").write_text("0"*64+"  "+str(archive)+"\n")
            r=subprocess.run(["bash",str(SCRIPT),"--classify-bundle",str(archive)],
                             capture_output=True,text=True,timeout=12)
            self.assertEqual(r.returncode,3)
            self.assertIn("D06_G3_ARCHIVE_SHA256_MISMATCH_HOLD",r.stdout+r.stderr)

    def test_guardrails_syntax_and_self_check(self):
        s=SCRIPT.read_text()
        for required in ("G3_HOST_CANDIDATE_NOT_ACCEPTED","AXIA_G3_ISOLATED_HOST_ACK",
                         "d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh",
                         "git hash-object","sha256sum -c","--run-once",
                         "D06_G3_NATIVE_NO_GOAL_CLEAN_CANDIDATE_NOT_MOVING_L3",
                         "AXIA_MVP_DEMO_ACCEPTED=HOLD"):
            self.assertIn(required,s)
        for forbidden in ("sudo ","apt-get install","pkill ","LD_PRELOAD=",
                          "RMW_IMPLEMENTATION=","send_goal","set_pose"):
            self.assertNotIn(forbidden,s)
        self.assertEqual(subprocess.run(["bash","-n",str(SCRIPT)]).returncode,0)
        rejected=subprocess.run(["bash",str(SCRIPT),"--run-once"],
                                capture_output=True,text=True,timeout=6)
        self.assertEqual(rejected.returncode,3)
        self.assertIn("D06_G3_ISOLATED_HOST_ATTESTATION_MISSING_NO_GAZEBO",
                      rejected.stderr)
        with tempfile.TemporaryDirectory() as td:
            env=os.environ.copy(); env["HOME"]=td
            r=subprocess.run(["bash",str(SCRIPT),"--self-check"],env=env,
                             capture_output=True,text=True,timeout=7)
            self.assertEqual(r.returncode,0)
            self.assertIn("NO_ROS_NO_GAZEBO_NO_GOAL",r.stdout)
            self.assertEqual(list(Path(td).iterdir()),[])

if __name__=="__main__": unittest.main()
