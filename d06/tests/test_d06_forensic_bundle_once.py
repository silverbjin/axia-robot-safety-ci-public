"""Contract and real offline fixture for D06 ONE command existing-evidence custody.

No ROS2, Gazebo or GPU is launched by these tests.
"""
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh"


def fake_record(home):
    root = home / "axia_d06_g07_gpu_rtf_evidence"
    d = root / "ab-no-goal-fixture"
    d.mkdir(parents=True)
    verdict = {
        "status": "NO_GOAL_SENSOR_UNSAFE_HOLD",
        "reasons": ["SAFETY_RECEIPT_TTL_300MS_BLOCKED", "RAW_RECEIPT_TTL_300MS_BLOCKED"],
        "goal_sent": False, "fixture_moved": False, "certified_estop": False,
        "dual_topic_required_observation_sec":20,
        "dual_topic_actual_wall_observation_sec":20.008,
        "startup_pre_both_scan_diagnostics":{
            "both_topics_ready":True,
            "pre_ready_raw_first_gap_sec":.434354,
            "pre_ready_breach_evidence_retained":True,
            "pre_ready_observations_not_motion_authority":True
        },
        "rtf_diagnostics": {"ros_clock_rtf": 0.913157, "timing_pattern": "RTF_NORMAL"},
        "metrics": {
            "raw": {"count": 185, "max_receipt_gap_sec": .427761,
                    "first_receipt_ttl_breach_at_index": 11},
            "safety": {"count": 180, "clear_count": 180,
                       "front_median_m": 1.414687, "side_median_m": 2.520466,
                       "max_receipt_gap_sec": .421172,
                       "first_receipt_ttl_breach_at_index": 6}
        },
        "raw_first_gap_diagnostics": {
            "first_gap_index": 11, "first_gap_sec": .390708,
            "paired_safety_receipt_gap_sec": .387036,
            "phase": "BOTH_TOPIC_ACTIVE"
        }
    }
    (d / "nvidia.g07_wslg_sensor_truth.json").write_text(json.dumps(verdict))
    (d / "nvidia.launch.log").write_text(
        "[INFO] [navigation_server]: accepted\n"
        "[WARN] [collision_monitor]: Robot to stop due to AXIA_StopFront polygon\n"
        "[WARN] [safety_supervisor]: HEALTH_BAD_DIAGNOSTIC SCAN_TIMEOUT\n"
        "[INFO] [launch]: SIGINT\n"
        "[ERROR] [collision_monitor-16]: process has died [pid 1760, exit code -11]\n"
        "[ERROR] [gz-21]: process has died [pid 1798, exit code -11]\n"
    )
    (d / "nvidia.run.log").write_text(
        "G07_WSLG_NO_GOAL_SENSOR_UNSAFE_HOLD\nD06_WSLG_NO_GOAL_SENSOR_HOLD_NATIVE_RC_3\n"
    )
    (d / "nvidia.renderer.txt").write_text(
        "OpenGL renderer string: D3D12 (NVIDIA GeForce RTX 2060)\n"
    )
    (d / "nvidia.preflight.txt").write_text(
        "OpenGL renderer string: D3D12 (NVIDIA GeForce RTX 2060)\n"
    )
    # The original Owner already stored a native TAR; collect just its
    # clock/graph/GUI/teardown evidence without another physical run.
    archive = root / "d06-native-original.tar.gz"
    native = {
        "clock_diagnostics.json": '{"status":"READY","clock":{"samples":3}}',
        "p2_graph_diagnostics.json": '{"status":"P2_NO_GOAL_READONLY_READY"}',
        "task04_rviz.log": "GLSL link result: active samplers with a different type\n",
        "task04_gazebo_gui.log": "Loading plugin [gz-rendering-ogre2]\n",
        "teardown.txt": "P2_L2_GRACEFUL_TEARDOWN\n",
        "g07_ordered_shutdown.json": '{"status":"NAV2_LIFECYCLE_SHUTDOWN_ACK","cm_managed_by_navigation":true,"navigation_ack":true,"localization_ack":true,"certified_estop":false}',
        "g07_shutdown_audit.json": '{"status":"SHUTDOWN_CLEAN_CANDIDATE","cm_exit_code":0,"certified_estop":false}',
        "g07_ordered_shutdown.log": 'G07_NAV2_ORDERED_SHUTDOWN navigation_ack=true localization_ack=true',
        "g07_witness_probe_complete.signal":"G07_READONLY_SENSOR_PROBE_FINISHED",
        "g07_witness_stopped.ack":"G07_READONLY_WITNESSES_STOPPED",
        "d06_g07_scan_delivery_layer.json": '{"candidate":"AFTER_NATIVE_TRANSPORT_RX","release":"HOLD","goal_allowed":false}',
        "d06_gz_scan_receipts.jsonl": '{"host_monotonic_sec":100.0,"source_stamp_ns":1000000000}\\n',
        "d06_ros_scan_receipts.jsonl": '{"topic":"raw","host_monotonic_sec":100.1,"source_stamp_ns":1000000000}\\n',
        "d06_gz_clock_receipts.jsonl": '{"host_monotonic_sec":100.0,"sim_stamp_ns":1000000000}\\n',

    }
    with tarfile.open(archive, "w:gz") as tar:
        for name, body in native.items():
            payload = body.encode()
            info = tarfile.TarInfo("d06-test/native/" + name)
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
    import hashlib
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    Path(str(archive)+".sha256").write_text(digest+"  "+str(archive)+"\n")
    with (d / "nvidia.run.log").open("a") as log:
        log.write("D06_WSLG_NO_GOAL_RAW_ARCHIVE="+str(archive)+"\n")
    (d / "nvidia.g07_world.sdf.xacro").write_text("<sdf version='1.10'/>")
    (d / "nvidia.g07_demo_waffle.sdf.xacro").write_text("<sdf version='1.10'/>")
    return d


