"""Task01: same-run clock sample only as relative numeric public artifact."""
import json
import unittest

from d06.diagnostic.export_public_cm120_first_gap import export_sanitized
from d06.tests.test_g07_cm120_tf_first_gap_join import observer, trace, anchor, READY, line
from d06.tests.test_g07_cm120_task01_per_sleep_span_join import poll

SHA="0123456789abcdef0123456789abcdef01234567"


def raw():
    t=12_000_000_000
    sim=1_000_000_000
    samples=[]
    for ms,sms in ((-10,0),(0,1),(30,2),(60,4),(90,7),
                   (125,8),(135,9)):
        samples.append(dict(mono_ns=t+ms*1_000_000,
                            sim_ns=sim+sms*1_000_000,
                            private_ros_message="LEAK_SEALED_CLOCK_MESSAGE"))
    return samples


def evidence(samples):
    return export_sanitized(observer(),trace(),[
        READY,line(12.014,12.105),poll(12.024,12.034),
        poll(12.044,12.054)],anchor(),
        run_id="44040000001",public_sha=SHA,clock_rows=samples)


class PublicClockProbeExport(unittest.TestCase):
    def test_sanitized_clock_progress_is_numeric_only(self):
        result=evidence(raw())
        clk=result["clock_progress"]
        self.assertEqual(clk["status"],"CLOCK_OBSERVER_WINDOW_BRACKETED_HYPOTHESIS_ONLY")
        self.assertLess(clk["sim_to_wall_progress_ratio"],0.20)
        self.assertEqual(clk["observer_pair_clock_sample_count"],5)
        self.assertNotIn("LEAK_SEALED_CLOCK_MESSAGE",json.dumps(result))
        self.assertFalse(result["root_cause_proven"])
        self.assertFalse(result["gate_c_authorized"])
        self.assertFalse(result["source_publication_to_monotonic_alignment_proven"])
        self.assertFalse(result["cm120_release_pass"])

    def test_not_enough_clock_samples_holds_not_release(self):
        result=evidence(raw()[2:4])
        self.assertEqual(result["clock_progress"]["status"],"CLOCK_WINDOW_UNBRACKETED_HOLD")
        self.assertFalse(result["clock_progress"]["tf_buffer_clock_progress_proven"])
        self.assertFalse(result["cm120_release_pass"])

    def test_invalid_clock_rewind_is_not_silent_success(self):
        rows=raw()
        rows[3]["sim_ns"]=rows[2]["sim_ns"]-2
        result=evidence(rows)
        self.assertEqual(result["clock_progress"]["status"],"CLOCK_REWIND_OR_BAD_ORDER_HOLD")
        self.assertFalse(result["root_cause_proven"])

    def test_existing_no_clock_legacy_export_is_unchanged(self):
        a=export_sanitized(observer(),trace(),[READY,line(12.014,12.105)],
            anchor(),run_id="44040000001",public_sha=SHA)
        self.assertNotIn("clock_progress",a)
        self.assertFalse(a["cm120_release_pass"])

if __name__=="__main__":
    unittest.main()
