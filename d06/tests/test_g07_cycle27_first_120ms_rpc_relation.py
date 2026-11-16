"""G07 Cycle27: first 120ms CM output gap versus native STOP RPC.

Actual CI #43799429562: CM 140.668ms with 3 upstream messages. The prior
150ms-only RPC classifier missed the 120..150ms release failure. This
test fixes the diagnostic blind spot; NO ROS / GUI / Goal or safety changes.
"""
import unittest
from d06.live.g07_cycle27_first120_rpc_relation import classify

def evt(kind,t,src_ms,seq):
    return {"kind":kind,"t":t,"rmw_source_ns":1700000000000000000+round(src_ms*1000000),
            "rmw_received_ns":1700000000000400000+round(src_ms*1000000),
            "rmw_publication_seq":seq}

def fixture(rpc_start=10.30,rpc_end=10.41):
    events=[{"kind":"owner_goal_published","t":9.0},
      evt("pre_guard",10.00,100.0,11),
      evt("pre_guard",10.140667774,240.667774,12),
      evt("supervised",10.015,121.0,101),
      evt("supervised",10.060,171.0,102),
      evt("supervised",10.110,221.0,103)]
    report={"stop_native_rpc_monotonic_window":
        {"started_at":rpc_start,"ended_at":rpc_end},
        "first_guard_latch":None}
    return events,report

class FirstReleaseGapVsStopRPC(unittest.TestCase):
    def test_real_140ms_gap_after_native_stop_rpc_not_accidentally_passed(self):
        events,report=fixture(9.50,9.65)
        r=classify(events,report)
        self.assertEqual(r["status"],"CM_SOURCE_120MS_GAP_AFTER_RPC_HOLD")
        self.assertAlmostEqual(r["first_cm_source_gap_ms"],140.667774,places=4)
        self.assertEqual(r["upstream_publications_inside_gap"],3)
        self.assertEqual(r["cm_publication_seq_delta"],1)
        self.assertFalse(r["native_stop_rpc_overlap_candidate"])
        self.assertFalse(r["owner_goal_authorized"])
        self.assertFalse(r["cm_input_callback_cause_proven"])

    def test_same_gap_overlaps_rpc_is_candidate_not_causal_proof(self):
        events,report=fixture(10.03,10.08)
        r=classify(events,report)
        self.assertEqual(r["status"],"CM_SOURCE_120MS_GAP_OVERLAPS_RPC_HOLD")
        self.assertTrue(r["native_stop_rpc_overlap_candidate"])
        self.assertFalse(r["rpc_caused_cm_gap_proven"])
        self.assertFalse(r["owner_goal_authorized"])

    def test_same_gap_before_rpc_is_explicit(self):
        events,report=fixture(10.35,10.45)
        r=classify(events,report)
        self.assertEqual(r["status"],"CM_SOURCE_120MS_GAP_BEFORE_RPC_HOLD")
        self.assertGreater(r["native_rpc_nearest_distance_ms"],0)

    def test_under120_real_gap_is_not_owner_acceptance(self):
        e,report=fixture()
        e[2]["rmw_source_ns"]=e[1]["rmw_source_ns"]+100000000
        r=classify(e,report)
        self.assertEqual(r["status"],"NO_CM_120MS_SOURCE_GAP_SCOPED_CI_ONLY")
        self.assertFalse(r["owner_goal_authorized"])
        self.assertFalse(r["owner_l3_accepted"])

    def test_missing_rpc_or_step_like_other_pub_is_unverified(self):
        e,r=fixture()
        r={}
        self.assertEqual(classify(e,r)["status"],"CM_SOURCE_120MS_GAP_RPC_WINDOW_MISSING_HOLD")
        e,r=fixture()
        e.append(evt("supervised",10.13,110.0,104))  # negative source or seq confusion
        self.assertEqual(classify(e,r)["status"],"RMW_SEQUENCE_OR_CLOCK_DOMAIN_UNVERIFIED_HOLD")

    def test_no_actual_goal_or_no_supervisor_coverage_fails_closed(self):
        e,r=fixture()
        self.assertEqual(classify(e[1:],r)["status"],"GOAL_MARKER_MISSING_HOLD")
        self.assertEqual(classify(e[:3],r)["status"],"SUPERVISOR_COVERAGE_UNVERIFIED_HOLD")

    def test_non_rmw_events_after_goal_cannot_hide_valid_first_gap(self):
        events,report=fixture(10.30,10.41)
        events.append({"kind":"pre_guard","t":10.5,"rmw_source_ns":None})
        events.append({"kind":"supervised","t":10.6,"rmw_publication_seq":None})
        report["cm_first_120ms_rmw_release_margin"]={
            "status":"CM_SOURCE_GAP_EXCEEDS_120MS",
            "cm_source_gap_sec":.140667774,
            "upstream_publications_inside_gap":3}
        r=classify(events,report,require_oracle=True)
        self.assertEqual(r["status"],"CM_SOURCE_120MS_GAP_BEFORE_RPC_HOLD")
        self.assertEqual(r["skipped_incomplete_rmw_rows"],2)
        self.assertTrue(r["scoped_original_oracle_gap_matched"])
        self.assertFalse(r["owner_goal_authorized"])

    def test_scoped_oracle_mismatch_or_missing_fails_closed(self):
        events,report=fixture()
        r=classify(events,report,require_oracle=True)
        self.assertEqual(r["status"],"ORIGINAL_GOAL_SCOPED_ORACLE_UNVERIFIED_HOLD")
        report["cm_first_120ms_rmw_release_margin"]={
            "status":"CM_SOURCE_GAP_EXCEEDS_120MS",
            "cm_source_gap_sec":.121,
            "upstream_publications_inside_gap":3}
        r=classify(events,report,require_oracle=True)
        self.assertEqual(r["status"],"ORIGINAL_GOAL_SCOPED_ORACLE_MISMATCH_HOLD")
        self.assertFalse(r["owner_goal_authorized"])

    def test_no_private_origin_in_diagnostic(self):
        e,r=fixture()
        out=classify(e,r)
        self.assertFalse(out["certified_estop"])
        self.assertFalse(out["owner_goal_authorized"])
        self.assertNotIn("goal_uuid",str(out))
        self.assertNotIn("raw_events",str(out))
        self.assertNotIn("home",str(out))

if __name__=="__main__":
    unittest.main()
