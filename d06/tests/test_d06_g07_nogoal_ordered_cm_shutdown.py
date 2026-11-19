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
    def test_opt_in_gazebo_world_pause_precedes_launch_sigint_without_ttl_change(self):
        s=SRC.read_text()
        self.assertIn("AXIA_G07_NO_GOAL_GZ_PAUSE_BEFORE_SIGINT",s)
        self.assertIn("gz service -l",s)
        self.assertIn("gz service -s",s)
        chunk=s[s.index('cleanup() {'):s.index('trap cleanup EXIT')]
        self.assertLess(chunk.index("gz service -s"),
                        chunk.index('kill -INT -- "-$LAUNCH_PID"'))
        self.assertIn("G07_NO_GOAL_GAZEBO_PAUSE_ACK_BEFORE_SIGINT",chunk)
        self.assertIn("G07_NO_GOAL_GAZEBO_PAUSE_FAILED_HOLD",chunk)
        self.assertIn("NO_GOAL_ORDERED",chunk)
        self.assertNotIn("AXIA_SCAN_TTL_SEC=.5",chunk)

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
    def test_two_read_only_witnesses_stop_before_nav2_ordered_shutdown(self):
        s=SRC.read_text()
        assert 'G07_READONLY_WITNESSES_STOPPED' in s
        assert 'AXIA_G07_NO_GOAL_WITNESS_HANDOFF' in s
        assert 'G07_READONLY_WITNESS_HANDOFF_ACK_BEFORE_SHUTDOWN' in s
        self.assertLess(s.index('witness_handoff_before_shutdown()'),s.index('G07_WSLG_NO_GOAL_SENSOR_WINDOW_CANDIDATE_NO_MOVING_ACCEPTANCE'))
        w=(ROOT/".github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml").read_text()
        self.assertIn("AXIA_G07_NO_GOAL_WITNESS_HANDOFF: '1'",w)
        self.assertIn('g07_witness_probe_complete.signal',w)
        self.assertIn('g07_witness_stopped.ack',w)
        self.assertIn('kill -TERM "$native_rx_pid" "$ros_rx_pid"',w)
        self.assertIn('G07_READONLY_WITNESSES_STOPPED',w)
        self.assertIn('[[ "$witness_handoff_done" == 1 ]]',w)

    def test_gazebo8_server_control_stop_after_nav2_ack_before_group_sigint(self):
        # Gazebo Harmonic ServerControl(stop:true) is a documented
        # non-signal shutdown path. No change to Scan300/CM120/Guard150.
        src=SRC.read_text()
        self.assertIn("AXIA_G07_NO_GOAL_GZ_STOP_BEFORE_SIGINT",src)
        self.assertIn("gz.msgs.ServerControl",src)
        self.assertIn("stop: true",src)
        self.assertIn("/server_control",src)
        self.assertIn("G07_NO_GOAL_GAZEBO_SERVER_STOP_ACK_BEFORE_SIGINT",src)
        block=src[src.index("cleanup() {"):src.index("trap cleanup EXIT")]
        self.assertLess(block.index("G07_NO_GOAL_GAZEBO_SERVER_STOP_ACK_BEFORE_SIGINT"),
                        block.index('kill -INT -- "-$LAUNCH_PID"'))
        self.assertIn("G07_NO_GOAL_GAZEBO_SERVER_STOP_FAILED_HOLD",block)
        wf=(ROOT/".github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml").read_text()
        self.assertIn("AXIA_G07_NO_GOAL_GZ_STOP_BEFORE_SIGINT: '1'",wf)
        self.assertIn("g07_gz_server_stop.log",wf)
        self.assertIn("G07_NO_GOAL_GAZEBO_SERVER_STOP_ACK",wf)

    def test_real_l2_localization_timeout_isolation_reuses_prior_task04_fix(self):
        # Actual L2 #44476730420: Scan300 20s good, native RX=0, CM=0,
        # Gazebo server=0, Navigation ACK but localization response TIMEOUT.
        # Reuse already-developed G07 Task04 isolated manager client rather
        # than retry SHUTDOWN or extend CM/Guard/Sensor safety TTL.
        src=(STUDENT/"tools/p2_g07_ordered_shutdown.py").read_text()
        self.assertIn("def _call_isolated_stage(",src)
        self.assertIn('rclpy.create_node("axia_g07_shutdown_"+manager',src)
        self.assertIn("node.destroy_node()",src)
        self.assertIn("ack=_call_isolated_stage(rclpy, manager=key,",src)
        self.assertIn('stages[key+"_response_elapsed_sec"]=ack.get("elapsed_sec")',src)
        self.assertIn('stages[key+"_service_request_sent"]=ack.get("request_sent",False)',src)
        self.assertIn('stages[key+"_service_status"]=ack.get("status")',src)
        self.assertIn('if ack["status"]!="ACK":',src)
        self.assertIn('"BLOCKED_LIFECYCLE_"+key.upper()+"_"+ack["status"]',src)
        self.assertIn("max(0.01, remaining_sec)",src)
        self.assertNotIn("retry_shutdown",src)

    def test_isolated_client_real_call_uses_new_node_per_manager(self):
        import sys
        sys.path.insert(0,str(STUDENT/"tools"))
        spec=importlib.util.spec_from_file_location(
            "axia_lifecycle_stage",STUDENT/"tools/p2_g07_ordered_shutdown.py")
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        class FakeNode:
            def __init__(self,label):self.label=label;self.destroyed=False
            def destroy_node(self):self.destroyed=True
        class FakeRclpy:
            def __init__(self):self.nodes=[]
            def create_node(self,label,enable_rosout=False):
                node=FakeNode(label);self.nodes.append(node);return node
        fake=FakeRclpy()
        original=m.call_native_manage
        calls=[]
        def manage(node,*,manager,command,timeout_sec):
            calls.append((node.label,manager,command,timeout_sec))
            return {"status":"ACK","elapsed_sec":1.25,"request_sent":True}
        try:
            m.call_native_manage=manage
            nav=m._call_isolated_stage(fake,manager="navigation",timeout_sec=29)
            loc=m._call_isolated_stage(fake,manager="localization",timeout_sec=20)
        finally:
            m.call_native_manage=original
        self.assertEqual(nav["status"],"ACK")
        self.assertEqual(loc["status"],"ACK")
        self.assertEqual([n.label for n in fake.nodes],
                         ["axia_g07_shutdown_navigation","axia_g07_shutdown_localization"])
        self.assertTrue(all(n.destroyed for n in fake.nodes))
        self.assertEqual(len(calls),2)
        self.assertEqual([c[2] for c in calls],["shutdown","shutdown"])

    def test_real_l2_requires_full_20s_dual_topic_safe_gate_not_just_cm_exit0(self):
        w=(ROOT/".github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml").read_text()
        self.assertIn('assert rc==0',w)
        self.assertIn('assert sensor["status"]=="NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE"',w)
        self.assertIn('assert not sensor["reasons"]',w)
        self.assertIn('assert startup["both_topics_ready"] is True',w)
        self.assertIn('assert sensor["dual_topic_actual_wall_observation_sec"]>=20',w)
        self.assertIn('assert sensor["metrics"][topic]["max_receipt_gap_sec"]<=.3',w)
        self.assertIn('assert sensor["metrics"]["safety"]["clear_count"]==sensor["metrics"]["safety"]["count"]',w)
        self.assertIn('assert gz_clean and not gz_bad',w)
        self.assertIn('audit["cm_exit_code"]==0',w)

    def test_owner_causal_runner_must_enable_safe_no_goal_teardown(self):
        s=(ROOT/"d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh").read_text()
        self.assertIn('AXIA_G07_NO_GOAL_ORDERED_SHUTDOWN=1',s)
        self.assertIn('SMOKE_BLOB=',s)

if __name__=="__main__":
    unittest.main()
