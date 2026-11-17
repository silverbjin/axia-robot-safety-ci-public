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

    def test_trace_failure_preserves_only_numeric_first_source_gap(self):
        # A genuine observer RMW source pair must not be discarded merely
        # because a separate LTTng/bt2 owner link cannot be decoded.
        # No PID, pose, raw ROS or TF line is allowed in the fallback.
        from unittest.mock import patch
        from d06.tests.test_g07_cm120_tf_first_gap_join import observer,anchor
        from d06.diagnostic.export_public_cm120_first_gap import READY
        with tempfile.TemporaryDirectory() as t:
            r=Path(t)
            (r/"trace").mkdir()
            (r/"anchors").mkdir()
            (r/"events").write_text("".join(
                json.dumps(x)+"\\n" for x in observer()),encoding="utf-8")
            (r/"tf").write_text(READY+"\\n",encoding="utf-8")
            (r/"anchors/start_anchor.json").write_text(
                json.dumps(anchor()["start"]))
            (r/"anchors/end_anchor.json").write_text(
                json.dumps(anchor()["end"]))
            with patch("d06.scripts.g07_task01_extract_public_gap.exact_trace_rows",
                       side_effect=ValueError("sensitive RAW event text")):
                status,p=extract(events=r/"events",trace_dir=r/"trace",
                    tf_file=r/"tf",anchors_dir=r/"anchors",
                    out=r/"safe"/"first_gap_sanitized.json",
                    run_id="44040000001",public_sha=SHA)
            d=json.loads(p.read_text())
            self.assertEqual(status,"PUBLIC_EVIDENCE_EXTRACTION_UNVERIFIED_HOLD")
            self.assertEqual(d["failure_stage"],"NATIVE_LTTNG_CALLBACK_ROWS")
            self.assertEqual(d["first_gap"]["rmw_source_gap_ns"],132000000)
            self.assertEqual(d["first_gap"]["observer_gap_ns"],132000000)
            self.assertFalse(d["source_publication_to_monotonic_alignment_proven"])
            self.assertFalse(d["root_cause_proven"])
            self.assertNotIn("sensitive RAW",p.read_text())
            self.assertNotIn("pose",p.read_text().lower())
            self.assertLess(p.stat().st_size,1024)

if __name__=="__main__":
    unittest.main()
