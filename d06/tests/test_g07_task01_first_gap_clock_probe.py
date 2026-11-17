"""Synthetic ROS /clock callback window, never original TF buffer clock proof."""
import unittest
from d06.diagnostic.firstgap_clock_progress import summarize

T0=73_262_840_714

def obs(samples):
    return [{"mono_ns":T0+int(m*1e6),"sim_ns":int(s*1e6)}
            for m,s in samples]

class Task01SameWindowClockProbe(unittest.TestCase):
    def test_slow_clock_and_tf_polling_only_candidate_no_causality(self):
        d=summarize(obs([(-20,1000),(-5,1005),(0,1010),(15,1013),
                         (35,1015),(55,1017),(90,1018),
                         (125,1019),(128.4,1020),(150,1022)]),
                    T0,T0+128_391_951)
        self.assertEqual(d["status"],"CLOCK_OBSERVER_WINDOW_BRACKETED_HYPOTHESIS_ONLY")
        self.assertEqual(d["observer_pair_clock_sample_count"],6)
        self.assertLess(d["sim_to_wall_progress_ratio"],0.20)
        self.assertTrue(d["slow_sim_progress_candidate"])
        self.assertFalse(d["clock_causality_proven"])
        self.assertFalse(d["tf_buffer_clock_progress_proven"])
        self.assertFalse(d["source_publication_to_monotonic_alignment_proven"])
        self.assertFalse(d["cm120_release_pass"])
        self.assertLessEqual(len(d["samples"]),96)

    def test_fast_clock_does_not_prove_tf_buffer_wait(self):
        d=summarize(obs([(-5,1000),(0,1005),(35,1040),
                         (90,1090),(125,1125),(131,1131)]),
                    T0,T0+128_391_951)
        self.assertEqual(d["status"],"CLOCK_OBSERVER_WINDOW_BRACKETED_HYPOTHESIS_ONLY")
        self.assertFalse(d["slow_sim_progress_candidate"])
        self.assertFalse(d["tf_buffer_clock_progress_proven"])

    def test_unbracketed_or_rewind_fails_closed(self):
        d=summarize(obs([(20,1000),(50,1010),(99,1020)]),
                    T0,T0+128_391_951)
        self.assertEqual(d["status"],"CLOCK_WINDOW_UNBRACKETED_HOLD")
        self.assertFalse(d["clock_causality_proven"])
        d=summarize(obs([(-10,1000),(0,1005),(50,1004),(150,1020)]),
                    T0,T0+128_391_951)
        self.assertEqual(d["status"],"CLOCK_REWIND_OR_BAD_ORDER_HOLD")

    def test_invalid_or_unbounded_inputs_hold(self):
        self.assertEqual(summarize([{"mono_ns":"secret","sim_ns":2}],
                                   T0,T0+128_391_951)["status"],"CLOCK_INVALID_INPUT_HOLD")
        self.assertEqual(summarize(obs([(i,i) for i in range(50002)]),
                                   T0,T0+128_391_951)["status"],"CLOCK_INVALID_INPUT_HOLD")

    def test_output_contains_only_numeric_relative_timing_no_raw_passthrough(self):
        rows=obs([(-5,1000),(0,1001),(25,1003),(100,1005),
                  (128,1010),(140,1011)])
        rows[2]["frame"]="LEAK_PRIVATE_FRAME"
        d=summarize(rows,T0,T0+128_391_951)
        self.assertNotIn("LEAK_PRIVATE_FRAME",str(d))
        for item in d["samples"]:
            self.assertEqual(set(item),{"mono_rel_first_observer_ns",
                                        "sim_rel_first_probe_ns"})
            self.assertTrue(all(type(v) is int for v in item.values()))

if __name__=="__main__":
    unittest.main()
