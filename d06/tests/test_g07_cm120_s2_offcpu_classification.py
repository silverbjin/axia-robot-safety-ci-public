"""S2 RED: runqueue delay vs voluntary blocking; never claim TF buffer cause."""
import unittest
from d06.diagnostic.classify_tf_non_cpu import classify_tf_offcpu

MS=1_000_000
def classify(runqueue_ms,voluntary=0,involuntary=0,available=True):
    return classify_tf_offcpu(wall_ns=101_683_000,cpu_ns=323_000,
        schedstat_available=available,runqueue_ns=round(runqueue_ms*MS),
        sched_cpu_ns=400_000,voluntary_cs=voluntary,involuntary_cs=involuntary)

class S2StrictFirstTfCost(unittest.TestCase):
    def test_voluntary_blocking_dominant_does_not_claim_tf_buffer_wait(self):
        v=classify(1.0,voluntary=10,involuntary=0)
        self.assertEqual(v["status"],"VOLUNTARY_BLOCKING_DOMINANT")
        self.assertGreater(v["offcpu_ms"],100)
        self.assertGreater(v["blocking_or_sleep_upper_ms"],99)
        self.assertFalse(v["tf_buffer_wait_proven"])
        self.assertFalse(v["gate_c_authorized"])

    def test_runqueue_wait_dominant_with_schedstats_proof(self):
        v=classify(95.0,voluntary=1,involuntary=8)
        self.assertEqual(v["status"],"RUNQUEUE_WAIT_DOMINANT")
        self.assertGreater(v["runqueue_wait_ms"],94)
        self.assertFalse(v["release_pass"])

    def test_schedstats_unavailable_does_not_misclassify_zero_wait(self):
        v=classify(0,voluntary=12,available=False)
        self.assertEqual(v["status"],"SCHEDSTAT_UNAVAILABLE_HOLD")
        self.assertFalse(v["root_cause_proven"])

    def test_unsupported_unreasonable_counters_fail_closed(self):
        for kw in [
          dict(wall_ns=10,cpu_ns=20,schedstat_available=True,
               runqueue_ns=0,sched_cpu_ns=1,voluntary_cs=1,involuntary_cs=0),
          dict(wall_ns=101_683_000,cpu_ns=323_000,
               schedstat_available=True,runqueue_ns=140_000_000,
               sched_cpu_ns=400_000,voluntary_cs=10,involuntary_cs=0),
          dict(wall_ns=101_683_000,cpu_ns=323_000,
               schedstat_available=True,runqueue_ns=0,
               sched_cpu_ns=400_000,voluntary_cs=-1,involuntary_cs=0),
        ]:
            with self.subTest(kw=kw):
                v=classify_tf_offcpu(**kw)
                self.assertEqual(v["status"],"INVALID_SCHEDULER_METRICS_HOLD")
                self.assertFalse(v["gate_c_authorized"])

    def test_zero_context_switches_is_not_proven_sleep(self):
        v=classify(1,voluntary=0,involuntary=0)
        self.assertEqual(v["status"],"OFFCPU_MIXED_UNPROVEN")

if __name__=="__main__":
    unittest.main()
