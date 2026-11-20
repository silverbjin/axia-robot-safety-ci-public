"""Real pinned Student Guard versus official Nav2 ZERO-stop behavior.

This is a deterministic *component compatibility* test, not evidence
that incident #44652034063 was caused by stop_pub_timeout.  The CM
suppression transition is an *external input schedule* from the official
Nav2 Jazzy publishVelocity() branch, not a forked Collision Monitor.
No ROS, Gazebo, motion goal, TTL or source code mutation occurs here.
"""
import importlib.util
from pathlib import Path
import sys
import unittest


def real_guard():
    root=Path(__file__).resolve().parents[2]
    student=root/"student" if (root/"student").is_dir() else root.parent/"student"
    source=student/"block_B/day07/h01_runtime/ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_base_guard_policy.py"
    if not source.is_file():
        raise AssertionError("PINNED_STUDENT_GUARD_SOURCE_MISSING: "+str(source))
    spec=importlib.util.spec_from_file_location("axia_g07_pinned_guard_policy",source)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


class GenuineGuardAfterCMZeroSuppression(unittest.TestCase):
    def setUp(self):
        self.m=real_guard()
        self.assertEqual(self.m.CM_TTL_SEC,.15)
        self.s=self.m.State()
        self.live=self.m.Motion(.10,.0)
        self.zero=self.m.ZERO
        # Prove that the REAL Guard first actually forwarded nonzero motion.
        self._feed(10.0,self.live,self.live)
        self.assertEqual(self.s.step(10.01),self.live)
        self.assertTrue(self.s.ever_moved)
        self.assertFalse(self.s.latched)

    def _feed(self,at,supervisor,cm=None):
        self.s.receive("supervisor",supervisor,at)
        self.s.receive_supervisor_state("NORMAL",at,goal_id="a"*32,
                                        healthy=True,stop_reason="")
        if cm is not None:
            self.s.receive("collision_monitor",cm,at)

    def test_nav2_zero_stop_five_sim_seconds_then_guard_stays_fail_closed(self):
        # Source-backed official CM behavior: after STOP (ZERO), CM emits
        # ZERO while stop_pub_timeout=5.0 SIM seconds; later it ceases
        # publishing. Here simulated time = host monotonic x1 strictly for
        # this deterministic schedule. No hardware or ROS clock equivalence.
        for i in range(1,102):
            at=10.0+.05*i
            self._feed(at,self.zero,self.zero)
            self.assertEqual(self.s.step(at+.01),self.zero)
            self.assertFalse(self.s.latched)
        # The official CM branch ceases its ZERO output. Supervisor is still
        # alive; receiving ZERO from it MUST NOT waive Guard CM150.
        self._feed(15.30,self.zero,cm=None)
        self.assertEqual(self.s.step(15.31),self.zero)
        self.assertEqual(self.s.reason,"UPSTREAM_STALE_AFTER_MOTION")
        self.assertTrue(self.s.latched)
        self.assertGreater(self.s.diagnostic_snapshot(15.31)["cm_age_sec"],.15)

    def test_real_cm_loss_after_motion_indistinguishable_from_intentional_silence(self):
        self._feed(10.21,self.zero,cm=None)
        self.assertEqual(self.s.step(10.22),self.zero)
        self.assertTrue(self.s.latched)
        self.assertEqual(self.s.reason,"UPSTREAM_STALE_AFTER_MOTION")
        # Replacing the watchdog with a no-latch branch would hide CM death.

    def test_short_zero_with_live_cm_does_not_false_latch(self):
        for i in range(1,12):
            at=10.0+.05*i
            self._feed(at,self.zero,self.zero)
            self.assertEqual(self.s.step(at+.01),self.zero)
            self.assertFalse(self.s.latched)

    def test_explicit_protective_stop_still_latches_with_fresh_cm(self):
        self.s.receive("supervisor",self.zero,10.05)
        self.s.receive("collision_monitor",self.zero,10.05)
        self.s.receive_supervisor_state("PROTECTIVE_STOP",10.05,
                                        goal_id="a"*32,healthy=False,
                                        stop_reason="OBSTACLE")
        self.assertEqual(self.s.step(10.06),self.zero)
        self.assertTrue(self.s.latched)
        self.assertIn(self.s.reason,("SUPERVISOR_SAFETY_STOP",
                                    "CM_EXCEEDS_SUPERVISOR"))


if __name__=="__main__":
    unittest.main()
