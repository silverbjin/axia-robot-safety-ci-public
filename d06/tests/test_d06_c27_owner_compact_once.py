"""C27 field delivery: compact only strict NO_GOAL evidence, no replay.
Contract and a synthetic archive are used. No ROS/Gazebo in L0.
"""
from pathlib import Path
import os,subprocess,tarfile,tempfile,hashlib,unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/axia_d06_c27_owner_wsl2_nogoal_once.sh"

class C27CompactOwner(unittest.TestCase):
    def test_selfcheck_never_starts_simulation(self):
        with tempfile.TemporaryDirectory() as td:
            env=dict(os.environ,HOME=td,GITHUB_ACTIONS="true")
            r=subprocess.run(["bash",str(SCRIPT),"--self-check"],env=env,
                capture_output=True,text=True,timeout=7)
            self.assertEqual(r.returncode,0,(r.stdout,r.stderr))
            self.assertIn("D06_C27_OWNER_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL",r.stdout)
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_compact_synthetic_no_core_and_preserves_first_crash(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);raw=base/"synthetic.tar.gz"
            source=base/"source";source.mkdir()
            (source/"launch.log").write_text("[ERROR] [gz-21]: process has died [pid 19280, exit code -11]\n")
            (source/"teardown.txt").write_text("P2_L2_GRACEFUL_TEARDOWN\n")
            (source/"private.core").write_bytes(b"DO_NOT_ARCHIVE")
            with tarfile.open(raw,"w:gz") as tf:
                for fn in source.iterdir():
                    tf.add(fn,arcname="one/native/"+fn.name)
            side=Path(str(raw)+".sha256")
            side.write_text(hashlib.sha256(raw.read_bytes()).hexdigest()+"  "+str(raw)+"\n")
            r=subprocess.run(["bash",str(SCRIPT),"--compact-only",str(raw)],
                 env=dict(os.environ,HOME=td,GITHUB_ACTIONS="true"),
                 capture_output=True,text=True,timeout=12)
            self.assertEqual(r.returncode,0,(r.stdout,r.stderr))
            outfile=next((base/"axia_d06_c27_compact").glob("*.tar.gz"))
            with tarfile.open(outfile) as tf:
                members=tf.getnames()
                self.assertIn("launch_tail.log",members)
                self.assertIn("summary.txt",members)
                self.assertFalse(any("private.core" in x for x in members))
                self.assertIn("exit code -11",tf.extractfile("launch_tail.log").read().decode())
            self.assertIn("D06_C27_COMPACT_ARCHIVE=",r.stdout)
            self.assertIn("D06_C27_COMPACT_ONLY_NO_GAZEBO_RUN",r.stdout)

    def test_real_run_requires_wsl2_and_pinned_student_candidate(self):
        source=SCRIPT.read_text()
        for required in (
            'MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA',
            'AXIA_D06_GAZEBO_C27_CANDIDATE=1',
            'AXIA_D06_G07_RX_WITNESS=1',
            '73ed5d3965361d3230cd7df5ceafaf590d9e4e5e',
            'D06_C27_COMPACT_ARCHIVE=', 'D06_C27_OWNER_WSL2_NO_GOAL_NOT_ACCEPTED',
            'core_not_archived=true',
        ):
            self.assertIn(required,source)
        self.assertNotIn("--run-once",source)
        self.assertNotIn("ros2 launch",source)
        self.assertNotIn("gz sim",source)

if __name__=="__main__":unittest.main()
