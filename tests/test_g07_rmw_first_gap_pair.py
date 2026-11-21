"""Read-only RMW source/receive versus Observer callback FIRST gap.

All test rows synthetic; actual same-session first pair joins only on exact
callback times and consecutive RMW seq. Never equates system and steady epochs,
never relaxes CM120/Guard150/Scan/Odom/Clock300, never proves Guard TTL root.
"""
import json
from pathlib import Path
import unittest
from d06.diagnostic.g07_first_actual_delivery_gap import classify_rmw_first_pair


def make(source_gap_ms, rmw_rx_gap_ms, callback_gap_ms=370, seq=(8,9)):
    a=1_780_000_000_000_000_000
    b=a+source_gap_ms*1_000_000
    r=a+1_000_000
    p={"channel":"pre_guard","previous_rx_monotonic":10.,
       "current_rx_monotonic":10.+callback_gap_ms/1000,
       "gap_ms":callback_gap_ms,"limit_ms":120}
    rows=[
      {"kind":"pre_guard","t":10.,"rmw_publication_seq":seq[0],
       "rmw_source_ns":a,"rmw_received_ns":r},
      {"kind":"pre_guard","t":p["current_rx_monotonic"],
       "rmw_publication_seq":seq[1],"rmw_source_ns":b,
       "rmw_received_ns":r+rmw_rx_gap_ms*1_000_000},
    ]
    return rows,p


class FirstActualRmwVsCallback(unittest.TestCase):
    def test_source_gap_candidate_not_root_proof(self):
        rows,p=make(350,355)
        v=classify_rmw_first_pair(rows,p)
        self.assertEqual(v["status"],"RMW_SOURCE_PERIOD_GAP_CANDIDATE")
        self.assertEqual(v["rmw_source_gap_ms"],350)
        self.assertEqual(v["callback_gap_ms"],370)
        self.assertFalse(v["root_cause_proven"])
        self.assertEqual(v["release"],"HOLD")

    def test_different_delivery_gap_candidate_not_source(self):
        rows,p=make(50,350)
        v=classify_rmw_first_pair(rows,p)
        self.assertEqual(v["status"],"RMW_RECEIPT_GAP_CANDIDATE")
        self.assertLess(v["rmw_source_gap_ms"],120)
        self.assertFalse(v["publisher_stall_proven"])

    def test_callback_only_gap_candidate_not_dds_root(self):
        rows,p=make(50,55)
        v=classify_rmw_first_pair(rows,p)
        self.assertEqual(v["status"],"OBSERVER_CALLBACK_GAP_CANDIDATE")
        self.assertFalse(v["rmw_transport_root_proven"])

    def test_missing_metadata_or_sequence_discontinuity_holds(self):
        rows,p=make(50,50)
        rows[1].pop("rmw_received_ns")
        self.assertEqual(classify_rmw_first_pair(rows,p)["status"],
                         "RMW_FIRST_PAIR_UNVERIFIED")
        rows,p=make(50,50,seq=(8,11))
        self.assertEqual(classify_rmw_first_pair(rows,p)["status"],
                         "RMW_SEQUENCE_DISCONTINUITY_HOLD")

    def test_backward_rmw_clock_step_is_not_a_delay_proof(self):
        rows,p=make(-6600,-6600)
        self.assertEqual(classify_rmw_first_pair(rows,p)["status"],
                         "RMW_TIMEBASE_REGRESSION_HOLD")

    def test_unknown_channel_or_unmatched_callbacks_fail_closed(self):
        rows,p=make(50,55)
        self.assertEqual(classify_rmw_first_pair([],p)["status"],
                         "RMW_FIRST_PAIR_UNVERIFIED")
        p["current_rx_monotonic"]=9.0
        self.assertEqual(classify_rmw_first_pair(rows,p)["status"],
                         "RMW_FIRST_PAIR_UNVERIFIED")


    def test_actual_44683741133_first_rmw_receipt(self):
        """Actual native Moving CI derived intervals, not invented RMW epochs."""
        path=Path(__file__).parent/"fixtures/g07_44683741133_first_rmw_receipt.json"
        v=json.loads(path.read_text())
        self.assertEqual(v["run_id"],44683741133)
        self.assertEqual(v["job_id"],136113019310)
        self.assertEqual(v["first_violation"]["channel"],"odom")
        self.assertAlmostEqual(v["rmw"]["source_gap_ms"],48.499371,places=5)
        self.assertAlmostEqual(v["rmw"]["received_gap_ms"],356.887562,places=5)
        self.assertAlmostEqual(v["rmw"]["callback_gap_ms"],362.069145,places=5)
        self.assertEqual(v["rmw"]["publication_seq_gap"],1)
        self.assertEqual(v["rmw"]["status"],"RMW_RECEIPT_GAP_CANDIDATE")
        self.assertFalse(v["rmw"]["publisher_stall_proven"])
        self.assertFalse(v["rmw"]["rmw_transport_root_proven"])
        self.assertFalse(v["first_guard_latch_proven"])
        self.assertEqual(v["status"],"HOLD_FIRST_ACTUAL_RMW_RECEIPT_GAP")
        self.assertEqual(v["release"],"HOLD")


if __name__=="__main__":
    unittest.main()
