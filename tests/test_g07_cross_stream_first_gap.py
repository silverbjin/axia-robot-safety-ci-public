"""Actual #44674827354 first Clock300 breach and multi-topic read-only join.

Synthetic records test analysis logic. Original CI first Clock pair is
field-derived but does not include the other channels' exact first pairs;
we must never reclassify a shared max-gap list into a proven common cause.
"""
import json
from pathlib import Path
import unittest
from d06.diagnostic.g07_first_actual_delivery_gap import classify


def rows(channels, *, gap_from=200., gap_to=200.37):
    events=[{"kind":"owner_goal_published","t":199.0}]
    for channel in channels:
        events.extend({"kind":channel,"t":t} for t in
                      (199.8,199.9,gap_from,gap_to,gap_to+.05))
    return sorted(events,key=lambda x:x["t"])


class FirstRealDeliveryGap(unittest.TestCase):
    def test_simultaneous_multi_stream_gap_is_candidate_never_root_proof(self):
        channels=["clock","scan","odom","pre_guard","supervised","guard","supervisor"]
        v=classify(rows(channels),start=199.0,end=201.0)
        self.assertEqual(v["status"],"CROSS_STREAM_GAP_CANDIDATE_HOLD")
        self.assertEqual(v["first_violation"]["channel"],"pre_guard")
        self.assertEqual(set(v["cross_stream_breaches"]),set(channels))
        self.assertFalse(v["publisher_delay_proven"])
        self.assertFalse(v["observer_scheduling_delay_proven"])
        self.assertEqual(v["release"],"HOLD")

    def test_single_channel_is_not_whole_chain_failure_proof(self):
        v=classify(rows(["clock"]),start=199.0,end=201.0)
        self.assertEqual(v["status"],"SINGLE_STREAM_GAP_HOLD")
        self.assertFalse(v["root_cause_proven"])

    def test_missing_pairs_cannot_relabel_real_failure(self):
        fixture=Path(__file__).parent/"fixtures/g07_44674827354_cycle2_first_gap.json"
        r=json.loads(fixture.read_text())
        self.assertEqual(r["first_violation"]["channel"],"clock")
        self.assertAlmostEqual(r["first_violation"]["duration_ms"],334.182029,places=4)
        self.assertGreater(r["max_gaps_ms"]["cm"],120.)
        self.assertGreater(r["max_gaps_ms"]["guard"],150.)
        self.assertFalse(r["cross_stream_first_pairs_available"])
        self.assertEqual(r["root_cause"],"UNDETERMINED")
        self.assertEqual(r["status"],"HOLD_FIRST_CLOCK300")
        v=classify([{"kind":"clock","t":r["first_violation"]["end_monotonic"]}],
                   start=r["first_violation"]["start_monotonic"],
                   end=r["first_violation"]["end_monotonic"]+.01)
        self.assertEqual(v["status"],"FIRST_DELIVERY_BOUNDARY_NOT_VERIFIED_HOLD")

    def test_out_of_order_and_empty_no_pass(self):
        self.assertEqual(classify([],start=1,end=2)["status"],
                         "FIRST_DELIVERY_BOUNDARY_NOT_VERIFIED_HOLD")
        self.assertEqual(classify(rows(["clock"]),start=201,end=199)["status"],
                         "FIRST_DELIVERY_BOUNDARY_NOT_VERIFIED_HOLD")


if __name__=="__main__":
    unittest.main()
