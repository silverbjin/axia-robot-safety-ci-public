"""Task01 same exact official TF call sleep-budget; no fake scheduler proof.

Old actual #44049067368 has only aggregate TF durations: must remain HOLD.
Synthetic calls demonstrate a future bounded numeric-only CI artifact contract.
"""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from d06.diagnostic.classify_exact_tf_sleep_budget import classify_call_budget
from d06.diagnostic.export_public_cm120_first_gap import export_sanitized
from d06.tests.test_g07_cm120_tf_first_gap_join import (
    READY, observer, trace, anchor, line
)
from d06.tests.test_g07_cm120_task01_per_sleep_span_join import poll

SHA="0123456789abcdef0123456789abcdef01234567"
ACTUAL=Path(__file__).resolve().parents[1]/"evidence/g07_cm120_task01/run_44049067368_first_gap_sanitized.json"


def advanced_sleep_line(count=2, end=12.105):
    base=line(12.014,end,cpu=.0003)
    return (base+" schedstat_valid=0 runqueue_ns=0 sched_cpu_ns=0"
            " voluntary_cs=2 involuntary_cs=0"
            " sleep_ns=20000000 sleep_calls="+str(count))


def synthetic_export(count=2):
    return export_sanitized(observer(),trace(),[
        READY,advanced_sleep_line(count),
        poll(12.024,12.034),poll(12.044,12.054)],anchor(),
        run_id="44040000001",public_sha=SHA)


class ExactTfCallSleepBudget(unittest.TestCase):
    def test_real_legacy_artifact_fails_closed_without_call_boundaries(self):
        doc=json.loads(ACTUAL.read_text(encoding="utf-8"))
        v=classify_call_budget(doc)
        self.assertEqual(v["status"],"EXACT_TF_CALL_INTERVALS_NOT_PRESERVED_HOLD")
        self.assertFalse(v["root_cause_proven"])
        self.assertFalse(v["tf_buffer_wait_proven"])
        self.assertFalse(v["scheduler_runqueue_wait_proven"])
        self.assertFalse(v["gate_c_authorized"])

    def test_synthetic_call_boundaries_and_sleep_count_proven_only_inside_tf(self):
        doc=synthetic_export()
        self.assertEqual(len(doc["tf_calls"]["spans"]),1)
        call=doc["tf_calls"]["spans"][0]
        self.assertEqual(set(call),{
            "start_rel_observer_ns","end_rel_observer_ns",
            "thread_cpu_ns","sleep_count_declared","sleep_count_observed",
            "sleep_request_ns","sleep_wall_ns","coverage_complete"})
        self.assertEqual(call["sleep_count_declared"],2)
        self.assertEqual(call["sleep_count_observed"],2)
        self.assertEqual(call["sleep_request_ns"],20_000_000)
        self.assertTrue(call["coverage_complete"])
        v=classify_call_budget(doc)
        self.assertEqual(v["status"],"EXACT_TF_CALL_SLEEP_BUDGET_OBSERVED_CAUSALITY_HOLD")
        self.assertEqual(v["calls_with_complete_sleep_provenance"],1)
        self.assertFalse(v["source_publication_to_monotonic_alignment_proven"])
        self.assertFalse(v["tf_buffer_wait_proven"])
        self.assertFalse(v["scheduler_runqueue_wait_proven"])
        self.assertFalse(v["cm120_release_pass"])
        self.assertNotIn("pid",json.dumps(doc))
        self.assertNotIn("tid",json.dumps(doc))

    def test_declared_sleep_count_mismatch_does_not_get_coverage_credit(self):
        doc=synthetic_export(count=3)
        self.assertFalse(doc["tf_calls"]["spans"][0]["coverage_complete"])
        self.assertFalse(doc["tf_sleep"]["coverage_proven"])
        v=classify_call_budget(doc)
        self.assertEqual(v["status"],"TF_SLEEP_PER_CALL_COVERAGE_INCOMPLETE_HOLD")
        self.assertFalse(v["root_cause_proven"])

    def test_missing_time_spans_or_wrong_nested_call_cannot_be_proven(self):
        doc=synthetic_export()
        a=deepcopy(doc)
        a["tf_calls"]["spans"][0]["start_rel_observer_ns"]=24_100_000
        self.assertEqual(classify_call_budget(a)["status"],"TF_SLEEP_OUTSIDE_EXACT_CALL_HOLD")
        b=deepcopy(doc)
        b["tf_calls"]["spans"][0]["end_rel_observer_ns"]=10_000_000
        self.assertEqual(classify_call_budget(b)["status"],"TF_CALL_INTERVAL_INVALID_HOLD")
        c=deepcopy(doc)
        c["tf_calls"]["spans"].append(dict(c["tf_calls"]["spans"][0]))
        self.assertEqual(classify_call_budget(c)["status"],"TF_CALL_COUNT_MISMATCH_HOLD")

    def test_fabricated_call_with_nine_sleeps_is_conditional_not_actual_proof(self):
        doc=synthetic_export()
        real=json.loads(ACTUAL.read_text(encoding="utf-8"))
        spans=[x for x in real["tf_sleep"]["spans"]
               if 0<=x["start_rel_observer_ns"]
               and x["end_rel_observer_ns"]<=real["first_gap"]["observer_gap_ns"]]
        self.assertEqual(len(spans),9)
        doc["tf_sleep"]["spans"]=deepcopy(spans)
        doc["tf_sleep"]["count"]=9
        doc["tf_calls"]["spans"]=[{
            "start_rel_observer_ns":34_000_000,
            "end_rel_observer_ns":125_732_660,
            "thread_cpu_ns":388_890,
            "sleep_count_declared":9,"sleep_count_observed":9,
            "sleep_request_ns":90_000_000,
            "sleep_wall_ns":91_416_406,
            "coverage_complete":True}]
        doc["tf_calls"]["count"]=1
        doc["tf_calls"]["durations_ms"]=[91.73266]
        v=classify_call_budget(doc)
        self.assertEqual(v["status"],"EXACT_TF_CALL_SLEEP_BUDGET_OBSERVED_CAUSALITY_HOLD")
        self.assertEqual(v["requested_sleep_lower_bound_ns"],90_000_000)
        self.assertEqual(v["nonrequested_wall_upper_bound_ns"],1_732_660)
        self.assertEqual(v["sleep_wakeup_excess_ns"],1_416_406)
        self.assertGreater(v["requested_sleep_wall_fraction"],.98)
        self.assertFalse(v["tf_buffer_wait_proven"])
        self.assertFalse(v["scheduler_runqueue_wait_proven"])
        self.assertFalse(v["root_cause_proven"])
        # This is SYNTHETIC call assignment, NOT recovered raw 440490.
        self.assertEqual(real["tf_calls"].get("spans"),None)

    def test_release_and_provenance_flags_never_promote_from_diagnostic(self):
        doc=synthetic_export()
        doc["cm120_release_pass"]=True
        self.assertEqual(classify_call_budget(doc)["status"],
                         "DIAGNOSTIC_RELEASE_FLAG_INVALID_HOLD")


if __name__=="__main__":
    unittest.main()
