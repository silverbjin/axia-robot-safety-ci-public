"""RED: only an explicit, narrow timing allowlist may leave the sealed runner.

This test never authorizes a Goal. Source SYSTEM and Observer MONOTONIC are
kept distinct; private source/scene/raw ROS/traces MUST NOT be serialized.
"""
import hashlib
import json
import unittest
from d06.diagnostic.export_public_cm120_first_gap import export_sanitized
from d06.tests.test_g07_cm120_tf_first_gap_join import (
    READY, anchor, line, metadata, trace, observer
)
from d06.tests.test_g07_cm120_task01_per_sleep_span_join import poll

SHA="0123456789abcdef0123456789abcdef01234567"

class TestPublicEvidenceAllowlist(unittest.TestCase):
    def _sample(self):
        obs=observer()
        obs[1]["private_source_code"]="LEAK_PRIVATE_INSTRUCTOR_CODE"
        obs[1]["pose"]={"x":"LEAK_GAZEBO_SCENE"}
        tr=trace()
        tr[0]["raw_file_path"]="/home/instructor/private-secret.py"
        tf=[READY,line(12.014,12.105,cpu=.0003),
            poll(12.024,12.034),poll(12.044,12.054)]
        return obs,tr,tf

    def test_no_private_fields_ever_leave_public_artifact(self):
        o,t,tf=self._sample()
        out=export_sanitized(o,t,tf,anchor(),run_id="44040000001",public_sha=SHA)
        s=json.dumps(out,sort_keys=True)
        for forbidden in ("LEAK_PRIVATE_INSTRUCTOR_CODE", "LEAK_GAZEBO_SCENE",
                          "private-secret.py", "0xa", "0xb", "0xc",
                          "pose", "source_code", "frame_id", "/cmd_vel_supervised"):
            self.assertNotIn(forbidden,s)
        self.assertEqual(out["schema"],"axia.g07.cm120.public_first_gap_v1")
        self.assertFalse(out["cm120_release_pass"])
        self.assertFalse(out["source_publication_to_monotonic_alignment_proven"])
        self.assertFalse(out["root_cause_proven"])
        self.assertEqual(out["first_gap"]["rmw_source_gap_ns"],132000000)
        self.assertEqual(out["tf_sleep"]["count"],2)

    def test_source_and_observer_clocks_never_subtracted_as_absolute_epoch(self):
        o,t,tf=self._sample()
        out=export_sanitized(o,t,tf,anchor(),run_id="44040000001",public_sha=SHA)
        self.assertIn("source_from_wall_start_anchor_ns",out["first_gap"]["pairs"][0])
        self.assertIn("observer_from_mono_start_anchor_ns",out["first_gap"]["pairs"][0])
        self.assertNotIn("same_clock_proven",out)
        self.assertFalse(out["source_publication_to_monotonic_alignment_proven"])
        self.assertEqual(len(out["first_gap"]["pairs"]),2)

    def test_missing_first_gap_gives_nonrelease_summary_without_raw_payload(self):
        o,t,tf=self._sample()
        o[2]["rmw_source_ns"]=o[1]["rmw_source_ns"]+110000000
        out=export_sanitized(o,t,tf,anchor(),run_id="44040000001",public_sha=SHA)
        self.assertEqual(out["status"],"FIRST_RMW_SOURCE_GAP_NOT_REPRODUCED")
        self.assertFalse(out["gate_c_authorized"])
        self.assertFalse(out["cm120_release_pass"])
        self.assertNotIn("LEAK_PRIVATE",json.dumps(out))

    def test_invalid_run_sha_or_unbounded_input_fails_closed(self):
        o,t,tf=self._sample()
        for sha in ("main","0"*39,"/"*40):
            with self.subTest(sha=sha):
                with self.assertRaises(ValueError):
                    export_sanitized(o,t,tf,anchor(),run_id="44040000001",public_sha=sha)
        with self.assertRaises(ValueError):
            export_sanitized(o,t,tf*7000,anchor(),run_id="44040000001",public_sha=SHA)

    def test_output_deterministic_and_only_anonymized_time_spans(self):
        o,t,tf=self._sample()
        a=export_sanitized(o,t,tf,anchor(),run_id="44040000001",public_sha=SHA)
        b=export_sanitized(o,t,tf,anchor(),run_id="44040000001",public_sha=SHA)
        self.assertEqual(hashlib.sha256(json.dumps(a,sort_keys=True).encode()).hexdigest(),
                         hashlib.sha256(json.dumps(b,sort_keys=True).encode()).hexdigest())
        self.assertIn("tf_sleep",a)
        self.assertLessEqual(len(a["tf_sleep"]["spans"]),64)
        for span in a["tf_sleep"]["spans"]:
            self.assertEqual(set(span),{"start_rel_observer_ns","end_rel_observer_ns",
                                       "request_ns","rc"})

if __name__=="__main__":
    unittest.main()
