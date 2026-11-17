"""Task01 zero-timeout TF readiness: native official TF Buffer, diagnostic only.

Never interpret one query as direct proof of first RMW source gap causality.
The pre/post calls are *outside* original getTransform timing and optional,
and do not modify official Nav2/CM/Guard parameters.
"""
import json
import unittest
from pathlib import Path

from d06.diagnostic.export_public_cm120_first_gap import export_sanitized
from d06.diagnostic.classify_tf_availability import classify
from d06.tests.test_g07_cm120_tf_first_gap_join import (
    READY, observer, trace, anchor, line
)
from d06.tests.test_g07_cm120_task01_per_sleep_span_join import poll

SHA="0123456789abcdef0123456789abcdef01234567"
ACTUAL=Path(__file__).resolve().parents[1]/"evidence/g07_cm120_task01/run_44049067368_first_gap_sanitized.json"


def probe(*, p=4242, tid=33, pre=0, post=1,
          p0=12.012, p1=12.013, q0=12.106, q1=12.107):
    return (f"TF_AVAIL pid={p} tid={tid} "
            f"mono_pre_ns={round(p0*1e9)} mono_pre_end_ns={round(p1*1e9)} "
            f"mono_post_start_ns={round(q0*1e9)} mono_post_end_ns={round(q1*1e9)} "
            f"pre_available={pre} post_available={post}")


def sample(*events):
    return export_sanitized(observer(),trace(),[
        READY,line(12.014,12.105,cpu=.0003),
        poll(12.024,12.034),poll(12.044,12.054),*events
    ],anchor(),run_id="44040000001",public_sha=SHA)


