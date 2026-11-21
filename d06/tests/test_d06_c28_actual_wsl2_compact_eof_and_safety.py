"""C28: regress a real WSL2 C27 compact evidence defect without a replay.
Exact 2026-11-21 owner failure numbers are synthetic metadata, never raw private logs.
"""
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
SCRIPT=ROOT/"d06/scripts/axia_d06_c27_owner_wsl2_nogoal_once.sh"


def compact(items):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        raw=root/"original.tar.gz"
        with tarfile.open(raw,"w:gz") as tf:
            for name,value in items.items():
                data=value.encode("utf-8")
                ti=tarfile.TarInfo("original/native/"+name)
                ti.size=len(data)
                tf.addfile(ti,io.BytesIO(data))
        Path(str(raw)+".sha256").write_text(
            hashlib.sha256(raw.read_bytes()).hexdigest()+"  "+str(raw)+"\n")
        p=subprocess.run(["bash",str(SCRIPT),"--compact-only",str(raw)],
            env={**os.environ,"HOME":tmp,"GITHUB_ACTIONS":"true"},
            capture_output=True,text=True,timeout=20)
        if p.returncode: return p,None,None
        out=next((root/"axia_d06_c27_compact").glob("*.tar.gz"))
        with tarfile.open(out,"r:gz") as tf:
            content={m.name:tf.extractfile(m).read().decode("utf-8","replace")
                     for m in tf.getmembers() if m.isfile()}
        return p,content,json.loads(content["summary.txt"].splitlines()[0])


class C28ActualWsl2FirstFailure(unittest.TestCase):
    def test_native_gz_exit_last_100kb_not_first_100kb(self):
        # Historical C27 compact used fh.read(100001), then tail(lines);
        # that discards the actual native end-of-log on long ROS launches.
        preamble="[INFO] [scan]: benign startup event\n" * 5100
        final="[ERROR] [gz-21]: process has died [pid 2299, exit code -11]\n"
        p,files,summary=compact({"launch.log":preamble+final,
            "teardown.txt":"P2_L2_FORCED_TEARDOWN\n"})
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("exit code -11",files["launch_tail.log"])
        self.assertTrue(summary["native_gz_died_marker"])
        self.assertFalse(summary["native_gz_exit0_marker"])
        self.assertTrue(summary["forced_teardown"])
        self.assertIn("D06_C28_EOF_BOUNDARY_PRESERVED_NO_SIM",p.stdout)

    def test_actual_safe_ttl_first_failure_and_nav_shutdown_hold_both_preserved(self):
        # Numbers are from verified C27 small TAR; fields are not imagined.
        sensor={
            "goal_sent":False, "fixture_moved":False, "status":"NO_GOAL_SENSOR_UNSAFE_HOLD",
            "metrics":{"raw":{"max_receipt_gap_sec":0.358830,
                              "first_receipt_ttl_breach_at_index":69},
                       "safety":{"max_receipt_gap_sec":0.357472,
                                 "first_receipt_ttl_breach_at_index":108}},
            "raw_first_gap_diagnostics":{"first_gap_sec":0.316032}}
        nav={"status":"BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT",
             "navigation_service_status":"SERVICE_TIMEOUT",
             "navigation_ack":False,"localization_ack":False,
             "navigation_response_elapsed_sec":40.000851}
        cm={"status":"BLOCKED_CM_SHUTDOWN_UNVERIFIED","cm_exit_code":None}
        p,files,summary=compact({
            "launch.log":"[WARN] first SCAN_TIMEOUT 300ms\n" +
                "[ERROR] [lifecycle_manager-17]: collision_monitor heartbeat lost\n",
            "g07_wslg_sensor_truth.json":json.dumps(sensor),
            "g07_ordered_shutdown.json":json.dumps(nav),
            "g07_shutdown_audit.json":json.dumps(cm),
            "teardown.txt":"P2_L2_FORCED_TEARDOWN\n"})
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(summary["first_failure"],"RAW_SCAN_RECEIPT_TTL_300MS")
        self.assertEqual(summary["navigation_service_status"],"SERVICE_TIMEOUT")
        self.assertIsNone(summary["cm_exit_code"])
        self.assertFalse(summary["native_gz_exit0_marker"])
        self.assertFalse(summary["release_authorized"])
        self.assertIn("D06_C28_FORCED_TEARDOWN_AND_SCAN_TTL_HOLD",p.stdout)
        self.assertIn("ordered_shutdown.json",files)

    def test_original_owner_failure_tail_can_be_recovered_without_simulation(self):
        p,files,_=compact({
            "launch.log":"[INFO] [gz-1]: process started with pid [1234]\n",
            "g07_ordered_shutdown.log":"Service timeout from navigation lifecycle manager\n",
            "owner_no_goal.log":"G07_NO_GOAL_NATIVE_NAV2_ORDERED_SHUTDOWN_BLOCKED\n",
            "teardown.txt":"P2_L2_FORCED_TEARDOWN\n"})
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("SERVICE",files["ordered_shutdown_log_tail.log"].upper())
        self.assertIn("ORDERED_SHUTDOWN_BLOCKED",files["owner_log_tail.log"])
        self.assertNotIn("G07_GAZEBO_SERVER_NATIVE_EXIT0_BEFORE_GROUP_SIGINT",p.stdout)
        self.assertIn("D06_C27_COMPACT_ONLY_NO_GAZEBO_RUN",p.stdout)


if __name__=="__main__":
    unittest.main()
