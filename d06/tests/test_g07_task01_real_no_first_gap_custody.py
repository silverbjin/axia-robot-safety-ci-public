"""The ONE approved extra moving diagnostic did NOT reproduce CM source>120.

This is an actual public-only allowlisted GitHub artifact: immutable hash,
verified explicit diagnostic HOLD and no unvalidated release/causal credit.
"""
import hashlib
import json
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]/"evidence/g07_cm120_task01"
P=BASE/"run_44059005075_first_gap_sanitized.json"
SUM=BASE/"run_44059005075_SHA256SUMS.txt"
EXPECTED_SHA="03728855c60a0a8dd69ad8b48960db078980ea675f40936c14b991a1849f6b34"

class TestRealDiagnosticNoFirstGapCustody(unittest.TestCase):
    def test_actual_sanitized_github_run_bytes_pinned(self):
        self.assertTrue(P.is_file())
        self.assertTrue(SUM.is_file())
        self.assertEqual(hashlib.sha256(P.read_bytes()).hexdigest(),EXPECTED_SHA)
        self.assertEqual(SUM.read_text().strip(),EXPECTED_SHA+"  first_gap_sanitized.json")

    def test_no_first_gap_means_no_causal_or_release_credit(self):
        obj=json.loads(P.read_text())
        self.assertEqual(obj["schema"],"axia.g07.cm120.public_first_gap_v1")
        self.assertEqual(obj["run_id"],"44059005075")
        self.assertEqual(obj["public_source_sha"],
                         "19ec465b7fdcb99391419e8252906961f1cda1a1")
        self.assertEqual(obj["status"],"FIRST_RMW_SOURCE_GAP_NOT_REPRODUCED")
        self.assertIsNone(obj["first_gap"])
        self.assertEqual(obj["tf_sleep"]["count"],0)
        self.assertFalse(obj["root_cause_proven"])
        self.assertFalse(obj["source_publication_to_monotonic_alignment_proven"])
        self.assertFalse(obj["gate_c_authorized"])
        self.assertFalse(obj["cm120_release_pass"])
        self.assertFalse(obj["owner_wsl2_accepted"])
        self.assertFalse(obj["certified_estop"])

if __name__=="__main__":
    unittest.main()
