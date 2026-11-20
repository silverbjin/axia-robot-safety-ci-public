"""C22: explicit single synthetic SIGSEGV exercises WSL2 systemd-coredump
backend BEFORE any future Gazebo run. L0 never starts Gazebo or segfaults.
Only actual Owner WSL2 can establish a real backend result.
"""
from pathlib import Path
import os, subprocess, tempfile, unittest
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/axia_d06_c22_wsl2_core_pipeline_probe_once.sh"

class C22CoreTransportPreflight(unittest.TestCase):
    def test_syntax_and_selfcheck_no_core_no_gazebo(self):
        src=SCRIPT.read_text()
        self.assertEqual(subprocess.run(["bash","-n",str(SCRIPT)]).returncode,0)
        with tempfile.TemporaryDirectory() as td:
            env=dict(os.environ,HOME=td,GITHUB_ACTIONS="true")
            p=subprocess.run(["bash",str(SCRIPT),"--self-check"],
                capture_output=True,text=True,env=env,timeout=5)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn("D06_C22_STATIC_PASS_NO_ROS_NO_GAZEBO_NO_CRASH",p.stdout)
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_ci_host_probe_is_denied_before_crash(self):
        with tempfile.TemporaryDirectory() as td:
            env=dict(os.environ,HOME=td,GITHUB_ACTIONS="true")
            p=subprocess.run(["bash",str(SCRIPT),"--probe-once"],
                capture_output=True,text=True,env=env,timeout=5)
            self.assertEqual(p.returncode,3,(p.stdout,p.stderr))
            self.assertIn("D06_C22_NOT_OWNER_WSL2_NO_CRASH",p.stdout+p.stderr)
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_single_isolated_crash_with_coredumpctl_dump_and_gdb_evidence(self):
        s=SCRIPT.read_text()
        for required in (
          "kill -s SEGV", "ulimit -c 65536", "coredumpctl --no-pager info",
          'coredumpctl dump', "gdb -nx -q -batch",
          "D06_C22_SYSTEMD_CORE_RETRIEVAL_NOT_PROVEN_HOLD_NO_GAZEBO",
          "D06_C22_SYNTHETIC_COREDUMP_PIPELINE_PASS_NOT_GAZEBO",
          "D06_C22_FORENSIC_ARCHIVE=", "sha256sum",
          "core_not_archived=true", "AXIA_MVP_DEMO_ACCEPTED=HOLD",
          "CERTIFIED_ESTOP=false"):
            self.assertIn(required,s)
        self.assertIn('if [[ "$MODE" == --self-check ]]',s)

    def test_no_simulation_no_host_override_and_private_core_removed(self):
        s=SCRIPT.read_text()
        for forbidden in (
          "gz sim", "ros2 launch", "--nvidia-causal", "--run-once",
          "send_goal", "cmd_vel", "sudo ", "apt-get", "sysctl -w",
          "LD_PRELOAD=", "RMW_IMPLEMENTATION=", "GITHUB_TOKEN"):
            self.assertNotIn(forbidden,s)
        self.assertIn('rm -f -- "$RUN/private.core"',s)
        self.assertIn('tar -czf "$archive" summary.txt preflight.txt probe_result.txt gdb_excerpt.txt',s)
        self.assertIn('D06_C22_NO_GOAL_ACCEPTANCE_NOT_RUN',s)

if __name__=="__main__": unittest.main()
