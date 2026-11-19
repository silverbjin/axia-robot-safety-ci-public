"""Regression for WSLg UCMOonHr CM -11 on NO_GOAL cleanup.
The official Nav2 lifecycle shutdown must precede launch SIGINT; the
P2_L2_GRACEFUL_TEARDOWN marker alone is not CM process exit0 evidence.
"""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
# Public L0 checks out student inside repo; real container L2 checks it out
# beside ci/. Resolve the two explicitly, never silently skip real source.
STUDENT_ROOT=ROOT/"student" if (ROOT/"student").is_dir() else ROOT.parent/"student"
STUDENT=STUDENT_ROOT/"block_B/day07/h01_runtime"
SRC=STUDENT/"scripts/p2_no_goal_smoke_ci.sh"
AUDIT=STUDENT/"tools/p2_g07_owner_shutdown_audit.py"

class NoGoalCMShutdownRegression(unittest.TestCase):
    def test_opt_in_nogoal_uses_existing_nav2_ordered_shutdown_before_sigint(self):
        s=SRC.read_text()
        self.assertIn('AXIA_G07_NO_GOAL_ORDERED_SHUTDOWN',s)
        self.assertIn('AXIA_G07_OWNER_SENSOR_TRUTH_NO_GOAL',s)
        self.assertIn('tools/p2_g07_ordered_shutdown.py',s)
        cleanup=s[s.index("cleanup() {"):s.index("trap cleanup EXIT")]
        self.assertLess(cleanup.index('tools/p2_g07_ordered_shutdown.py'),
                        cleanup.index('kill -INT -- "-$LAUNCH_PID"'))
        self.assertIn('G07_NO_GOAL_NATIVE_NAV2_ORDERED_SHUTDOWN_ACK',cleanup)
        self.assertIn('G07_NO_GOAL_NATIVE_NAV2_ORDERED_SHUTDOWN_BLOCKED',cleanup)
    def test_requires_both_ack_and_actual_cm_child_exit_zero(self):
        s=SRC.read_text()
        self.assertIn('tools/p2_g07_owner_shutdown_audit.py',s)
        self.assertIn('AXIA_G07_NO_GOAL_ORDERED_SHUTDOWN',s)
        self.assertIn('G07_NO_GOAL_NATIVE_CM_CHILD_EXIT0',s)
    def test_original_cm_minus11_is_never_green_even_with_graceful_parent(self):
        spec=importlib.util.spec_from_file_location("shutdown_audit",AUDIT)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        abnormal="[ERROR] [collision_monitor-16]: process has died [pid 1760, exit code -11]\\n"
        a=m.audit(abnormal+"P2_L2_GRACEFUL_TEARDOWN", "navigation_ack=true")
        self.assertEqual(a["cm_exit_code"],-11)
        self.assertEqual(a["status"],"BLOCKED_CM_ABNORMAL_EXIT")
        clean="[INFO] [collision_monitor-16]: process has finished cleanly [pid 1760]\\n"
        v=m.audit(clean,"navigation_ack=true")
        self.assertEqual(v["cm_exit_code"],0)
        self.assertEqual(v["status"],"SHUTDOWN_CLEAN_CANDIDATE")
    def test_owner_causal_runner_must_enable_safe_no_goal_teardown(self):
        s=(ROOT/"d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh").read_text()
        self.assertIn('AXIA_G07_NO_GOAL_ORDERED_SHUTDOWN=1',s)
        self.assertIn('SMOKE_BLOB=',s)

if __name__=="__main__":
    unittest.main()
