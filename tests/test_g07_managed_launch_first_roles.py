"""G25 first managed-exit 26s failure: bounded first process-role facts only.

Historic native #44876350954 C2: Goal/CLEAR/SLOW/STOP/dwell/Cancel +
Nav/Loc ACK, then first G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET.
No raw command lines, PID or private paths may enter a public artifact.
"""
import unittest
from pathlib import Path
from d06.diagnostic.g07_managed_launch_first_roles import classify

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml"

class NativeManagedExitFirstRoles(unittest.TestCase):
    def test_same_26sec_launch_alive_keeps_role_counts_only(self):
        raw="PID PGID STAT COMMAND\n"
        raw+="701 688 S /usr/bin/python3 /private/teacher/launch/ros2 launch tb3_world.launch.py\n"
        raw+="702 688 Sl /usr/lib/gz/gz sim -r /private/teacher/world.sdf\n"
        raw+="703 688 S /private/src/p2_supervisor_node --ros-args --params-file /tmp/secret\n"
        result=classify(raw,managed_timeout=True)
        self.assertEqual(result["status"],"MANAGED_LAUNCH_26S_RETAINED_PROCESSES_HOLD")
        self.assertEqual(result["roles"]["ros2_launch"],1)
        self.assertEqual(result["roles"]["gazebo"],1)
        self.assertEqual(result["roles"]["safety_supervisor"],1)
        self.assertEqual(result["retained_process_count"],3)
        self.assertFalse(result["root_cause_proven"])
        self.assertFalse(result["clean_exit_proven"])
        self.assertEqual(result["release"],"HOLD")
        self.assertNotIn("teacher",str(result))
        self.assertNotIn("/private",str(result))
        self.assertNotIn("701",str(result))
        self.assertFalse(result["certified_estop"])

    def test_missing_or_oversize_process_snapshot_cannot_become_pass(self):
        from d06.diagnostic.g07_managed_launch_first_roles import classify
        r=classify(None,managed_timeout=True)
        self.assertEqual(r["status"],"MANAGED_EXIT_ROLE_SNAPSHOT_MISSING_HOLD")
        self.assertEqual(r["release"],"HOLD")
        r=classify("S" * 70000,managed_timeout=True)
        self.assertEqual(r["status"],"MANAGED_EXIT_ROLE_SNAPSHOT_MISSING_HOLD")

    def test_native_workflow_publishes_only_bounded_first_role_verdict(self):
        source=WF.read_text()
        self.assertIn("g07_managed_launch_first_roles.py",source)
        self.assertIn("managed_launch_first_roles.json",source)
        self.assertIn("managed_launch_first_roles.json.sha256",source)
        upload=source.split("uses: actions/upload-artifact@",1)[-1]
        self.assertIn("public_evidence/managed_launch_first_roles.json",upload)
        self.assertNotIn("native/teardown_processes.txt",upload)
        self.assertNotIn("native/launch.log",upload)

if __name__=="__main__":
    unittest.main()
