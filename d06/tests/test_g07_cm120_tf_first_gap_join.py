"""Fail-closed Gate B time-domain regression, no ROS or fake safety PASS."""
import unittest
from d06.diagnostic.analyze_first_cm_tf import analyze

PID=4242
T0=1800000000000000000
def metadata():
    return [
      dict(name="ros2:rcl_subscription_init",vpid=PID,
           procname="collision_monit",topic_name="/cmd_vel_supervised",
           subscription_handle="0xa"),
      dict(name="ros2:rclcpp_subscription_init",vpid=PID,
           procname="collision_monit",subscription_handle="0xa",
           subscription="0xb"),
      dict(name="ros2:rclcpp_subscription_callback_added",vpid=PID,
           procname="collision_monit",subscription="0xb",callback="0xc"),
    ]
def cb(name,t,tid=33):
    return dict(name=name,vpid=PID,vtid=tid,callback="0xc",
                timestamp_ns=round(t*1e9))
def observer():
    return [
      dict(kind="owner_goal_published",t=11.0),
      dict(kind="pre_guard",t=12.0,rmw_source_ns=T0,rmw_publication_seq=6),
      dict(kind="pre_guard",t=12.132,rmw_source_ns=T0+132000000,rmw_publication_seq=7),
    ]
def anchor():
    return dict(start=dict(mono_ns=10000000000,wall_ns=T0),
                end=dict(mono_ns=20000000000,wall_ns=T0+10000000000))
def line(start,end,cpu=.004,pid=PID,tid=33):
    return ("TF_ADV pid=%d tid=%d mono_start_ns=%d mono_end_ns=%d "
            "thread_cpu_ns=%d ok=1" % (pid,tid,round(start*1e9),
            round(end*1e9),round(cpu*1e9)))
def trace():
    return metadata()+[cb("ros2:callback_start",12.010),
                       cb("ros2:callback_end",12.110)]
READY="AXIA_CM120_TF_DIAG_CM_LIBRARY_LOADED"

class GateBFirstRealTFInterval(unittest.TestCase):
    def test_dominant_advanced_tf_wall_is_not_claimed_as_tf_blocking(self):
        v=analyze(observer(),trace(),[READY,line(12.014,12.105)],anchor())
        self.assertEqual(v["status"],"TF_FUNCTION_DOMINANT_WAIT_CAUSE_UNPROVEN")
        self.assertAlmostEqual(v["first_cm_rmw_source_gap_ms"],132)
        self.assertAlmostEqual(v["cm_callback_wall_ms"],100)
        self.assertAlmostEqual(v["tf_function_wall_ms"],91)
        self.assertFalse(v["tf_wait_proven"])
        self.assertFalse(v["root_cause_proven"])
        self.assertFalse(v["gate_c_authorized"])
        self.assertFalse(v["cm120_release_pass"])

    def test_short_tf_does_not_authorize_executor_tuning(self):
        v=analyze(observer(),trace(),[READY,line(12.020,12.024)],anchor())
        self.assertEqual(v["status"],"CM_OTHER_OR_QUEUING_DOMINANT_CAUSE_UNPROVEN")
        self.assertFalse(v["scheduler_wait_proven"])
        self.assertFalse(v["gate_c_authorized"])

    def test_wrong_owner_ambiguous_clock_or_no_hook_blocks_causes(self):
        for data,anchors in [
            ([READY,line(12.014,12.104,pid=4243)],anchor()),
            ([READY],anchor()),
            ([READY,line(12.014,12.104)],
             dict(start=dict(mono_ns=10_000_000_000,wall_ns=T0),
                  end=dict(mono_ns=20_000_000_000,wall_ns=T0+10_200_000_000)))
        ]:
            with self.subTest(data=data):
                v=analyze(observer(),trace(),data,anchors)
                self.assertFalse(v["root_cause_proven"])
                self.assertFalse(v["gate_c_authorized"])
                self.assertFalse(v["cm120_release_pass"])

if __name__=="__main__":
    unittest.main()
