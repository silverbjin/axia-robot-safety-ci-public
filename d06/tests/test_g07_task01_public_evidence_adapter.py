"""Public CI sealed raw-to-timing adapter must fail closed without private evidence."""
import json
import tempfile
import unittest
from pathlib import Path
from d06.scripts.g07_task01_extract_public_gap import extract

SHA="0123456789abcdef0123456789abcdef01234567"
class TestPublicEvidenceAdapter(unittest.TestCase):
    def test_missing_private_inputs_produce_small_fixed_public_hold(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            out=root/"public"/"first_gap_sanitized.json"
            status,p=extract(events=root/"INSTRUCTOR_SECRET_TOKEN",
                trace_dir=root/"PRIVATE_TRACE",tf_file=root/"TF_FILE",
                anchors_dir=root/"PRIVATE_ANCHOR",out=out,
                run_id="44040000001",public_sha=SHA)
            self.assertEqual(status,"RAW_EVIDENCE_NOT_CREATED_HOLD")
            doc=json.loads(p.read_text())
            self.assertFalse(doc["cm120_release_pass"])
            self.assertFalse(doc["root_cause_proven"])
            self.assertFalse(doc["gate_c_authorized"])
            self.assertNotIn("INSTRUCTOR_SECRET_TOKEN",p.read_text())
            self.assertNotIn("PRIVATE_TRACE",p.read_text())
            self.assertLess(p.stat().st_size,1024)

    def test_malformed_private_input_does_not_propagate_exception_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"trace").mkdir()
            (root/"anchors").mkdir()
            (root/"events").write_text('{"INSTRUCTOR_PASSWORD":"DONOTLEAK"}\n')
            (root/"tf").write_text('DONOTLEAK RAW TF\n')
            (root/"anchors"/"start_anchor.json").write_text('{"mono_ns":1,"wall_ns":2}')
            (root/"anchors"/"end_anchor.json").write_text('{"mono_ns":2,"wall_ns":3}')
            status,p=extract(events=root/"events",trace_dir=root/"trace",
                tf_file=root/"tf",anchors_dir=root/"anchors",
                out=root/"public"/"first_gap_sanitized.json",
                run_id="44040000001",public_sha=SHA)
            self.assertEqual(status,"PUBLIC_EVIDENCE_EXTRACTION_UNVERIFIED_HOLD")
            self.assertNotIn("DONOTLEAK",p.read_text())
            self.assertFalse(json.loads(p.read_text())["cm120_release_pass"])

    def test_invalid_identifier_prevents_even_fallback_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(ValueError):
                extract(events="none",trace_dir="none",tf_file="none",
                    anchors_dir="none",out=root/"out.json",
                    run_id="bogus",public_sha=SHA)
            self.assertFalse((root/"out.json").exists())

if __name__=="__main__":
    unittest.main()
