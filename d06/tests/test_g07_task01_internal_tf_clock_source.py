"""Task01 original official CM TF-internal ROS time, not an outside /clock proxy.

Synthetic L0 contract for new DIAGNOSTIC ONLY rcl_clock_get_now interposition.
The buffer's real clock type / override state may be proven only with genuine
official Jazzy ABI and original CM PID/TID in the same Moving first-gap run.
"""
import json
import unittest
from d06.diagnostic.export_public_cm120_first_gap import export_sanitized
from d06.tests.test_g07_cm120_tf_first_gap_join import (
    READY, observer, trace, anchor, line
)
from d06.tests.test_g07_cm120_task01_per_sleep_span_join import poll

SHA="0123456789abcdef0123456789abcdef01234567"


def tick(mono,ros_ns,*,pid=4242,tid=33,clock_type=1,active=1):
    return (f"TF_CLOCK pid={pid} tid={tid} mono_ns={round(mono*1e9)} "
            f"ros_ns={ros_ns} clock_type={clock_type} override_active={active}")


def fixture(ticks):
    # Include actual named official advanced getTransform interval and 2
    # slept events; the full L0 contract cannot infer a proven source cause.
    return export_sanitized(observer(),trace(),[
        READY,line(12.014,12.105,cpu=.0003),
        poll(12.024,12.034),poll(12.044,12.054),*ticks
    ],anchor(),run_id="44040000001",public_sha=SHA)


class ExactTfInternalClockContract(unittest.TestCase):
    def test_internal_clock_same_owner_and_call_is_numeric_only_and_not_release(self):
        out=fixture([
            tick(12.014,1_000_000_000),
            tick(12.024,1_003_000_000),
            tick(12.044,1_006_000_000),
            tick(12.054,1_007_000_000)])
        ck=out["tf_internal_clock"]
        self.assertEqual(ck["status"],"TF_INTERNAL_RCL_CLOCK_SAMPLES_OBSERVED_CAUSALITY_HOLD")
        self.assertEqual(ck["clock_type"],1)
        self.assertEqual(ck["override_active"],True)
        self.assertEqual(ck["sample_count"],4)
        self.assertEqual(ck["sim_advance_ns"],7_000_000)
        self.assertEqual(ck["mono_advance_ns"],40_000_000)
        self.assertFalse(ck["tf_buffer_availability_wait_proven"])
        self.assertFalse(ck["same_rmw_source_clock_alignment_proven"])
        self.assertFalse(out["root_cause_proven"])
        self.assertFalse(out["cm120_release_pass"])
        for hidden in ("pid","tid","rcl_clock_t","/cmd_vel_supervised"):
            self.assertNotIn(hidden,json.dumps(ck))

    def test_other_pid_tid_clock_must_not_poison_exact_cm_call(self):
        out=fixture([tick(12.014,1_000_000_000),
                     tick(12.044,1_004_000_000),
                     tick(12.024,999_000_000,pid=4243),
                     tick(12.034,123_000_000,tid=34)])
        ck=out["tf_internal_clock"]
        self.assertEqual(ck["sample_count"],2)
        self.assertEqual(ck["sim_advance_ns"],4_000_000)
        self.assertFalse(ck["same_rmw_source_clock_alignment_proven"])

    def test_clock_rewind_is_hold_no_true_causality(self):
        ck=fixture([tick(12.014,1_000_000_000),
                    tick(12.044,990_000_000)])["tf_internal_clock"]
        self.assertEqual(ck["status"],"TF_INTERNAL_CLOCK_REWIND_HOLD")
        self.assertFalse(ck["tf_buffer_availability_wait_proven"])

    def test_ros_clock_override_disabled_is_not_claimed_as_sim(self):
        ck=fixture([tick(12.014,1_000_000_000,active=0),
                    tick(12.044,1_030_000_000,active=0)])["tf_internal_clock"]
        self.assertEqual(ck["status"],"TF_CLOCK_OVERRIDE_NOT_ACTIVE_HOLD")
        self.assertFalse(ck["tf_buffer_availability_wait_proven"])

    def test_incomplete_single_sample_or_disparate_clock_types_hold(self):
        ck=fixture([tick(12.014,1_000_000_000)])["tf_internal_clock"]
        self.assertEqual(ck["status"],"TF_INTERNAL_CLOCK_INSUFFICIENT_SAMPLES_HOLD")
        ck=fixture([tick(12.014,1_000_000_000),
                    tick(12.044,1_030_000_000,clock_type=2)])["tf_internal_clock"]
        self.assertEqual(ck["status"],"TF_INTERNAL_CLOCK_INCONSISTENT_TYPE_HOLD")

    def test_legacy_raw_without_clock_is_still_accepted_as_diagnostic_only(self):
        v=fixture([])
        self.assertNotIn("tf_internal_clock",v)
        self.assertFalse(v["root_cause_proven"])
        self.assertFalse(v["gate_c_authorized"])


if __name__=="__main__":
    unittest.main()
