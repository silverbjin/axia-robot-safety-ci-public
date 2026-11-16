"""Cycle32 RED->GREEN: LTTng diagnostic != moving-Goal acceptance.

Real Cycle31 L2 #43814208942 failed first at SLOW TIMEOUT (min .7459m,
no forward positive in slow zone) during all-node LTTng tracing. This is not
proof tracing caused it; A/B without tracing is necessary before inference.
Run one unchanged ROS/Gazebo Goal with the same CM Guard/Owner safety checks.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT/".github/workflows/axia-g07-unified-gui-one-goal-l2.yml"
class TestCycle32UntracedL2(unittest.TestCase):
    def text(self):
        return WORKFLOW.read_text(encoding="utf-8")
    def test_no_lttng_or_tracer_apt_during_release_goal(self):
        s=self.text()
        self.assertNotIn("lttng start",s)
        self.assertNotIn("lttng enable-event",s)
        self.assertNotIn("lttng stop",s)
        self.assertNotIn("python3-bt2",s)
        self.assertNotIn("bt2.TraceCollectionMessageIterator",s)
    def test_exact_private_shared_goal_and_field_safety_proof_remain(self):
        s=self.text()
        for token in (
          "c1d778c0f8ad68837487b65fc4f8557aef842887",
          "Real Harmonic official TB3 Waffle and Nav2 ONE bounded simulation Goal",
          "Field 150ms hard safety and 120ms release headroom",
          "AXIA_G07_FIELD_REAL_CM_BELOW_120MS_RELEASE_MARGIN_PASS",
          "AXIA_G07_FIELD_REAL_L2_SEVEN_CHANNELS",
          "AXIA_G07_REAL_POST_GOAL_OWNER_IDENTICAL_NAV2_SHUTDOWN_CM_EXIT0_PASS",
          "AXIA_S02_SAME_GOAL_NATIVE_CI_REVIEW",
          "AXIA_G07_REAL_EXACT_NAV2_GOAL_CANCEL_ACK_BEFORE_LIFECYCLE_PASS",
          "OWNER_L3_NOT_RUN",
        ):
            self.assertIn(token,s,token)
    def test_scope_is_same_real_sim_goal_not_synthetic_no_owner(self):
        s=self.text()
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '1'",s)
        self.assertIn("ghcr.io/silverbjin/axia-g07-runtime@sha256:",s)
        self.assertIn("xwininfo",s)
        self.assertNotIn("YES-P2-G07-GOAL",s)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=true",s)
    def test_separate_trace_tools_retained_not_in_l2(self):
        s=self.text()
        self.assertNotIn("Cycle29: start official CM callback",s)
        self.assertNotIn("Cycle29: first CM RMW gap",s)
        self.assertIn("First 120ms original CM publication gap vs native STOP RPC",s)

if __name__=="__main__":unittest.main()
