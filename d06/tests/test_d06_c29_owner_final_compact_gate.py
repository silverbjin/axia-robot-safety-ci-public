"""C29-05 no-simulation release/field custody contracts.

A synthetic compact TAR exercises EXACT SAME fail-closed evidence validator
used by the one-shot owner; no ROS/Gazebo/hardware is run by these tests.
"""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
VALIDATOR=ROOT/"d06/tools/d06_c29_no_goal_compact_gate.py"
WRAPPER=ROOT/"d06/scripts/axia_d06_c29_owner_final_no_goal_once.sh"
RELEASE=ROOT/"d06/ci/c29_selected_cyclonedds_release.json"

def good():
    return {
      "summary.txt":json.dumps({"first_failure":"NOT_OBSERVED_IN_COMPACT",
              "native_gz_exit0_marker":True,"native_gz_died_marker":False,
              "forced_teardown":False,"cm_exit_code":0,"root_cause":"UNCONFIRMED"})+"\ncore_not_archived=true\n",
      "native_gazebo_exit_events.log":"[INFO] [gz-21]: process has finished cleanly [pid 4242]\n",
      "renderer.txt":"OpenGL renderer string: D3D12 (NVIDIA GeForce RTX 2060 with Max-Q Design)\n",
      "sensor_truth.json":json.dumps({
              "status":"NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE","reasons":[],
              "goal_sent":False,"fixture_moved":False,"fault_injected":False,
              "dual_topic_actual_wall_observation_sec":20.15,
              "metrics":{"raw":{"count":202,"max_receipt_gap_sec":0.121,
                        "first_receipt_ttl_breach_at_index":None},
                         "safety":{"count":201,"max_receipt_gap_sec":0.123,
                         "first_receipt_ttl_breach_at_index":None,
                         "clear_count":201,"front_median_m":1.41,"side_median_m":2.52}}}),
      "ordered_shutdown.json":json.dumps({
          "status":"NAV2_LIFECYCLE_SHUTDOWN_ACK","navigation_ack":True,
          "localization_ack":True,"rmw_implementation_identifier":"rmw_cyclonedds_cpp"}),
      "cm_shutdown_audit.json":json.dumps({
          "status":"SHUTDOWN_CLEAN_CANDIDATE","cm_exit_code":0}),
      "teardown.txt":"P2_L2_GRACEFUL_TEARDOWN\n",
      "scan_delivery.json":json.dumps({
          "native_count":200,"observer_raw_count":200,"observer_safety_count":200,
          "post_ready_proxy":{"scope":"POST_NAV2_READY_PROXY",
                "candidate":"NO_ROS_TTL_VIOLATION_WITNESSED","goal_allowed":False},
          "student_first_ttl":{"student_first_candidate":"STUDENT_FIRST_PAIR_UNAVAILABLE"},
          "goal_allowed":False})
    }

def check(files):
    with tempfile.TemporaryDirectory() as tmp:
        archive=Path(tmp)/"compact.tar.gz"
        with tarfile.open(archive,"w:gz") as tf:
            for n,v in files.items():
                raw=v.encode()
                meta=tarfile.TarInfo(n);meta.size=len(raw)
                tf.addfile(meta,io.BytesIO(raw))
        Path(str(archive)+".sha256").write_text(
           hashlib.sha256(archive.read_bytes()).hexdigest()+"  "+str(archive)+"\n")
        return subprocess.run(["python3",str(VALIDATOR),"--verify-compact",str(archive)],
            capture_output=True,text=True,timeout=6)

