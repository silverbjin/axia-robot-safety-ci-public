"""RED/ GREEN: exact FastDDS source stamp -> native RMw publish -> TF call.

This module only tests the existing public CI diagnostic. It grants no
CM120 release, Goal authority or certified E-Stop.
"""
import unittest
from copy import deepcopy

from d06.diagnostic.classify_cm_rmw_publish_join import classify_publish_join
from d06.tests.test_g07_cm120_tf_first_gap_join import (
    observer, anchor, metadata, cb, PID, T0,
)


def fixture():
    obs=observer()
    native=metadata()+[
      dict(cb("ros2:callback_start",11.945),procname="collision_monit"),
      dict(cb("ros2:callback_end",11.995),procname="collision_monit"),
      dict(cb("ros2:callback_start",12.005),procname="collision_monit"),
      dict(cb("ros2:callback_end",12.123),procname="collision_monit"),
      dict(name="ros2:rcl_publisher_init",vpid=PID,
           procname="collision_monit",topic_name="/cmd_vel_pre_guard",
           rmw_publisher_handle="0xabc",publisher_handle="0xdef"),
      dict(name="ros2:rmw_publish",vpid=PID,vtid=33,
           procname="collision_monit",rmw_publisher_handle="0xabc",
           timestamp=T0, timestamp_ns=11980000000),
      dict(name="ros2:rmw_publish",vpid=PID,vtid=33,
           procname="collision_monit",rmw_publisher_handle="0xabc",
           timestamp=T0+132000000,timestamp_ns=12112000000),
    ]
    # On this synthetic test the RMW source stamp is from a different host
    # epoch than our fake anchor. It must fail until explicitly calibrated.
    tf={"spans":[{
      "start_rel_observer_ns":14_000_000,
      "end_rel_observer_ns":105_000_000,
      "sleep_request_ns":90_000_000,
      "coverage_complete":True,
    }],"count":1}
    # Synthetic clock anchors whose wall offset matches native publish
    # events. First RMW timestamp is taken at native 11.980s, not at 10s.
    source_anchors={
      "start":{"mono_ns":10_000_000_000,
               "wall_ns":T0-1_980_000_000},
      "end":{"mono_ns":20_000_000_000,
             "wall_ns":T0+8_020_000_000}
    }
    return obs,native,source_anchors,tf


class ExactNativePublisherJoin(unittest.TestCase):
    def test_two_exact_source_timestamps_same_cm_publisher_and_tf_callback(self):
        obs,events,anchors,tf=fixture()
        v=classify_publish_join(obs,events,anchors,tf)
        self.assertEqual(v["status"],"CM_SOURCE_TF_POLLING_NATIVE_PUBLISH_JOIN_PROVEN_SCOPED")
        self.assertTrue(v["rmw_publisher_source_timestamp_pair_exact"])
        self.assertTrue(v["same_cm_input_callback_tf_publisher"])
        self.assertGreaterEqual(v["sleep_requests_within_native_publisher_gap_ns"],90_000_000)
        self.assertFalse(v["cm120_release_pass"])
        self.assertFalse(v["owner_wsl2_accepted"])
        self.assertFalse(v["certified_estop"])

    def test_wrong_timestamp_and_another_publisher_fail_closed(self):
        obs,events,anchors,tf=fixture()
        for mutate in ("one_ns", "other_topic", "other_handle", "missing"):
            with self.subTest(mutate=mutate):
                rows=deepcopy(events)
                if mutate=="one_ns":
                    next(x for x in rows if x["name"]=="ros2:rmw_publish"
                         and x["timestamp"]==T0+132000000)["timestamp"]+=1
                elif mutate=="other_topic":
                    next(x for x in rows if x["name"]=="ros2:rcl_publisher_init")["topic_name"]="/other"
                elif mutate=="other_handle":
                    next(x for x in rows if x["name"]=="ros2:rmw_publish"
                         and x["timestamp"]==T0+132000000)["rmw_publisher_handle"]="0xother"
                else:
                    rows=[x for x in rows if x.get("timestamp")!=T0+132000000]
                v=classify_publish_join(obs,rows,anchors,tf)
                self.assertNotEqual(v["status"],"CM_SOURCE_TF_POLLING_NATIVE_PUBLISH_JOIN_PROVEN_SCOPED")
                self.assertFalse(v["cm120_release_pass"])

    def test_clock_epoch_mismatch_and_wrong_thread_block(self):
        obs,events,anchors,tf=fixture()
        a=deepcopy(anchors)
        a["start"]["wall_ns"]+=10_000_000
        a["end"]["wall_ns"]+=10_000_000
        v=classify_publish_join(obs,events,a,tf)
        self.assertNotEqual(v["status"],"CM_SOURCE_TF_POLLING_NATIVE_PUBLISH_JOIN_PROVEN_SCOPED")
        rows=deepcopy(events)
        next(x for x in rows if x["name"]=="ros2:rmw_publish"
             and x["timestamp"]==T0+132000000)["vtid"]=44
        v=classify_publish_join(obs,rows,anchors,tf)
        self.assertNotEqual(v["status"],"CM_SOURCE_TF_POLLING_NATIVE_PUBLISH_JOIN_PROVEN_SCOPED")

    def test_unobserved_first_source_breach_or_missing_tf_sleep_blocks(self):
        obs,events,anchors,tf=fixture()
        obs[-1]["rmw_source_ns"]=T0+110000000
        v=classify_publish_join(obs,events,anchors,tf)
        self.assertFalse(v["publisher_source_causality_proven"])
        obs,events,anchors,tf=fixture()
        tf["spans"][0]["sleep_request_ns"]=0
        v=classify_publish_join(obs,events,anchors,tf)
        self.assertFalse(v["publisher_source_causality_proven"])


if __name__=="__main__":
    unittest.main()
