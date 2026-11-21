"""G07 exact native #44859905000: independent witness lost RMW metadata.

Main Observer normalizer accepts rclpy two-argument MessageInfo **dict**.
Independent read-only witness incorrectly used getattr(info, ...), so all
291 witness rows had src/received/sequence=-1. Fix only evidence decoding,
not DDS/CM/Guard/Goal, and never infer an L3 pass from valid metadata.
"""
import unittest
from d06.diagnostic.g07_independent_cm_rmw_witness import (
    normalize_witness_metadata, compare_same_cm_pair)


class JazzyTwoArgMessageInfoDict(unittest.TestCase):
    def test_actual_jazzy_dict_source_received_sequence_retained(self):
        src=1_795_000_000_000_000_000
        info={"source_timestamp":src,
              "received_timestamp":src+2_500_000,
              "publication_sequence_number":180}
        self.assertEqual(normalize_witness_metadata(info),
                         (src,src+2_500_000,180))

    def test_seq_unavailable_preserves_only_valid_two_timestamps(self):
        src=1_795_000_000_000_000_000
        info={"source_timestamp":src,
              "received_timestamp":src+4_000_000,
              "publication_sequence_number":None}
        self.assertEqual(normalize_witness_metadata(info),
                         (src,src+4_000_000,-1))
        self.assertEqual(normalize_witness_metadata({}),(-1,-1,-1))

    def test_independent_exact_same_pub_pair_after_dict_decode_remains_hold(self):
        base=1_795_000_000_000_000_000
        def row(t,recv_delta,seq,sent_delta):
            src,rx,n=normalize_witness_metadata({
                "source_timestamp":base+sent_delta,
                "received_timestamp":base+recv_delta,
                "publication_sequence_number":seq})
            return dict(kind="pre_guard",t=t,rmw_source_ns=src,
                        rmw_received_ns=rx,rmw_publication_seq=n)
        original=[row(10,1_000_000,180,0),
                  row(10.37,370_000_000,181,50_000_000)]
        witness=[row(10.01,2_000_000,180,0),
                 row(10.06,52_000_000,181,50_000_000)]
        r=compare_same_cm_pair(original,witness,10,10.37)
        self.assertEqual(r["status"],"ORIGINAL_PROCESS_RECEIPT_GAP_CANDIDATE")
        self.assertAlmostEqual(r["original_receive_gap_ms"],369,places=2)
        self.assertAlmostEqual(r["independent_receive_gap_ms"],50,places=2)
        self.assertEqual(r["matched_publication_seq_gap"],1)
        self.assertEqual(r["release"],"HOLD")
        self.assertFalse(r["root_cause_proven"])


if __name__=="__main__":
    unittest.main()
