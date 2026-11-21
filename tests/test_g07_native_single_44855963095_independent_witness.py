"""Same-session real Gazebo native L2 #44855963095 first 377ms CM gap.
Read original independent witness as a distinct ROS subscriber /host monotonic;
never call an absent DDS publication sequence proof. Fail closed unchanged.
"""
import json
from pathlib import Path
import unittest
from d06.diagnostic.g07_independent_cm_rmw_witness import (
    compare_same_cm_pair, normalize_witness_metadata)

DATA=json.loads((Path(__file__).parent/"fixtures"/
                  "g07_native_single_44855963095_first_gap.json").read_text())

class DistinctWitnessFirstGap(unittest.TestCase):
    def test_same_session_independent_callback_continued_while_single_observer_blocked(self):
        first=DATA["first_cm_observer_pair"]
        a=1_799_000_000_000_000_000
        original=[
            dict(kind="pre_guard",t=first["previous_rx_monotonic"],
                 rmw_source_ns=a,rmw_received_ns=a+300000,
                 rmw_publication_seq=700),
            dict(kind="pre_guard",t=first["current_rx_monotonic"],
                 rmw_source_ns=a+52_640_339,
                 rmw_received_ns=a+378_384_177,
                 rmw_publication_seq=701)]
        independent=[dict(kind="pre_guard",t=t,rmw_source_ns=-1,
                          rmw_received_ns=-1,rmw_publication_seq=-1)
                     for t in DATA["independent_cm_callback_host_monotonic"]]
        r=compare_same_cm_pair(original,independent,
                               first["previous_rx_monotonic"],
                               first["current_rx_monotonic"])
        self.assertEqual(r["status"],"INDEPENDENT_CM_CALLBACKS_CONTINUED_EXACT_PAIR_UNVERIFIED_HOLD")
        self.assertEqual(r["independent_host_callback_count_inside_gap"],7)
        self.assertLess(r["independent_max_callback_interval_ms"],70)
        self.assertFalse(r["original_executor_root_proven"])
        self.assertFalse(r["transport_root_proven"])
        self.assertIsNone(r["matched_publication_seq_gap"])
        self.assertEqual(r["release"],"HOLD")

    def test_missing_publication_seq_does_not_destroy_valid_rmw_stamps(self):
        class Info:
            source_timestamp=1_799_000_000_000_000_000
            received_timestamp=1_799_000_000_003_000_000
        src,rx,seq=normalize_witness_metadata(Info())
        self.assertEqual(src,Info.source_timestamp)
        self.assertEqual(rx,Info.received_timestamp)
        self.assertEqual(seq,-1)

    def test_no_independent_coverage_cannot_claim_continuity(self):
        a=1_799_000_000_000_000_000
        original=[dict(kind="pre_guard",t=1.,rmw_source_ns=a,rmw_received_ns=a+1,rmw_publication_seq=1),
                  dict(kind="pre_guard",t=1.38,rmw_source_ns=a+40_000_000,
                       rmw_received_ns=a+375_000_000,rmw_publication_seq=2)]
        bad=[dict(kind="pre_guard",t=1.04,rmw_source_ns=-1,
                  rmw_received_ns=-1,rmw_publication_seq=-1)]
        r=compare_same_cm_pair(original,bad,1.,1.38)
        self.assertEqual(r["status"],"INDEPENDENT_CM_EXACT_PAIR_NOT_VERIFIED_HOLD")
        self.assertFalse(r["root_cause_proven"])

if __name__=="__main__":
    unittest.main()
