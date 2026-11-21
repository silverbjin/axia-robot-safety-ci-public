"""C27: public CI tests immutable Student NO_GOAL Gazebo server stop drain.
No ROS/Gazebo/GPU/Goal run: only real native ROS launch log fixtures.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

STUDENT_SHA = "6c79c09d91f13c81961492eb30e66d99d307831c"  # GREEN patched source
EXPECTED_SMOKE_BLOB = "cc3c64f7ae769a11d9daad4acdbdb48141253f7c"
EXPECTED_HELPER_BLOB = "72a117d9a1b22748ffd16171d213916c095a623e"
ROOT = ("https://raw.githubusercontent.com/silverbjin/"
        "axia-robot-safety-student/")
BASE = "block_B/day07/h01_runtime/"

def fetch(relative, expected_blob):
    with tempfile.TemporaryDirectory() as td:
        target=Path(td)/"file"
        p=subprocess.run(["curl","-fLsS","--retry","2","--max-time","40",
            ROOT+STUDENT_SHA+"/"+BASE+relative,"-o",str(target)],
            capture_output=True,text=True,timeout=60)
        if p.returncode:
            raise AssertionError("PINNED_STUDENT_SOURCE_NOT_AVAILABLE: "+p.stderr[:180])
        h=subprocess.run(["git","hash-object",str(target)],capture_output=True,text=True)
        if h.stdout.strip()!=expected_blob:
            raise AssertionError("PINNED_STUDENT_GIT_BLOB_MISMATCH")
        return target.read_text()

class C27StopAckNotExit(unittest.TestCase):
    def test_immutable_student_sources_are_bound_and_ordered(self):
        smoke=fetch("scripts/p2_no_goal_smoke_ci.sh",EXPECTED_SMOKE_BLOB)
        helper=fetch("tools/g07_gazebo_server_exit_guard.sh",EXPECTED_HELPER_BLOB)
        self.assertLess(smoke.index("G07_GAZEBO_SERVER_WAIT_NATIVE_EXIT0_BEFORE_GROUP_SIGINT"),
                        smoke.index('kill -INT -- "-$LAUNCH_PID"'))
        self.assertIn("G07_NO_GOAL_GAZEBO_SERVER_NATIVE_EXIT0_HOLD",smoke)
        self.assertIn('kill -INT "$LAUNCH_PID"',smoke)
        self.assertIn('G07_GAZEBO_SERVER_NATIVE_SIGSEGV_BEFORE_GROUP_SIGINT_HOLD',helper)

    def test_real_log_fixture_exit0_vs_exit_minus11_and_ack_only(self):
        helper=fetch("tools/g07_gazebo_server_exit_guard.sh",EXPECTED_HELPER_BLOB)
        with tempfile.TemporaryDirectory() as td:
            hs=Path(td)/"guard.sh";hs.write_text(helper)
            ok="[INFO] [gz-21]: process has finished cleanly [pid 19280]\n"
            segv="[ERROR] [gz-21]: process has died [pid 19280, exit code -11, cmd 'gz sim -r -s /tmp/world.sdf']\n"
            ack="G07_NO_GOAL_GAZEBO_SERVER_STOP_ACK_BEFORE_SIGINT\n"
            for log,expected,marker in (
                (ok,0,"G07_GAZEBO_SERVER_NATIVE_EXIT0_BEFORE_GROUP_SIGINT"),
                (segv,3,"G07_GAZEBO_SERVER_NATIVE_SIGSEGV_BEFORE_GROUP_SIGINT_HOLD"),
                (ack,3,"G07_GAZEBO_SERVER_NATIVE_EXIT0_TIMEOUT_HOLD"),
            ):
                p=Path(td)/"launch.log";p.write_text(log)
                r=subprocess.run(["bash",str(hs),"--wait",str(p),"1"],
                    capture_output=True,text=True,timeout=6)
                self.assertEqual(r.returncode,expected,(log,r.stdout,r.stderr))
                self.assertIn(marker,r.stdout+r.stderr)

    def test_no_side_effects_in_guard(self):
        helper=fetch("tools/g07_gazebo_server_exit_guard.sh",EXPECTED_HELPER_BLOB)
        for forbidden in ("ros2 launch","kill -KILL","kill -TERM","kill -INT",
                          "MESA_D3D12_DEFAULT_ADAPTER_NAME=", "sysctl -w"):
            self.assertNotIn(forbidden,helper)

if __name__=="__main__":unittest.main()
