"""S2 actual sleep within first official CM TF interval, no release pass."""
import unittest
from d06.diagnostic.classify_tf_non_cpu import classify_tf_offcpu
from d06.diagnostic.analyze_first_cm_tf import analyze
from d06.tests.test_g07_cm120_tf_first_gap_join import (
    observer,trace,anchor,line,READY)

def log(ns, calls, *,valid=0):
    return (line(12.014,12.105,cpu=.0003)
            +(" schedstat_valid=%d runqueue_ns=0 sched_cpu_ns=0"
               " voluntary_cs=10 involuntary_cs=0 sleep_ns=%d sleep_calls=%d"
               % (valid,ns,calls)))

class TestTFActualSleep(unittest.TestCase):
    def test_actual_sleep_can_explain_offcpu_without_schedstats(self):
        v=analyze(observer(),trace(),
                  [READY,log(88_000_000,9)],anchor())
        self.assertEqual(v["s2_offcpu_provenance"]["status"],
                         "TF_FUNCTION_SLEEP_DOMINANT")
        self.assertGreater(v["s2_offcpu_provenance"]["tf_function_actual_sleep_ms"],80)
        self.assertFalse(v["tf_wait_proven"])
        self.assertFalse(v["gate_c_authorized"])
        self.assertFalse(v["cm120_release_pass"])

    def test_without_libc_sleep_and_disabled_schedstats_remains_unattributed(self):
        v=analyze(observer(),trace(),[READY,log(0,0)],anchor())
        self.assertEqual(v["s2_offcpu_provenance"]["status"],
                         "SCHEDSTAT_UNAVAILABLE_HOLD")
        self.assertFalse(v["root_cause_proven"])

    def test_impossible_sleep_exceeds_non_cpu_fail_closed(self):
        v=analyze(observer(),trace(),[READY,log(120_000_000,12)],anchor())
        self.assertEqual(v["s2_offcpu_provenance"]["status"],
                         "INVALID_SCHEDULER_METRICS_HOLD")
        self.assertFalse(v["gate_c_authorized"])

if __name__=="__main__":
    unittest.main()
