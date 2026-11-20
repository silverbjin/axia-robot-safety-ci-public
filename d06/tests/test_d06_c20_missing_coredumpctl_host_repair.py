"""C20: local WSL2 missing-coredumpctl recovery runs no ROS/Gazebo.
C12 already proves missing CLI and real Noble package, C20 checks one-shot
host-safe fix and immutable existing-only analyzer. Never replays the crash.
"""
from pathlib import Path
import subprocess, tempfile, os, unittest
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/axia_d06_c20_coredumpctl_existing_only_repair.sh"
class C20NoReplay(unittest.TestCase):
    def test_one_shot_static_and_no_side_effects(self):
        s=SCRIPT.read_text()
        self.assertEqual(subprocess.run(["bash","-n",str(SCRIPT)]).returncode,0)
        with tempfile.TemporaryDirectory() as td:
            env=os.environ.copy();env["HOME"]=td
            r=subprocess.run(["bash",str(SCRIPT),"--self-check"],env=env,
                 capture_output=True,text=True,timeout=6)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn("C20_STATIC_L0_PASS_NO_ROS_NO_GAZEBO",r.stdout)
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_missing_tool_installs_only_official_noble_package(self):
        s=SCRIPT.read_text()
        self.assertIn('command -v coredumpctl',s)
        self.assertIn('sudo apt-get update',s)
        self.assertIn('sudo env DEBIAN_FRONTEND=noninteractive apt-get install',s)
        self.assertIn('--no-install-recommends systemd-coredump',s)
        self.assertIn('D06_C20_POSTCRASH_INSTALL_CANNOT_RECREATE_OLD_CORE',s)
        self.assertIn('coredumpctl --help',s)
        self.assertIn('--json',s)

    def test_frozen_existing_only_and_no_replay(self):
        s=SCRIPT.read_text()
        self.assertIn('1f0c5e9fffd0d40d151129dd72b6eb840266655a',s)
        self.assertIn('3ba68b695c91d058604b9cfc9c37e4a3cd0d257d',s)
        self.assertIn('git hash-object',s)
        self.assertIn('AXIA_D06_EXPECTED_GAZEBO_PID=19280',s)
        self.assertIn('--existing-only',s)
        self.assertIn('GITHUB_ACTIONS',s)
        for forbidden in ('--run-once','--nvidia-causal','send_goal','cmd_vel',
                          'LD_PRELOAD=','RMW_IMPLEMENTATION=','sysctl -w','pkill '):
            self.assertNotIn(forbidden,s)

if __name__=="__main__":unittest.main()
