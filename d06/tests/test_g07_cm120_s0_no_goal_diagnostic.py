"""S0 RED contract: CM only callback bounded filter and real process maps."""
import unittest
from d06.diagnostic.s0_cm_diag_readiness import select_exact_cm_callbacks, check_cm_loaded

PID=4242
META=[
    dict(name="ros2:rcl_subscription_init",vpid=PID,procname="collision_monit",
         topic_name="/cmd_vel_supervised",subscription_handle="0xa"),
    dict(name="ros2:rclcpp_subscription_init",vpid=PID,procname="collision_monit",
         subscription_handle="0xa",subscription="0xb"),
    dict(name="ros2:rclcpp_subscription_callback_added",vpid=PID,
         procname="collision_monit",subscription="0xb",callback="0xc")]
def cb(kind,handle,tid=11):
    return dict(name=kind,callback=handle,vpid=PID,vtid=tid,
                procname="collision_monit",timestamp_ns=1800000000000000000)

class ReadinessS0(unittest.TestCase):
    def test_100k_unrelated_events_must_not_overflow(self):
        def events():
            yield from META
            for n in range(100_005):
                yield cb("ros2:callback_start","0xother")
            yield cb("ros2:callback_start","0xc")
            yield cb("ros2:callback_end","0xc")
        result=select_exact_cm_callbacks(events())
        self.assertEqual(result["status"],"EXACT_CM_CALLBACK_FILTER_READY")
        self.assertEqual(len(result["rows"]),len(META)+2)
        self.assertEqual(result["stats"]["accepted_cm_callback_count"],2)
        self.assertGreater(result["stats"]["raw_examined"],100000)
        self.assertFalse(result["release_pass"])

    def test_own_callback_overflow_fails_closed(self):
        result=select_exact_cm_callbacks(iter(META+[cb("ros2:callback_start","0xc")]*6),
                                         max_target_events=4)
        self.assertEqual(result["status"],"TARGET_CM_CALLBACK_TRACE_UNBOUNDED_HOLD")
        self.assertFalse(result["release_pass"])

    def test_ambiguous_or_missing_link_is_not_green(self):
        result=select_exact_cm_callbacks(iter(META[:1]+[cb("ros2:callback_start","0xc")]))
        self.assertNotEqual(result["status"],"EXACT_CM_CALLBACK_FILTER_READY")
        result=select_exact_cm_callbacks(iter(META+[dict(META[0],vpid=4321)]))
        self.assertNotEqual(result["status"],"EXACT_CM_CALLBACK_FILTER_READY")

    def test_real_maps_must_show_owned_cm_before_timing(self):
        lib="/tmp/axia_g07_cm120_abi/libaxia_g07_cm120_tf_diag.so"
        maps="7fa000-7fb000 r-xp 00000000 00:01 42 "+lib+"\n"
        good=check_cm_loaded("collision_monit\n",maps,lib)
        self.assertEqual(good["status"],"CM_SHIM_MAPPED_NO_GOAL")
        self.assertFalse(good["tf_call_observed"])
        self.assertFalse(good["goal_authorized"])
        for comm,m in (("python3\n",maps),("collision_monit\n",""),
                       ("collision_monit\n",maps.replace(lib,"/wrong.so"))):
            bad=check_cm_loaded(comm,m,lib)
            self.assertNotEqual(bad["status"],"CM_SHIM_MAPPED_NO_GOAL")
            self.assertFalse(bad["goal_authorized"])

if __name__=="__main__":
    unittest.main()
