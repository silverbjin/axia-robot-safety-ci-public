"""Cycle19 targeted 186.714ms Owner first CM provenance to STOP RPC.

RED->GREEN for read-only ORIGINAL Owner archive, not a simulated ROS/Goal PASS.
Synthetic ROS event timestamps are artificial; real Owner file is not in CI.
"""
from __future__ import annotations
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

M=importlib.import_module("d06.live.g07_cycle19_first_cm_archive_readonly")
T0=1700000000000000000
def ev(kind,callback,source_sec,sequence):
    s=T0+int(source_sec*1e9)
    return {"kind":kind,"t":callback,"rmw_source_ns":s,
            "rmw_received_ns":s+800000,"rmw_publication_seq":sequence}
def data(complete=True,with_rpc=True):
    events=[{"kind":"owner_goal_published","t":9.0}]
    events += [ev("pre_guard",10.10,100.0,1),
               ev("pre_guard",10.286714207,100.186714207,2)]
    events += [ev("supervised",10.10+i*.036,100.02+i*.035,10+i)
               for i in range(4)]
    live={"first_guard_latch":{
             "reason":"UPSTREAM_STALE_AFTER_MOTION",
             "cm_age_sec":.174184617,"tick_monotonic":10.274184617},
          "goal_sent":True,"owner_l3_accepted":False,
          "cm_scheduler_native_stop_window":{
              "available":False,"attribution":"CM_SCHEDSTAT_UNAVAILABLE"}}
    if with_rpc:
        live["stop_native_rpc_monotonic_window"]={
            "started_at":10.15,"ended_at":10.25}
    if not complete:
        del events[-1]
    return live,events

def archive(root, live, events, *, source=M.PRIVATE_SHA, duplicate=False):
    p=root/(M.NAME+".tar.gz")
    pieces={
        M.NAME+"/source.sha":(source+"\n").encode(),
        M.NAME+"/G07/live/ci_moving_goal_result.json":
            json.dumps(live).encode(),
        M.NAME+"/G07/live/actual_ros_events.jsonl":
            ("\n".join(json.dumps(x) for x in events)+"\n").encode()
    }
    with tarfile.open(p,"w:gz") as t:
        for name,blob in pieces.items():
            x=tarfile.TarInfo(name)
            x.size=len(blob)
            t.addfile(x,io.BytesIO(blob))
        if duplicate:
            blob=pieces[M.NAME+"/source.sha"]
            x=tarfile.TarInfo(M.NAME+"/source.sha")
            x.size=len(blob)
            t.addfile(x,io.BytesIO(blob))
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    return p,sha

