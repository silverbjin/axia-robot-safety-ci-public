"""Six compact first Scan evidence records; raw rosbag never public."""
import json
from pathlib import Path
import tempfile
import unittest
from d06.diagnostic.g07_scan_compact_bundle import build_compact_records

class CompactScanReport(unittest.TestCase):
    def test_no_evidence_produces_six_hold_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=build_compact_records(Path(tmp),"a"*40,44706879509)
            self.assertEqual(len(r),6)
            self.assertEqual(r["release_scope.json"]["owner_wsl2_l3"],"NOT_ACCEPTED")
            self.assertEqual(r["first_scan_timing_boundary.json"]["status"],"NOT_MEASURED")
            self.assertFalse(r["release_scope.json"]["certified_estop"])

    def test_actual_scan_breach_is_preserved_not_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"native/g07_ci_moving";p.mkdir(parents=True)
            p.joinpath("ci_moving_goal_result.json").write_text(json.dumps({
                "first_timing_violation":{"channel":"scan","limit_sec":.30,
                  "first_violation_sec":.317942691,
                  "first_violation_at":4467.340131066,
                  "first_violation_from":4467.022188375,
                  "first_violation_stage":"PRE_STOP"},
                "delivery_interval_diagnostics":{"scan":{
                  "first_violation_sec":.317942691,"max_gap_sec":.378410075,
                  "first_violation_from":4467.022188375,
                  "first_violation_at":4467.340131066,
                  "first_violation_stage":"PRE_STOP"}},
                "goal_cancel_ack":True,"guard_latched":False,
                "max_scan_interval_sec":.378410075,"status":"BLOCKED"}))
            p=Path(tmp)/"native"
            p.joinpath("g07_ci_scan_pregoal.json").write_text(json.dumps({
              "status":"PASS_SCOPED_RECEIVED_SCAN_ONLY",
              "local_window_rtf_estimate":.41,
              "topic_results":{"scan":{"max_wall_gap_ms":235.1},
                               "safety_scan":{"max_wall_gap_ms":242.1}}}))
            r=build_compact_records(Path(tmp),"b"*40,44706879509)
            self.assertEqual(r["first_scan_timing_boundary.json"]["status"],"SCAN300_BREACH")
            self.assertAlmostEqual(r["first_scan_timing_boundary.json"]["first_gap_ms"],317.942691)
            self.assertEqual(r["release_scope.json"]["owner_wsl2_l3"],"NOT_ACCEPTED")
            self.assertEqual(r["scan_pipeline_first_failure.json"]["root_cause"],"UNDETERMINED")
            self.assertNotIn("goal_uuid",json.dumps(r))

if __name__=="__main__":unittest.main()
