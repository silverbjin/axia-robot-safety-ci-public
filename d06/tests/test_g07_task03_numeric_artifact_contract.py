"""Task03 real numeric artifact JSON integrity regression.

Actual run 44215546368 passed physics/Goal/CM/Guard but exported a trailing
literal escaped newline in one supplementary calibration JSON. Never fake
physical evidence or rerun valid motions merely for a JSON source typo.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LEDGER=ROOT/"d06/evidence/g07_task03/run_44215546368_formal_public_l2_provenance.json"
WORKFLOW=ROOT/".github/workflows/axia-g07-task03-formal-public-l0-l2-20261118.yml"


class Task03NumericEvidenceIntegrity(unittest.TestCase):
    def test_positive_calibration_source_writes_valid_json_newline(self):
        text=WORKFLOW.read_text()
        # Python source must contain ONE literal backslash+n, which becomes
        # newline in the JSON file; the previous TWO emitted literal '\n'
        # after the JSON object and broke json.loads().
        self.assertIn(r'+"\n")',text)
        self.assertNotIn(r'+"\\n")',text)

    def test_tail_only_repair_is_valid_json_and_exact_sha(self):
        normalized=(ROOT/"d06/evidence/g07_task03/"
                    "task03_positive_calibration_run_44215546368_normalized.json")
        data=normalized.read_bytes()
        obj=json.loads(data)
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\\n"))
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         "5abb8ad189f6bb109f910b7af2d044f09f81cb375037e7682d6f759f4098f2be")
        self.assertEqual(obj["status"],"CONTACT_CALIBRATION_PROVEN_DISPOSABLE_ONLY")
        self.assertEqual(obj["native_positive_contacts"],5346)
        self.assertEqual(obj["native_observed_iterations"],21692)
        self.assertEqual(obj["leaked_processes_count"],0)
        self.assertFalse(obj["motion_goal_sent"])

    def test_actual_evidence_source_pinned_original_hash_and_repaired_only_tail(self):
        obj=json.loads(LEDGER.read_text(encoding="utf-8"))
        self.assertEqual(obj["original_run_id"],44215546368)
        self.assertEqual(obj["original_gazebo_source_sha"],
                         "c996a5f415ca90e9dac99d798944a56d6b70d8be")
        self.assertEqual(obj["original_numeric_artifact_id"],14387738909)
        self.assertEqual(obj["original_zip_sha256"],
                         "a0cb7e7a4c961c321e0f9c32fc0854e93b5b9137e72da5d21d9052a17d109cbe")
        self.assertEqual(obj["original_formal_verdict_json_sha256"],
                         "c02a77d45a72f771e7505f0798014c528c49fbe9d4")
        self.assertEqual(obj["original_positive_raw_invalid_json_sha256"],
                         "ef33d89b2c4a9c06f412c73a4d555fe5ae731af3399ecebcd6eabf5e60494bc6")
        self.assertEqual(obj["positive_calibration_json_tail_only_normalized_sha256"],
                         "5abb8ad189f6bb109f910b7af2d044f09f81cb375037e7682d6f759f4098f2be")
        self.assertEqual(obj["actual_goal"]["first_failure"],"NONE")
        self.assertEqual(obj["actual_goal"]["guard_after_forward_cm_age_max_ms"],49.872948)
        self.assertEqual(obj["actual_goal"]["cm_rmw_source_gap_max_ms"],52.513109)
        self.assertEqual(obj["actual_goal"]["cm_observer_gap_max_ms"],67.913195)
        self.assertEqual(obj["actual_goal"]["contact_count"],0)
        self.assertEqual(obj["actual_goal"]["bag_topic_count"],14)
        self.assertFalse(obj["owner_wsl2_l3_accepted"])
        self.assertFalse(obj["certified_estop"])

if __name__=="__main__":
    unittest.main()