class Cycle19FirstOwnerGap(unittest.TestCase):
    def test_realistic_gap_with_four_upstream_and_overlapping_rpc_is_only_candidate(self):
        live,events=data()
        r=M.analyze_original(live,events)
        self.assertEqual(r["status"],"OWNER_FIRST_CM_GAP_CONFIRMED_CAUSE_PENDING")
        self.assertAlmostEqual(r["first_guard_cm_age_ms"],174.184617,places=4)
        self.assertAlmostEqual(r["first_cm_rmw_source_gap_ms"],186.714207,places=4)
        self.assertEqual(r["upstream_publications_inside_gap"],4)
        self.assertTrue(r["first_guard_tick_inside_same_monotonic_cm_gap"])
        self.assertTrue(r["native_stop_rpc_overlaps_first_cm_gap_candidate"])
        self.assertAlmostEqual(r["native_stop_rpc_duration_ms"],100,places=4)
        self.assertFalse(r["cm_internal_callback_cause_proven"])
        self.assertFalse(r["owner_goal_authorized"])
        self.assertFalse(r["owner_l3_accepted"])

    def test_missing_stop_rpc_is_unknown_never_guessed(self):
        r=M.analyze_original(*data(with_rpc=False))
        self.assertIsNone(r["native_stop_rpc_overlaps_first_cm_gap_candidate"])
        self.assertIsNone(r["native_stop_rpc_duration_ms"])
        self.assertEqual(r["causal_attribution"],"UNDETERMINED_CM_PROCESSING_VS_TF_VS_SCHEDULER")

    def test_no_first_latch_or_no_rmw_source_never_claims_success(self):
        live,events=data()
        bad=M.analyze_original(live|{"first_guard_latch":None},events)
        self.assertEqual(bad["status"],"ORIGINAL_GUARD_FIRST_LATCH_UNVERIFIED")
        bad=M.analyze_original(live,[{"kind":"owner_goal_published","t":9.}])
        self.assertEqual(bad["status"],"ORIGINAL_CM_RMW_SOURCE_MISSING")

    def test_bad_clock_step_or_nonmonotonic_rmw_fails_closed(self):
        live,events=data()
        events[2]["rmw_source_ns"]=events[1]["rmw_source_ns"]-1
        result=M.analyze_original(live,events)
        self.assertEqual(result["status"],"RMW_SOURCE_SEQUENCE_OR_CLOCK_DISCONTINUITY")

    def test_original_hash_and_source_verified_no_tar_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            p,sha=archive(base,*data())
            saved=M.ORIGINAL_SHA
            try:
                M.ORIGINAL_SHA=sha
                report=M.inspect(p,expected_sha=sha)
                self.assertEqual(report["status"],"OWNER_FIRST_CM_GAP_CONFIRMED_CAUSE_PENDING")
                with self.assertRaisesRegex(ValueError,"HASH_OR_NAME_MISMATCH"):
                    M.inspect(p,expected_sha="f"*64)
            finally:
                M.ORIGINAL_SHA=saved
            self.assertEqual(sorted(x.name for x in base.iterdir()),[p.name])

    def test_sha256_custody_object_original_filename_supported_without_copy(self):
        # Actual G11 retention has an immutable object named by the SHA256.
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            p,sha=archive(base,*data())
            stored=base/sha
            p.rename(stored)
            original=M.ORIGINAL_SHA
            try:
                M.ORIGINAL_SHA=sha
                d=M.inspect(stored,expected_sha=sha)
                self.assertEqual(d["status"],"OWNER_FIRST_CM_GAP_CONFIRMED_CAUSE_PENDING")
            finally:
                M.ORIGINAL_SHA=original
            self.assertEqual(list(base.iterdir()),[stored])

    def test_duplicate_and_wrong_source_members_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            for dup,source in [(True,M.PRIVATE_SHA),(False,"0"*40)]:
                p,sha=archive(base,*data(),source=source,duplicate=dup)
                old=M.ORIGINAL_SHA
                try:
                    M.ORIGINAL_SHA=sha
                    with self.assertRaises(ValueError):
                        M.inspect(p,expected_sha=sha)
                finally:
                    M.ORIGINAL_SHA=old
                p.unlink()

    def test_cli_wrong_archive_no_output_side_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            p,sha=archive(base,*data())
            out=base/"sanitized.json"
            cli=Path(M.__file__)
            r=subprocess.run(["python3",str(cli),"--archive",str(p),
                             "--output",str(out)],
                             text=True,capture_output=True,timeout=15,
                             cwd=tmp,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
            self.assertEqual(r.returncode,3,r.stdout+r.stderr)
            self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",r.stdout)
            self.assertFalse(out.exists())

    def test_no_goal_no_ros_or_private_uuid_in_output(self):
        r=M.analyze_original(*data())
        s=json.dumps(r,sort_keys=True)
        self.assertNotIn("goal_uuid",s)
        self.assertNotIn("add31714d8c54b4980603d76ee6bc0b4",s)
        self.assertNotIn("/home/",s)
        self.assertNotIn("PASSED_OWNER",s)
        self.assertNotIn("ACCEPTED",s)

if __name__=="__main__":
    unittest.main()
