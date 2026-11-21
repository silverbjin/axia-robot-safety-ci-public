"""Fail-closed RMW message-info readiness before claiming first-pair attribution.

This only checks whether the *already enabled* Jazzy Observer metadata
path supplied enough bounded, same-host evidence; it is NOT a source proof.
"""
import unittest
from d06.diagnostic.g07_first_actual_delivery_gap import summarize_rmw_readiness


def info(kind,t,seq):
    src=1_780_000_000_000_000_000+int(t*1e9)
    return {"kind":kind,"t":t,"rmw_source_ns":src,
            "rmw_received_ns":src+2_000_000,
            "rmw_publication_seq":seq}


class ExactRmwReadiness(unittest.TestCase):
    def test_both_existing_subscriptions_have_real_message_info(self):
        rows=[info("pre_guard",1.0,1),info("supervised",1.0,7),
              info("pre_guard",1.05,2),info("supervised",1.05,8)]
        v=summarize_rmw_readiness(rows)
        self.assertEqual(v["status"],"RMW_TWO_TOPICS_METADATA_READY")
        self.assertEqual(v["pre_guard_valid_consecutive_pairs"],1)
        self.assertEqual(v["supervised_valid_consecutive_pairs"],1)
        self.assertFalse(v["first_boundary_proven"])
        self.assertEqual(v["release"],"HOLD")

    def test_missing_seq_and_received_timestamp_must_be_explicit(self):
        rows=[info("pre_guard",1.,1),info("supervised",1.,1)]
        rows.append(info("pre_guard",1.05,2))
        rows[-1]["rmw_publication_seq"]=None
        rows.append(info("supervised",1.05,2))
        rows[-1].pop("rmw_received_ns")
        v=summarize_rmw_readiness(rows)
        self.assertEqual(v["status"],"RMW_METADATA_INSUFFICIENT_HOLD")
        self.assertEqual(v["pre_guard_valid_consecutive_pairs"],0)
        self.assertEqual(v["supervised_valid_consecutive_pairs"],0)
        self.assertEqual(v["missing_or_unusable_samples"],2)

    def test_discontinuous_publication_sequence_never_ready(self):
        rows=[info("pre_guard",1.,8),info("pre_guard",1.05,12),
              info("supervised",1.,2),info("supervised",1.05,7)]
        v=summarize_rmw_readiness(rows)
        self.assertEqual(v["status"],"RMW_METADATA_INSUFFICIENT_HOLD")
        self.assertEqual(v["pre_guard_valid_consecutive_pairs"],0)
        self.assertEqual(v["supervised_valid_consecutive_pairs"],0)
        self.assertEqual(v["sequence_discontinuities"],2)

    def test_empty_not_safety_pass(self):
        v=summarize_rmw_readiness([])
        self.assertEqual(v["status"],"RMW_METADATA_INSUFFICIENT_HOLD")
        self.assertEqual(v["release"],"HOLD")
        self.assertFalse(v["root_cause_proven"])


if __name__=="__main__":
    unittest.main()