class ForensicOneShot(unittest.TestCase):
    def test_existing_no_ros_no_gazebo_has_compact_sha256_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            d = fake_record(home)
            env = {"PATH": os.environ["PATH"], "HOME": str(home),
                   "GITHUB_ACTIONS": "true"}
            run = subprocess.run(["bash", str(SCRIPT), "--analyze-existing"],
                                 env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, (run.stdout, run.stderr))
            self.assertIn("D06_FORENSIC_EXISTING_NO_SIM_REPLAY", run.stdout)
            self.assertIn("D06_FORENSIC_ARCHIVE=", run.stdout)
            self.assertIn("D06_FORENSIC_FIRST_SENSOR_FAILURE=SAFETY_RECEIPT_TTL_300MS_BLOCKED", run.stdout)
            root = d.parent
            archive = root / ("d06-forensic-" + d.name + ".tar.gz")
            sha_file = Path(str(archive) + ".sha256")
            self.assertTrue(archive.is_file())
            self.assertTrue(sha_file.is_file())
            verify = subprocess.run(["sha256sum", "-c", str(sha_file)],
                                    capture_output=True, text=True, cwd=root)
            self.assertEqual(verify.returncode, 0, verify.stderr)
            with tarfile.open(archive, "r:gz") as tar:
                members = tar.getnames()
                self.assertIn("forensic/summary.json", members)
                self.assertIn("forensic/first_stop_and_timing.txt", members)
                self.assertIn("forensic/shutdown_context.txt", members)
                self.assertIn("forensic/source_hashes.txt", members)
                self.assertIn("forensic/native_clock_diagnostics.json", members)
                self.assertIn("forensic/native_p2_graph_diagnostics.json", members)
                self.assertIn("forensic/native_render_errors_excerpt.txt", members)
                self.assertIn("forensic/d06_g07_scan_delivery_layer.json", members)
                self.assertIn("forensic/d06_gz_scan_receipts.jsonl", members)
                self.assertIn("forensic/d06_ros_scan_receipts.jsonl", members)
                self.assertIn("forensic/d06_gz_clock_receipts.jsonl", members)
                self.assertIn("forensic/native_teardown_marker.txt", members)
                self.assertIn("forensic/native_nav2_ordered_shutdown.json", members)
                self.assertIn("forensic/native_cm_shutdown_audit.json", members)
                self.assertIn("forensic/native_witness_probe_completed.txt", members)
                self.assertIn("forensic/native_witness_handoff_ack.txt", members)
                summary = json.load(tar.extractfile("forensic/summary.json"))
                self.assertEqual(summary["first_sensor_failure"], "SAFETY_RECEIPT_TTL_300MS_BLOCKED")
                self.assertEqual(summary["process_crashes"], ["collision_monitor", "gazebo_server"])
                self.assertFalse(summary["goal_sent"])
                self.assertTrue(summary["dual_topic_both_topics_ready"])
                self.assertAlmostEqual(summary["pre_ready_raw_gap_sec"],.434354)
                self.assertTrue(summary["pre_ready_breach_evidence_retained"])
                self.assertEqual(summary["dual_topic_required_observation_sec"],20)
                self.assertAlmostEqual(summary["dual_topic_observed_wall_sec"],20.008)
                self.assertIn("forensic/startup_pre_both_scan_diagnostics.json", members)
                self.assertEqual(summary["source"], "EXISTING_LOCAL_EVIDENCE")
                self.assertTrue(summary["source_archive_sha256_verified"])
                self.assertTrue(summary["native_readonly_witness_handoff_ack"])
                self.assertEqual(summary["native_no_goal_navigation_ack"], True)
                self.assertEqual(summary["native_no_goal_localization_ack"], True)
                self.assertEqual(summary["native_no_goal_cm_exit_code"], 0)
                self.assertEqual(summary["native_no_goal_cm_clean_candidate"], False)  # launch exit -11 overrides self-reported audit
                self.assertEqual(summary["native_no_goal_gazebo_server_exit_code"],-11)
                self.assertFalse(summary["native_no_goal_gazebo_server_clean"])
                self.assertFalse(summary["native_no_goal_whole_teardown_clean"])
                self.assertEqual(summary["first_native_crash_layer"],"GAZEBO_OR_CM_SHUTDOWN")
                self.assertFalse(any("native_full" in m or ".sdf.xacro" in m
                                     for m in members))

    def test_actual_cm_clean_launch_can_be_scoped_candidate_even_if_scan_ttl_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            d=fake_record(home)
            (d / "nvidia.launch.log").write_text(
                "[INFO] [collision_monitor-16]: process has finished cleanly [pid 1760]"+chr(10)
                + "[INFO] [gz-21]: process has finished cleanly [pid 1798]"+chr(10))
            run=subprocess.run(["bash",str(SCRIPT),"--analyze-existing"],
                env={"PATH":os.environ["PATH"],"HOME":str(home),"GITHUB_ACTIONS":"true"},
                capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,0,(run.stdout,run.stderr))
            archive=d.parent/("d06-forensic-"+d.name+".tar.gz")
            with tarfile.open(archive,"r:gz") as tar:
                v=json.load(tar.extractfile("forensic/summary.json"))
            self.assertTrue(v["native_no_goal_navigation_ack"])
            self.assertTrue(v["native_no_goal_localization_ack"])
            self.assertEqual(v["native_no_goal_cm_exit_code"],0)
            self.assertTrue(v["native_no_goal_cm_clean_candidate"])
            self.assertEqual(v["native_no_goal_gazebo_server_exit_code"],0)
            self.assertTrue(v["native_no_goal_gazebo_server_clean"])
            self.assertTrue(v["native_no_goal_whole_teardown_clean"])
            self.assertIn("SAFETY_RECEIPT_TTL_300MS_BLOCKED",v["all_sensor_reasons"])
            self.assertFalse(v["no_goal_acceptance"])

    def test_real_zoa_cm_clean_but_gazebo_server_minus11_blocks_whole_shutdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fake_record(Path(tmp))
            (d/"nvidia.launch.log").write_text(
                "[INFO] [collision_monitor-16]: process has finished cleanly [pid 3574]"+chr(10)
                + "[ERROR] [gz-21]: process has died [pid 3623, exit code -11, cmd 'gz sim -r -s /tmp/nav2_5wtxcwad.sdf']"+chr(10)
            )
            result=subprocess.run(["bash",str(SCRIPT),"--analyze-existing"],
                env={"PATH":os.environ["PATH"],"HOME":str(Path(tmp)),"GITHUB_ACTIONS":"true"},
                capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,(result.stdout,result.stderr))
            arc=d.parent/("d06-forensic-"+d.name+".tar.gz")
            with tarfile.open(arc,"r:gz") as tar:
                v=json.load(tar.extractfile("forensic/summary.json"))
            self.assertEqual(v["process_crashes"],["gazebo_server"])
            self.assertTrue(v["native_no_goal_cm_clean_candidate"])
            self.assertEqual(v["native_no_goal_gazebo_server_exit_code"],-11)
            self.assertFalse(v["native_no_goal_whole_teardown_clean"])
            self.assertEqual(v["first_native_crash_layer"],"GAZEBO_SERVER")

    def test_absent_real_evidence_fails_without_simulation(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"PATH": os.environ["PATH"], "HOME": tmp,
                   "GITHUB_ACTIONS": "true"}
            run = subprocess.run(["bash", str(SCRIPT), "--analyze-existing"],
                                 env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 3, (run.stdout, run.stderr))
            self.assertIn("D06_FORENSIC_EXISTING_EVIDENCE_MISSING_NO_GOAL", run.stderr)

    def test_future_nvidia_run_always_packages_on_failure_before_exit(self):
        s = SCRIPT.read_text()
        self.assertIn("collect_and_package", s)
        self.assertIn("trap cleanup EXIT", s)
        self.assertIn("D06_GPU_RTF_NATIVE_SHUTDOWN_SEGV_HOLD", s)
        self.assertIn("D06_FORENSIC_ARCHIVE=", s)
        self.assertIn("--analyze-existing", s)
        self.assertNotIn("YES-P2-G07-GOAL", s)


if __name__ == "__main__":
    unittest.main()