class ZeroTimeoutReadiness(unittest.TestCase):
    def test_actual_legacy_first_source_gap_is_still_unproven(self):
        actual=json.loads(ACTUAL.read_text())
        out=classify(actual)
        self.assertEqual(out["status"],"TF_AVAILABILITY_PROBE_NOT_PRESENT_HOLD")
        self.assertFalse(out["root_cause_proven"])
        self.assertFalse(out["scheduler_wait_proven"])
        self.assertFalse(out["gate_c_authorized"])

    def test_pre_unavailable_post_available_is_only_candidate(self):
        doc=sample(probe())
        self.assertEqual(len(doc["tf_availability"]["spans"]),1)
        data=doc["tf_availability"]["spans"][0]
        self.assertEqual(set(data),{
            "pre_available","post_available",
            "pre_probe_wall_ns","post_probe_wall_ns",
            "original_tf_call_wall_ns",
            "pre_start_rel_observer_ns","post_end_rel_observer_ns"})
        self.assertFalse(data["pre_available"])
        self.assertTrue(data["post_available"])
        self.assertEqual(data["pre_probe_wall_ns"],1_000_000)
        self.assertEqual(data["original_tf_call_wall_ns"],91_000_000)
        self.assertNotIn("pid",json.dumps(doc["tf_availability"]))
        self.assertNotIn("tid",json.dumps(doc["tf_availability"]))
        v=classify(doc)
        self.assertEqual(v["status"],"TF_INITIAL_UNAVAILABLE_LATER_AVAILABLE_CANDIDATE_HOLD")
        self.assertEqual(v["same_call_transition_count"],1)
        self.assertFalse(v["tf_wait_root_cause_proven"])
        self.assertFalse(v["source_publication_to_monotonic_alignment_proven"])
        self.assertFalse(v["scheduler_wait_proven"])
        self.assertFalse(v["cm120_release_pass"])

    def test_unrelated_pid_and_tid_can_not_count_as_owned_tf(self):
        doc=sample(probe(p=4243),probe(tid=34))
        self.assertNotIn("tf_availability",doc)
        self.assertEqual(classify(doc)["status"],"TF_AVAILABILITY_PROBE_NOT_PRESENT_HOLD")

    def test_probe_crossing_original_call_does_not_credit(self):
        doc=sample(probe(p1=12.016))
        self.assertEqual(classify(doc)["status"],"TF_AVAILABILITY_BOUNDARY_UNVERIFIED_HOLD")

    def test_multi_probe_per_same_call_does_not_credit(self):
        doc=sample(probe(),probe())
        self.assertEqual(classify(doc)["status"],"TF_AVAILABILITY_AMBIGUOUS_CALL_HOLD")

    def test_pre_available_with_sleep_is_not_tf_wait_proof(self):
        doc=sample(probe(pre=1,post=1))
        self.assertEqual(classify(doc)["status"],"TF_AVAILABLE_AT_ENTRY_CAUSE_UNPROVEN_HOLD")
        self.assertFalse(classify(doc)["root_cause_proven"])

    def test_conservative_original_wall_not_probe_wall(self):
        doc=sample(probe(p0=12.000,p1=12.014,q0=12.105,q1=12.118))
        # Both optional checks may be expensive; existing original official
        # TF wall must remain 91ms and cannot be inflated with probes.
        self.assertEqual(doc["tf_availability"]["spans"][0]["original_tf_call_wall_ns"],91_000_000)
        self.assertEqual(classify(doc)["status"],
                         "TF_AVAILABILITY_PROBE_TOO_SLOW_HOLD")

    def test_no_first_source_gap_must_not_claim_same_gap_availability(self):
        # Real moving #44073078458 had TF observations, but the original
        # >120ms RMW source gap was NOT reproduced. A synthetic exporter
        # must never turn a TF pre/post observation into first-gap evidence.
        doc = sample(probe())
        doc["first_gap"] = None
        got = classify(doc)
        self.assertEqual(got["status"], "FIRST_SOURCE_GAP_NOT_REPRODUCED_HOLD")
        self.assertFalse(got["root_cause_proven"])
        self.assertFalse(got["gate_c_authorized"])
        self.assertFalse(got["cm120_release_pass"])

    def test_subthreshold_source_interval_must_not_claim_same_gap_availability(self):
        doc = sample(probe())
        doc["first_gap"]["rmw_source_gap_ns"] = 117_998_000
        got = classify(doc)
        self.assertEqual(got["status"], "FIRST_SOURCE_GAP_NOT_REPRODUCED_HOLD")
        self.assertFalse(got["root_cause_proven"])

    def test_other_callback_availability_is_not_first_observer_pair(self):
        # The public exporter accepts bounded nearby TF calls (±200ms)
        # to preserve evidence. A DIFFERENT native CM callback in that
        # neighborhood must not become first-pair TF readiness causality.
        # Real source gap fixture: observer pair [12.000, 12.132].
        from d06.tests.test_g07_cm120_tf_first_gap_join import cb
        for t0, t1, p0, p1, q0, q1 in (
            (11.864, 11.955, 11.862, 11.863, 11.956, 11.957),
            (12.160, 12.240, 12.158, 12.159, 12.241, 12.242),
        ):
            with self.subTest(tf_start=t0):
                other_callback = [
                    cb("ros2:callback_start", t0 - .003),
                    cb("ros2:callback_end", t1 + .003),
                ]
                doc = export_sanitized(
                    observer(), trace() + other_callback,
                    [READY, line(t0, t1, cpu=.0003),
                     probe(p0=p0, p1=p1, q0=q0, q1=q1)],
                    anchor(), run_id="44040000001", public_sha=SHA)
                self.assertEqual(
                    doc["tf_availability"]["status"],
                    "TF_AVAILABILITY_READ_ONLY_RECORDED_HOLD")
                self.assertEqual(
                    classify(doc)["status"],
                    "TF_AVAILABILITY_OUTSIDE_FIRST_OBSERVER_PAIR_HOLD")
                self.assertFalse(classify(doc)["gate_c_authorized"])

if __name__=="__main__":
    unittest.main()
