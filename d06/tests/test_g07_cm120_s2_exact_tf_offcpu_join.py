"""S2 exact S1 first-gap TF interval pairing, legacy compatibility."""
import unittest
from d06.diagnostic.analyze_first_cm_tf import analyze
from d06.tests.test_g07_cm120_tf_first_gap_join import observer,trace,anchor,line,READY

def extended(*,runqueue=1_000_000,valid=1,voluntary=10,involuntary=0):
    return (line(12.014,12.105,cpu=.0003)
            +(" schedstat_valid=%d runqueue_ns=%d sched_cpu_ns=500000"
               " voluntary_cs=%d involuntary_cs=%d" %
               (valid,runqueue,voluntary,involuntary)))

class TestSameCMFirstGapSchedProvenance(unittest.TestCase):
    def test_s1_legacy_remains_fail_closed_without_s2_fields(self):
        r=analyze(observer(),trace(),[READY,line(12.014,12.105)],anchor())
        self.assertEqual(r["s2_offcpu_provenance"]["status"],
                         "S2_SCHEDULER_METRICS_NOT_COLLECTED_HOLD")
        self.assertFalse(r["root_cause_proven"])

    def test_same_pid_tid_tf_with_voluntary_switches(self):
        r=analyze(observer(),trace(),[READY,extended()],anchor())
        self.assertEqual(r["status"],"TF_FUNCTION_DOMINANT_WAIT_CAUSE_UNPROVEN")
        self.assertEqual(r["s2_offcpu_provenance"]["status"],
                         "VOLUNTARY_BLOCKING_DOMINANT")
        self.assertFalse(r["tf_wait_proven"])
        self.assertFalse(r["gate_c_authorized"])

    def test_scheduler_delay_dominates_first_callback_only_with_metrics(self):
        r=analyze(observer(),trace(),
                  [READY,extended(runqueue=83_000_000,voluntary=0,involuntary=7)],
                  anchor())
        self.assertEqual(r["s2_offcpu_provenance"]["status"],
                         "RUNQUEUE_WAIT_DOMINANT")
        self.assertFalse(r["root_cause_proven"])

    def test_disabled_schedstat_never_interprets_zero_delay(self):
        r=analyze(observer(),trace(),
                  [READY,extended(runqueue=0,valid=0,voluntary=10)],anchor())
        self.assertEqual(r["s2_offcpu_provenance"]["status"],
                         "SCHEDSTAT_UNAVAILABLE_HOLD")
        self.assertFalse(r["root_cause_proven"])

if __name__=="__main__":
    unittest.main()
