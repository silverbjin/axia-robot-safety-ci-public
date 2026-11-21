"""C29-01: fail-closed immutable exact-source manifest before any WSL2 delivery.

This never runs ROS/Gazebo. Full L2 in same-world two cold cycles is a
separate required condition, not inferred from previously green empty-world L2.
"""
import copy
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"d06/ci/c29_source_manifest.json"
BASE_WORKFLOW=ROOT/".github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml"
FULL_WORKFLOW=ROOT/".github/workflows/axia-d06-c29-nogoal-full-two-cold-l2.yml"

def gate(m, *, actual=None):
    """One L2 result cannot certify two independent cold runs."""
    required=("student_sha","smoke_blob","guard_blob","public_c28_sha",
              "baseline_l2_workflow_blob","runtime_image_digest",
              "target_rmw","window_sec","scan_ttl_ms","cycle_count")
    if any(not m.get(k) for k in required):
        return "C29_RELEASE_BLOCKED_MANIFEST_INCOMPLETE"
    if m["student_sha"]!="6c79c09d91f13c81961492eb30e66d99d307831c" or (
         m["smoke_blob"]!="cc3c64f7ae769a11d9daad4acdbdb48141253f7c" or
         m["guard_blob"]!="72a117d9a1b22748ffd16171d213916c095a623e"):
        return "C29_RELEASE_BLOCKED_STUDENT_PIN_MISMATCH"
    if m["target_rmw"]!="rmw_fastrtps_cpp":
        return "C29_RELEASE_BLOCKED_RMW_NOT_OWNER_TARGET"
    if (m["window_sec"]!=20 or m["scan_ttl_ms"]!=300 or
        m["cycle_count"]!=2):
        return "C29_RELEASE_BLOCKED_SAFETY_CONTRACT"
    if m.get("wsL2_owner_rmw_verified") is not False:
        return "C29_RELEASE_BLOCKED_OWNER_RMW_SCOPE_UNKNOWN"
    if not actual or len(actual)!=2 or len({r.get("cycle") for r in actual})!=2:
        return "C29_RELEASE_BLOCKED_REAL_L2_TWO_COLD_RESULTS_MISSING"
    checks=("real_gazebo","real_nav2","cm_exit0","navigation_ack",
            "localization_ack","gazebo_native_exit0","scan300","goal_not_sent")
    if any(not all(r.get(k) is True for k in checks) for r in actual):
        return "C29_RELEASE_BLOCKED_REAL_INTEGRATED_L2_FAIL"
    if any(r.get("student_sha")!=m["student_sha"] or
           r.get("rmw")!=m["target_rmw"] for r in actual):
        return "C29_RELEASE_BLOCKED_TESTED_SHA_OR_RMW_MISMATCH"
    # Even 2/2 Linux L2 does NOT prove Windows WSLg NVIDIA.
    return "C29_CI_L2_CANDIDATE_READY_OWNER_WSL2_L3_REQUIRED"

class C29Manifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads(MANIFEST.read_text())

    def test_manifest_exact_sources_and_scope(self):
        m=self.m
        self.assertEqual(m["schema"],"axia.d06.c29.ci-first.v1")
        self.assertEqual(m["student_sha"],"6c79c09d91f13c81961492eb30e66d99d307831c")
        self.assertEqual(m["public_c28_sha"],"ffe0d467e159efcf1b60da6263203d3cee86f9d5")
        self.assertEqual(m["baseline_l2_workflow_blob"],
                         "3d8a69b23147a81a97bb869d6f3d3409819c57d9")
        self.assertEqual(m["runtime_image_digest"],
              "sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e")
        self.assertEqual(m["scan_ttl_ms"],300)
        self.assertEqual(m["window_sec"],20)
        self.assertEqual(m["cycle_count"],2)
        self.assertFalse(m["wsL2_owner_rmw_verified"])
        self.assertEqual(m["moving_goal_scope"],"NOT_TESTED")
        self.assertEqual(m["certified_estop"],False)
        self.assertEqual(m["main_merge_allowed"],False)

    def test_old_positive_C27_empty_world_does_not_pass_release(self):
        self.assertEqual(gate(self.m), "C29_RELEASE_BLOCKED_REAL_L2_TWO_COLD_RESULTS_MISSING")
        one=[{"cycle":1, "real_gazebo":True,"gazebo_native_exit0":True}]
        self.assertEqual(gate(self.m,actual=one),
                         "C29_RELEASE_BLOCKED_REAL_L2_TWO_COLD_RESULTS_MISSING")

    def test_bad_rmw_and_student_sha_fail_closed(self):
        a=copy.deepcopy(self.m);a["target_rmw"]="rmw_cyclonedds_cpp"
        self.assertEqual(gate(a),"C29_RELEASE_BLOCKED_RMW_NOT_OWNER_TARGET")
        a=copy.deepcopy(self.m);a["student_sha"]="0565e580f5b7c80d719960a6046de3e45c8ea477"
        self.assertEqual(gate(a),"C29_RELEASE_BLOCKED_STUDENT_PIN_MISMATCH")

    def test_two_separate_successful_ci_runs_still_require_wsl2_l3(self):
        base={k:True for k in ("real_gazebo","real_nav2","cm_exit0",
                               "navigation_ack","localization_ack",
                               "gazebo_native_exit0","scan300","goal_not_sent")}
        a=[{**base,"cycle":i,"rmw":self.m["target_rmw"],"student_sha":self.m["student_sha"]}
           for i in (1,2)]
        self.assertEqual(gate(self.m,actual=a),
                         "C29_CI_L2_CANDIDATE_READY_OWNER_WSL2_L3_REQUIRED")
        a[1]["cm_exit0"]=False
        self.assertEqual(gate(self.m,actual=a),
                         "C29_RELEASE_BLOCKED_REAL_INTEGRATED_L2_FAIL")

    def test_no_unverified_full_l2_relabelled_in_manifest(self):
        self.assertEqual(self.m["full_l2_2cycles_status"],"NOT_RUN")
        self.assertEqual(self.m["owner_wsl2_l3_status"],"NOT_RUN")
        self.assertEqual(self.m["acceptance"],"HOLD")
        self.assertTrue(BASE_WORKFLOW.is_file())
        self.assertNotIn("C29_RELEASE_CI_PASS",self.m.get("note",""))

if __name__=="__main__": unittest.main()
