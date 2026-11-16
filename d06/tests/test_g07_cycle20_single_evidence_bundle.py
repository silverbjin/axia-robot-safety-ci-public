"""Cycle20 RED: one WSL2 read-only tar.gz with ALL bounded CM evidence.

No ROS/Gazebo/Goal, no raw bag, identifiers, host paths, or previous attempt
writes. A bounded synthetic original TAR is used in public Ubuntu24 CI.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from d06.live import g07_cycle19_first_cm_archive_readonly as old
from d06.live.g07_cycle20_single_bundle import create_bundle, read_bundle_manifest

FILES={"00_manifest.json","01_first_boundary.json","02_event_window.json",
       "03_cm_scheduler.json","04_environment.json","SHA256SUMS"}
NS=1700000000000000000

def ev(kind,t,source,seq,**other):
    n=NS+round(source*1e9)
    return {"kind":kind,"t":t,"rmw_source_ns":n,
            "rmw_received_ns":n+1000000,"rmw_publication_seq":seq,
            **other}

def synthetic():
    # first gap 186.714207ms, 4 real upstream source publications
    e=[{"kind":"owner_goal_published","t":8.0,"uuid":"PRIVATE_GOAL_UUID"},
       ev("pre_guard",10.1,100.,1,data={"secret":"PRIVATE_TEXT"}),
       ev("pre_guard",10.286714207,100.186714207,2,data={"secret":"DO_NOT_UPLOAD"})]
    e.extend([ev("supervised",10.12+.034*i,100.022+.035*i,100+i)
              for i in range(4)])
    e.extend([ev(kind,10.12+i*.01,100.025+i*.01,i+10,extra_path="/home/PRIVATE")
              for kind in ("scan","odom","clock","guard","source","supervisor")
              for i in range(3)])
    e.append({"kind":"action","t":10.25,"uuid":"PRIVATE_GOAL_UUID","status":5})
    live={
       "source_sha":old.PRIVATE_SHA,"goal_sent":True,"goal_uuid":"PRIVATE_GOAL_UUID",
       "first_guard_latch":{"reason":"UPSTREAM_STALE_AFTER_MOTION",
           "cm_age_sec":.174184617,"tick_monotonic":10.274184617,
           "secret":"PRIVATE_TOKEN"},
       "stop_native_rpc_monotonic_window":{"started_at":11.0,"ended_at":11.107021916},
       "cm_native_rpc_thread_state":{"available":True,"samples":8,
           "valid_samples":8,"runnable_samples":1,"all_sleeping_samples":7,
           "thread_count_max":16,"wait_classes":{"futex":31,"epoll":8},
           "tid":"PRIVATE_PID"},
       "cm_scheduler_native_stop_window":{"available":True,"run_sec":.012,
           "wait_sec":.003,"thread_count":16,
           "attribution":"CM_SCHEDULER_VS_EXECUTION_UNDETERMINED",
           "pid":"PRIVATE_PID"},
       "first_cm_supervisor_rmw_window":{"status":"CM_SOURCE_GAP_EXCEEDS_150MS"},
       "host_path":"/home/PRIVATE",
    }
    return live,e

def make_original(home):
    live,events=synthetic()
    name=old.NAME
    p=home/(name+".tar.gz")
    entries={
       name+"/source.sha":(old.PRIVATE_SHA+"\n").encode(),
       name+"/G07/live/ci_moving_goal_result.json":json.dumps(live).encode(),
       name+"/G07/live/actual_ros_events.jsonl":
           ("\n".join(json.dumps(x) for x in events)+"\n").encode()
    }
    with tarfile.open(p,"w:gz") as f:
        for n,b in entries.items():
            info=tarfile.TarInfo(n)
            info.size=len(b)
            f.addfile(info,io.BytesIO(b))
    return p,hashlib.sha256(p.read_bytes()).hexdigest()

class Cycle20BundleContract(unittest.TestCase):
    def build(self,home):
        arc,sha=make_original(home)
        output=home/"bundle_out"
        with patch.object(old,"ORIGINAL_SHA",sha):
            bundle=create_bundle(arc,output,expected_sha=sha)
        return arc,bundle

    def test_single_tar_has_exact_sanitized_six_members_and_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            arc,bundle=self.build(home)
            self.assertEqual(len(list((home/"bundle_out").iterdir())),1)
            self.assertEqual(bundle.suffixes[-2:],[".tar",".gz"])
            with tarfile.open(bundle,"r:gz") as tar:
                self.assertEqual(set(tar.getnames()),FILES)
                payload={i.name:tar.extractfile(i).read()
                         for i in tar.getmembers()}
                self.assertTrue(all(i.isfile() and i.size<200000
                                    for i in tar.getmembers()))
                checks={name:digest for digest,name in
                            (line.split(maxsplit=1) for line in
                             payload["SHA256SUMS"].decode().splitlines())}
                self.assertEqual(set(checks),FILES-{"SHA256SUMS"})
                for n,d in payload.items():
                    if n!="SHA256SUMS":
                        self.assertEqual(checks[n],hashlib.sha256(d).hexdigest())
                manifest=json.loads(payload["00_manifest.json"])
                self.assertTrue(manifest["no_ros_no_goal"])
                self.assertFalse(manifest["owner_l3_accepted"])
                self.assertFalse(manifest["certified_estop"])
                self.assertEqual(manifest["original_archive_sha256"],hashlib.sha256(arc.read_bytes()).hexdigest())
                self.assertFalse(manifest["private_original_included"])
            self.assertTrue(arc.is_file())

    def test_first_gap_is_outside_native_rpc_and_clock_discontinuity_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,bundle=self.build(Path(tmp))
            with tarfile.open(bundle) as t:
                b=json.load(t.extractfile("01_first_boundary.json"))
            self.assertEqual(b["native_stop_rpc_temporal_relation"],"FIRST_GAP_BEFORE_RPC")
            self.assertFalse(b["native_stop_rpc_overlaps_first_cm_gap"])
            self.assertEqual(b["upstream_publications_inside_gap"],4)
            self.assertAlmostEqual(b["first_cm_rmw_source_gap_ms"],186.714207,places=4)
            self.assertAlmostEqual(b["first_guard_cm_age_ms"],174.184617,places=4)
            self.assertFalse(b["host_clock_step_excluded"])
            self.assertFalse(b["cm_internal_cause_proven"])
            self.assertEqual(b["status"],"OWNER_FIRST_GUARD_TTL_BREACH_CAUSE_PENDING")

    def test_bounded_window_contains_no_raw_identifiers_values_or_absolute_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,bundle=self.build(Path(tmp))
            blob=bundle.read_bytes()
            for s in (b"PRIVATE_GOAL_UUID",b"PRIVATE_TOKEN",b"DO_NOT_UPLOAD",
                      b"/home/PRIVATE",b"PRIVATE_PID"):
                self.assertNotIn(s,blob)
            with tarfile.open(bundle) as t:
                b=json.load(t.extractfile("02_event_window.json"))
            self.assertEqual(b["time_origin"],"FIRST_CM_CALLBACK_AND_SOURCE_NORMALIZED")
            self.assertTrue(all(len(rows)<=16 for rows in b["events_by_kind"].values()))
            self.assertEqual(set(b["events_by_kind"]),{
                "pre_guard","supervised","scan","odom","clock","guard","source","supervisor"})
            for rows in b["events_by_kind"].values():
                for r in rows:
                    self.assertNotIn("data",r)
                    self.assertNotIn("uuid",r)
                    self.assertNotIn("t",r)
                    self.assertNotIn("rmw_source_ns",r)

    def test_scheduler_aggregation_only_not_pid_or_raw_thread_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,bundle=self.build(Path(tmp))
            with tarfile.open(bundle) as t:
                b=json.load(t.extractfile("03_cm_scheduler.json"))
            self.assertTrue(b["native_stop_window"]["available"])
            self.assertEqual(b["native_stop_window"]["thread_count"],16)
            self.assertEqual(b["rpc_sampler"]["samples"],8)
            self.assertNotIn("tid",json.dumps(b))
            self.assertNotIn("pid",json.dumps(b))

    def test_invalid_source_or_archive_digest_creates_no_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            arc,sha=make_original(root)
            out=root/"out"
            with self.assertRaises(ValueError):
                create_bundle(arc,out,expected_sha="f"*64)
            self.assertFalse(out.exists())
            arc.write_bytes(arc.read_bytes()+b"altered")
            with patch.object(old,"ORIGINAL_SHA",sha):
                with self.assertRaises(ValueError):
                    create_bundle(arc,out,expected_sha=sha)
            self.assertFalse(out.exists())

    def test_fail_closed_no_unsafe_symlink_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            arc,sha=make_original(root)
            out=root/"outside"
            out.symlink_to(root)
            with patch.object(old,"ORIGINAL_SHA",sha):
                with self.assertRaises(ValueError):
                    create_bundle(arc,out,expected_sha=sha)
            self.assertTrue(out.is_symlink())

    def test_report_reader_validates_manifest_and_tar_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,bundle=self.build(Path(tmp))
            m=read_bundle_manifest(bundle)
            self.assertEqual(m["schema"],"axia.g07.single_owner_sanitized_evidence_v1")
            self.assertFalse(m["owner_l3_accepted"])

    def test_readonly_owner_entrypoint_static_and_empty_home_does_not_start_ros(self):
        root=Path(__file__).resolve().parents[2]
        p=root/"scripts/axia_g07_cycle20_owner_single_bundle_once.sh"
        src=p.read_text(encoding="utf-8")
        for term in ("g07_cycle20_single_bundle.py","--self-check",
                     "NO_ROS_NO_GOAL",'--expected-sha256 "$ORIGINAL_SHA"'):
            self.assertIn(term,src)
        for term in ("ros2 action send_goal","YES-P2-G07-GOAL",
                     "wsl --shutdown","sudo apt","rm -rf -- \"$HOME"):
            self.assertNotIn(term,src)
        with tempfile.TemporaryDirectory() as tmp:
            r=subprocess.run(["bash",str(p),"--self-check"],
                             cwd=tmp,capture_output=True,text=True,timeout=15,
                             env={**os.environ,"HOME":tmp})
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertIn("NO_ROS_NO_GOAL",r.stdout)
            self.assertEqual(list(Path(tmp).iterdir()),[])

if __name__=="__main__":unittest.main()