class C29CompactAcceptance(unittest.TestCase):
    def test_positive_synthetic_is_not_wsl2_proof(self):
        r=check(good())
        self.assertEqual(r.returncode,0,(r.stdout,r.stderr))
        self.assertIn("C29_NO_GOAL_EVIDENCE_CONTRACT_PASS_NEEDS_ACTUAL_WSL2_PROVENANCE",r.stdout)
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",r.stdout)

    def test_unsafe_scan_and_first_ttl_breach_never_pass(self):
        for unsafe in (0.316032,0.400895):
            d=good();v=json.loads(d["sensor_truth.json"])
            v["metrics"]["raw"]["max_receipt_gap_sec"]=unsafe
            v["metrics"]["raw"]["first_receipt_ttl_breach_at_index"]=13
            d["sensor_truth.json"]=json.dumps(v)
            r=check(d)
            self.assertEqual(r.returncode,3,r.stdout)
            self.assertIn("C29_EVIDENCE_HOLD=",r.stdout)

    def test_nav_cm_gz_rmw_forced_and_goal_failure_is_fail_closed(self):
        def replace_obj(d,key,f):
            v=json.loads(d[key]);f(v);d[key]=json.dumps(v)
        cases=[
          lambda d:replace_obj(d,"ordered_shutdown.json",
                              lambda v:v.update(navigation_ack=False)),
          lambda d:replace_obj(d,"cm_shutdown_audit.json",
                              lambda v:v.update(cm_exit_code=None)),
          lambda d:replace_obj(d,"ordered_shutdown.json",
                              lambda v:v.update(rmw_implementation_identifier="rmw_fastrtps_cpp")),
          lambda d:replace_obj(d,"sensor_truth.json",
                              lambda v:v.update(goal_sent=True)),
          lambda d:d.update({"teardown.txt":"P2_L2_FORCED_TEARDOWN\n"}),
          lambda d:d.update({"native_gazebo_exit_events.log":
                             "[ERROR] [gz-21]: process has died [exit code -11]\n"}),
          lambda d:d.update({"renderer.txt":
                             "OpenGL renderer string: D3D12 (Intel Iris Xe)\n"}),
          lambda d:d.pop("scan_delivery.json"),
        ]
        for mut in cases:
            d=good();mut(d);r=check(d)
            self.assertEqual(r.returncode,3,(r.stdout,r.stderr))
            self.assertIn("C29_EVIDENCE_HOLD=",r.stdout)

    def test_release_manifest_preserves_ab_evidence_and_other_safety_holds(self):
        m=json.loads(RELEASE.read_text())
        self.assertEqual(m["schema"],"axia.d06.c29.release-candidate.v1")
        self.assertEqual(m["student_sha"],"6c79c09d91f13c81961492eb30e66d99d307831c")
        self.assertEqual(m["ci_two_cold_run_id"],44876761417)
        self.assertEqual(m["ci_two_cold_status"],"PASS_2_OF_2_LINUX_CYCLONEDDS")
        self.assertEqual(m["selected_rmw"],"rmw_cyclonedds_cpp")
        self.assertEqual(m["owner_wsl2_l3"],"NOT_RUN")
        self.assertEqual(m["cm120_moving_e2e"],"NOT_VERIFIED")
        self.assertEqual(m["guard150_moving_e2e"],"NOT_VERIFIED")
        self.assertFalse(m["certified_estop"])
        self.assertFalse(m["main_merged"])

    def test_one_shot_preflight_blocks_ci_and_has_no_automatic_moving(self):
        with tempfile.TemporaryDirectory() as tmp:
            env={**os.environ,"HOME":tmp,"GITHUB_ACTIONS":"true"}
            t=subprocess.run(["bash",str(WRAPPER),"--self-check"],env=env,
                capture_output=True,text=True,timeout=8)
            self.assertEqual(t.returncode,0,(t.stdout,t.stderr))
            self.assertIn("C29_OWNER_SELF_CHECK_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL",t.stdout)
            p=subprocess.run(["bash",str(WRAPPER),"--run"],env=env,
                capture_output=True,text=True,timeout=8)
            self.assertNotEqual(p.returncode,0)
            self.assertIn("C29_OWNER_WSL2_ONLY_NO_SIMULATION",p.stdout+p.stderr)
            self.assertEqual(list(Path(tmp).iterdir()),[])
        s=WRAPPER.read_text()
        for target in ("RMW_IMPLEMENTATION=rmw_cyclonedds_cpp",
              "MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA",
              "ffe0d467e159efcf1b60da6263203d3cee86f9d5",
              "cefe00b6304c7bab0265b7b5d660cfb9a909a3a3",
              "--compact-only", "--verify-compact",
              "C29_OWNER_WSL2_NO_GOAL_L3_CANDIDATE_PASS",
              "C29_OWNER_REQUIRED_SAFETY_CM120_GUARD150_MOVING_NOT_VERIFIED"):
            self.assertIn(target,s)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",s)

if __name__=="__main__":unittest.main()
