"""D08 existing isolated scan witness pattern applied to G07 real CM sample.

Only numeric timestamps/sequence, never message payload or publisher GID.
Compare exact first Observer CM pair against independent ROS process with
separate DDS participant, same host-monotonic domain and same sample seq.
"""
import unittest
from d06.diagnostic.g07_independent_cm_rmw_witness import BoundedCmEvidence, compare_same_cm_pair


def packet(t,src,rx,seq):
    return {"kind":"pre_guard","t":t,
            "rmw_source_ns":src,"rmw_received_ns":rx,
            "rmw_publication_seq":seq}


class IndependentRmwPair(unittest.TestCase):
    def test_two_process_same_pub_seq_original_only_gap(self):
        a=1_799_000_000_000_000_000
        original=[packet(10.,a,a+1_000_000,41),
                  packet(10.36,a+50_000_000,a+356_000_000,42)]
        isolated=[packet(10.001,a,a+2_000_000,41),
                  packet(10.052,a+50_000_000,a+52_000_000,42)]
        v=compare_same_cm_pair(original,isolated,10.,10.36)
        self.assertEqual(v["status"],"ORIGINAL_PROCESS_RECEIPT_GAP_CANDIDATE")
        self.assertAlmostEqual(v["original_receive_gap_ms"],355.,places=3)
        self.assertAlmostEqual(v["independent_receive_gap_ms"],50.,places=3)
        self.assertEqual(v["matched_publication_seq_gap"],1)
        self.assertFalse(v["root_cause_proven"])
        self.assertEqual(v["release"],"HOLD")

    def test_both_processes_gap_means_shared_boundary_not_dds_proven(self):
        a=1_799_000_000_000_000_000
        original=[packet(10.,a,a+1_000_000,41),
                  packet(10.36,a+50_000_000,a+356_000_000,42)]
        isolated=[packet(10.002,a,a+2_000_000,41),
                  packet(10.354,a+50_000_000,a+351_000_000,42)]
        v=compare_same_cm_pair(original,isolated,10.,10.36)
        self.assertEqual(v["status"],"TWO_PROCESS_RECEIPT_GAP_CANDIDATE")
        self.assertFalse(v["transport_root_proven"])

    def test_unmatched_seqs_and_source_stamps_must_hold(self):
        a=1_799_000_000_000_000_000
        original=[packet(10.,a,a+1_000_000,41),
                  packet(10.36,a+50_000_000,a+356_000_000,42)]
        ind=[packet(10.,a,a+2_000_000,11),
             packet(10.05,a+50_000_000,a+53_000_000,12)]
        self.assertEqual(compare_same_cm_pair(original,ind,10.,10.36)["status"],
                         "INDEPENDENT_CM_EXACT_PAIR_NOT_VERIFIED_HOLD")
        ind=[packet(10.,a+1,a+2_000_000,41),
             packet(10.05,a+50_000_000,a+53_000_000,42)]
        self.assertEqual(compare_same_cm_pair(original,ind,10.,10.36)["status"],
                         "INDEPENDENT_CM_EXACT_PAIR_NOT_VERIFIED_HOLD")

    def test_no_samples_are_never_release(self):
        self.assertEqual(compare_same_cm_pair([],[],0.,1.)["release"],"HOLD")

    def test_bounded_no_callback_io(self):
        v=BoundedCmEvidence(max_samples=3)
        for seq in range(1,7):
            v.add(packet(seq*.05,1_799_000_000_000_000_000+seq,
                         1_799_000_000_000_010_000+seq,seq))
        self.assertEqual(len(v.rows),3)
        self.assertEqual(v.dropped,3)
        self.assertEqual(v.rows[0]["rmw_publication_seq"],4)


if __name__=="__main__":
    unittest.main()
