"""P4-00 G11 source ledger contract: synthetic data, never a real acceptance."""
import copy
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "tools/p4_g11_source_ledger.py"
spec = importlib.util.spec_from_file_location("p4_g11_source_ledger", SOURCE)
ledger_validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger_validator)

SHA = "1"*40
ARCHIVE_SHA = "2"*64
UUID = "a"*32


def fixture():
    records = [
        {"id": "p0_run7_s01", "scenario": "S01", "gate": "G08", "evidence_level": "OWNER_REPORT_ONLY",
         "capture_source_sha": SHA, "formal_eligible": False, "reason": "SAME_GOAL_RAW_ARCHIVE_NOT_LOCATED",
         "reported_goal_uuid": UUID, "archive_sha256": ARCHIVE_SHA},
        {"id": "g07_scoped", "scenario": "S02", "gate": "G07", "evidence_level": "OWNER_L3_SCOPED_RAW_REVIEW",
         "capture_source_sha": SHA, "formal_eligible": False, "reason": "NO_CONTACT_GROUND_TRUTH"},
        {"id": "p2_xjx_g06_failed", "scenario": "S03", "gate": "G06",
         "evidence_level": "OWNER_RAW_REVIEW_FAILED", "capture_source_sha": SHA,
         "formal_eligible": False, "reason": "GOAL_SUCCEEDED_BEFORE_LATCH", "observed_result": "FAIL"},
        {"id": "g09_synthetic", "scenario": "S04", "gate": "G09",
         "evidence_level": "SYNTHETIC_INPUT_REAL_ROS_L1", "capture_source_sha": SHA,
         "formal_eligible": False, "reason": "NO_GAZEBO_TRACK_JOIN"},
        {"id": "g10_synthetic", "scenario": "S05", "gate": "G10",
         "evidence_level": "SYNTHETIC_COMPOUND_TRACE_L0", "capture_source_sha": SHA,
         "formal_eligible": False, "reason": "NO_REAL_GOAL"}
    ]
    scenarios = [
        {"id": "S0"+str(i), "gate": ["G08", "G07", "G10", "G09", "G10"][i-1],
         "required": 3, "formal_verified": 0,
         "unverified_candidate_ids": [records[i-1]["id"]],
         "unresolved_join": ["raw time and source join"],
         "remaining_to_qualify": 3,
         "new_runs_required_now": "UNDETERMINED_REQUALIFY_EXISTING_RAW_FIRST"}
        for i in range(1, 6)
    ]
    return {
        "schema": "axia_p4_g11_source_evidence_ledger_v1",
        "origin_staging_sha": SHA, "scope": "P4_00_METADATA_ONLY_NO_NEW_ROS_GAZEBO_OR_OWNER_RUN",
        "runtime_reference_digest": "ghcr.io/example/image@sha256:"+"3"*64,
        "runtime_digest_this_task_reverified": False,
        "formal_accepted": False, "main_merge_approved": False,
        "student_release_approved": False, "hardware_estop_certified": False,
        "g08": {"status": "G08_RAW_MISSING_IN_REVIEWED_INVENTORY_NOT_ACCEPTED",
                "reference_source_id": "p0_run7_s01", "replayed_or_reran_goal": False},
        "observed_sources": records,
        "g11": {"required_scenarios": 5, "required_formal_runs_each": 3,
                "formal_acceptance_counts": {"S0"+str(i): 0 for i in range(1, 6)},
                "scenarios": scenarios},
        "g12": {"status": "D03_SCOPED_ONLY_FULL_RELEASE_HOLD",
                "full_git_history_scan_done": False,
                "full_p4_student_release_approved": False},
        "g13": {"status": "NOT_RUN", "required_distinct_external_pcs": 2,
                "verified_distinct_external_pcs": 0},
    }


class LedgerContract(unittest.TestCase):
    def test_metadata_only_never_grants_formal_gate(self):
        out = ledger_validator.check(fixture())
        self.assertEqual(out["status"], "P4_00_METADATA_SCOPE_PASS")
        self.assertFalse(out["formal_accepted"])
        self.assertEqual(out["g11_formal_runs"], 0)

    def test_forged_formal_pass_is_rejected(self):
        for key in ("formal_accepted", "main_merge_approved", "student_release_approved", "hardware_estop_certified"):
            with self.subTest(key=key):
                src = fixture()
                src[key] = True
                with self.assertRaises(ValueError):
                    ledger_validator.check(src)

    def test_raw_missing_cannot_be_silently_changed_to_g08_pass(self):
        v = fixture()
        v["g08"]["status"] = "PASS"
        with self.assertRaises(ValueError):
            ledger_validator.check(v)

    def test_no_counting_synthetic_or_candidate_ros_as_a_cold_run(self):
        for scenario in fixture()["g11"]["scenarios"]:
            v = fixture()
            sc = next(s for s in v["g11"]["scenarios"] if s["id"] == scenario["id"])
            sc["formal_verified"] = 1
            v["g11"]["formal_acceptance_counts"][scenario["id"]] = 1
            with self.assertRaises(ValueError):
                ledger_validator.check(v)

    def test_duplicate_candidate_or_missing_provenance_rejected(self):
        v = fixture()
        v["observed_sources"].append(copy.deepcopy(v["observed_sources"][0]))
        with self.assertRaises(ValueError):
            ledger_validator.check(v)
        v = fixture()
        v["observed_sources"][0]["capture_source_sha"] = "not-a-sha"
        with self.assertRaises(ValueError):
            ledger_validator.check(v)

    def test_historical_g06_succeeded_before_latch_remains_failure(self):
        v = fixture()
        v["observed_sources"][2]["observed_result"] = "PASS"
        with self.assertRaises(ValueError):
            ledger_validator.check(v)
        v = fixture()
        v["observed_sources"][2]["formal_eligible"] = True
        with self.assertRaises(ValueError):
            ledger_validator.check(v)

    def test_external_two_pc_and_full_student_release_remain_hold(self):
        v = fixture()
        v["g13"]["verified_distinct_external_pcs"] = 2
        with self.assertRaises(ValueError):
            ledger_validator.check(v)
        v = fixture()
        v["g12"]["full_git_history_scan_done"] = True
        with self.assertRaises(ValueError):
            ledger_validator.check(v)


if __name__ == "__main__":
    unittest.main()
