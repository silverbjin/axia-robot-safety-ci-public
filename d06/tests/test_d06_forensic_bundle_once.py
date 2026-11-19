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


class LocalizationFirstTimeoutCompactContract(unittest.TestCase):
    def test_owner_forensic_retains_parameter_service_probe_verdict(self):
        text=SCRIPT.read_text()
        self.assertIn('summary["native_no_goal_localization_parameter_probe"]=',text)
        self.assertIn('nav.get("localization_parameter_probe")',text)
        self.assertIn('summary["native_no_goal_localization_response_elapsed_sec"]=',text)
        self.assertIn('summary["native_no_goal_localization_request_sent"]=',text)
        self.assertIn("D06_FORENSIC_LOCALIZATION_FIRST_TIMEOUT_PROBE=",text)
        self.assertIn("D06_G07_WSLG_READONLY_WITNESS_HANDOFF_DONE_BEFORE_SHUTDOWN",
                      (Path(__file__).resolve().parents[2]/
                       "d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh").read_text())

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

    def test_fr1_fresh_scan_clear_but_native_witness_134_gazebo_minus11_stays_hold(self):
        # Exact, distinct facts from actual Owner fr1FN4YJ archive. No ROS
        # or Gazebo is started in this L0 replay.
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            d=fake_record(home)
            v=json.loads((d/"nvidia.g07_wslg_sensor_truth.json").read_text())
            v["status"]="NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE"
            v["reasons"]=[]
            v["dual_topic_actual_wall_observation_sec"]=20.003
            v["metrics"]["raw"].update({"count":171,"max_receipt_gap_sec":.255948,
                 "first_receipt_ttl_breach_at_index":None})
            v["metrics"]["safety"].update({"count":171,"clear_count":171,
                 "max_receipt_gap_sec":.256287,
                 "first_receipt_ttl_breach_at_index":None})
            (d/"nvidia.g07_wslg_sensor_truth.json").write_text(json.dumps(v))
            (d/"nvidia.launch.log").write_text(
                "[INFO] [collision_monitor-16]: process has finished cleanly [pid 1650]\n"
                "[ERROR] [p2_base_guard_node-20]: process has died [pid 1656, exit code 1]\n"
                "[ERROR] [p2_supervisor_node-19]: process has died [pid 1655, exit code 1]\n"
                "[ERROR] [gz-21]: process has died [pid 1682, exit code -11]\n"
            )
            old=(d/"nvidia.run.log").read_text()
            (d/"nvidia.run.log").write_text(
                "D06_G07_WSLG_WITNESS_NONCLEAN_HANDOFF_HOLD\n"
                "D06_G07_RX_WITNESS_EXIT ros=0 native=134\n"
                +old)
            source=d.parent/"d06-native-original.tar.gz"
            values={}
            with tarfile.open(source,"r:gz") as src:
                for entry in src:
                    if entry.isfile():
                        values[entry.name]=src.extractfile(entry).read()
            values.pop("d06-test/native/g07_witness_stopped.ack",None)
            values["d06-test/native/d06_gz_scan_rx.log"]=(
                b"terminate called without an active exception\n")
            with tarfile.open(source,"w:gz") as target:
                for name,content in values.items():
                    item=tarfile.TarInfo(name)
                    item.size=len(content)
                    target.addfile(item,io.BytesIO(content))
            import hashlib
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            Path(str(source)+".sha256").write_text(digest+"  "+str(source)+"\n")
            run=subprocess.run(["bash",str(SCRIPT),"--analyze-existing"],
                env={"PATH":os.environ["PATH"],"HOME":str(home),
                     "GITHUB_ACTIONS":"true"},text=True,capture_output=True,timeout=15)
            self.assertEqual(run.returncode,0,(run.stdout,run.stderr))
            target=d.parent/("d06-forensic-"+d.name+".tar.gz")
            with tarfile.open(target,"r:gz") as tar:
                summary=json.load(tar.extractfile("forensic/summary.json"))
            self.assertEqual(summary["sensor_status"],
                             "NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE")
            self.assertEqual(summary["native_ros_witness_exit_code"],0)
            self.assertEqual(summary["native_gz_witness_exit_code"],134)
            self.assertEqual(summary["native_gz_witness_first_error"],
                             "terminate called without an active exception")
            self.assertFalse(summary["native_readonly_witness_handoff_ack"])
            self.assertEqual(summary["native_no_goal_cm_exit_code"],0)
            self.assertEqual(summary["native_no_goal_gazebo_server_exit_code"],-11)
            self.assertFalse(summary["native_no_goal_whole_teardown_clean"])
            self.assertFalse(summary["no_goal_acceptance"])

    def test_tcljt2qc_early_failure_preserves_first_owner_log_line_and_stage(self):
        # TCljt2Qc original user archive was 1.3KB and had only summary +
        # original nvidia.run.log SHA256. The actual log bytes were NOT
        # uploaded. A synthetic log exercises that confirmed custody gap,
        # not an invented real-world root cause.
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp); d=fake_record(home)
            (d/"nvidia.g07_wslg_sensor_truth.json").unlink()
            (d/"nvidia.launch.log").unlink()
            (d/"nvidia.run.log").write_text(
                "D06_WSLG_NO_GOAL_REAL_SETUP_BEGIN\n"
                "D06_G07_NATIVE_PROBE_IMPORT_MISSING_NO_GOAL\n"
                "D06_WSLG_NO_GOAL_SENSOR_HOLD_NATIVE_RC_3\n")
            (d/"attempt_state.txt").write_text(
                "phase=OWNER_FINISHED\nowner_rc=3\nouter_rc=3\nmode=--nvidia-causal\n")
            env={"PATH":os.environ["PATH"],"HOME":str(home),
                 "GITHUB_ACTIONS":"true"}
            run=subprocess.run(["bash",str(SCRIPT),"--analyze-existing"],
                env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,0,(run.stdout,run.stderr))
            archive=d.parent/("d06-forensic-"+d.name+".tar.gz")
            with tarfile.open(archive,"r:gz") as tf:
                summary=json.load(tf.extractfile("forensic/summary.json"))
                detail=tf.extractfile("forensic/first_preflight_or_owner_failure.txt").read().decode()
                state=tf.extractfile("forensic/attempt_state.txt").read().decode()
            self.assertEqual(summary["first_sensor_failure"],"EVIDENCE_INCOMPLETE")
            self.assertFalse(summary["source_archive_sha256_verified"])
            self.assertEqual(summary["first_failure_stage"],"OWNER_FINISHED")
            self.assertEqual(summary["first_owner_failure_marker"],
                             "D06_G07_NATIVE_PROBE_IMPORT_MISSING_NO_GOAL")
            self.assertEqual(summary["owner_exit_code"],3)
            self.assertIn("D06_G07_NATIVE_PROBE_IMPORT_MISSING_NO_GOAL",detail)
            self.assertIn("owner_rc=3",state)
            self.assertLess(len(detail),18000)
            self.assertFalse(summary["no_goal_acceptance"])

    def test_tcljt2qc_missing_log_reports_missing_not_fake_root_cause(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fake_record(Path(tmp))
            (d/"nvidia.g07_wslg_sensor_truth.json").unlink()
            (d/"nvidia.run.log").unlink()
            (d/"nvidia.launch.log").unlink()
            env={"PATH":os.environ["PATH"],"HOME":str(Path(tmp)),
                 "GITHUB_ACTIONS":"true"}
            run=subprocess.run(["bash",str(SCRIPT),"--analyze-existing"],
                env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,0,(run.stdout,run.stderr))
            archive=d.parent/("d06-forensic-"+d.name+".tar.gz")
            with tarfile.open(archive,"r:gz") as tf:
                summary=json.load(tf.extractfile("forensic/summary.json"))
                excerpt=tf.extractfile("forensic/first_preflight_or_owner_failure.txt").read().decode()
            self.assertEqual(summary["first_owner_failure_marker"],
                             "ORIGINAL_OWNER_LOG_UNAVAILABLE")
            self.assertIn("ORIGINAL_OWNER_LOG_UNAVAILABLE",excerpt)
            self.assertIsNone(summary["owner_exit_code"])
            self.assertFalse(summary["no_goal_acceptance"])

    def test_tcljt2qc_exact_existing_directory_selected_not_unrelated_newer_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            previous=fake_record(home)
            target=previous.parent/"ab-no-goal-TCljt2Qc"
            target.mkdir()
            (target/"nvidia.run.log").write_text(
                "D06_G07_NATIVE_PROBE_IMPORT_MISSING_NO_GOAL\n")
            (target/"attempt_state.txt").write_text(
                "phase=OWNER_FINISHED\nowner_rc=3\nouter_rc=3\nmode=--nvidia-causal\n")
            env={"PATH":os.environ["PATH"],"HOME":str(home),
                 "GITHUB_ACTIONS":"true",
                 "AXIA_D06_FORENSIC_TARGET":"ab-no-goal-TCljt2Qc"}
            run=subprocess.run(["bash",str(SCRIPT),"--analyze-existing"],
                env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,0,(run.stdout,run.stderr))
            self.assertIn("ab-no-goal-TCljt2Qc",run.stdout)
            archive=target.parent/"d06-forensic-ab-no-goal-TCljt2Qc.tar.gz"
            with tarfile.open(archive,"r:gz") as tf:
                summary=json.load(tf.extractfile("forensic/summary.json"))
            self.assertEqual(summary["first_owner_failure_marker"],
                             "D06_G07_NATIVE_PROBE_IMPORT_MISSING_NO_GOAL")
            self.assertEqual(summary["sensor_status"],"UNMEASURED")
            self.assertFalse(summary["source_archive_sha256_verified"])

    def test_replay_target_path_traversal_denied_before_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);fake_record(home)
            env={"PATH":os.environ["PATH"],"HOME":str(home),
                 "GITHUB_ACTIONS":"true",
                 "AXIA_D06_FORENSIC_TARGET":"../another_directory"}
            run=subprocess.run(["bash",str(SCRIPT),"--analyze-existing"],
                env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,3,(run.stdout,run.stderr))
            self.assertIn("D06_FORENSIC_INVALID_TARGET_NO_GOAL",run.stderr)

    def test_enriched_tcljt2qc_archive_must_never_overwrite_original_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=fake_record(Path(tmp))
            original=d.parent/("d06-forensic-"+d.name+".tar.gz")
            preserved=b"ORIGINAL_IMMUTABLE_TCLJT2QC_EVIDENCE"
            original.write_bytes(preserved)
            original_sha=__import__("hashlib").sha256(original.read_bytes()).hexdigest()
            env={"PATH":os.environ["PATH"],"HOME":str(Path(tmp)),
                 "GITHUB_ACTIONS":"true",
                 "AXIA_D06_FORENSIC_TARGET":d.name}
            run=subprocess.run(["bash",str(SCRIPT),"--analyze-existing"],
                 env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,0,(run.stdout,run.stderr))
            self.assertEqual(original.read_bytes(),preserved)
            self.assertEqual(__import__("hashlib").sha256(original.read_bytes()).hexdigest(),original_sha)
            emitted=run.stdout.split("D06_FORENSIC_ARCHIVE=")[-1].splitlines()[0].strip()
            self.assertNotEqual(Path(emitted),original)
            self.assertIn("-recovered-",Path(emitted).name)
            with tarfile.open(emitted,"r:gz") as tf:
                self.assertIn("forensic/first_preflight_or_owner_failure.txt",tf.getnames())
            side=Path(emitted+".sha256")
            self.assertTrue(side.is_file())

    def test_launch_trap_records_original_failure_phase_before_archive(self):
        source=SCRIPT.read_text()
        self.assertIn("D06_STAGE=GPU_PREFLIGHT",source)
        self.assertIn("D06_STAGE=OWNER_RUNNING",source)
        self.assertIn("D06_STAGE=OWNER_FINISHED",source)
        self.assertIn('printf "phase=%s\\nowner_rc=%s\\nouter_rc=%s\\nmode=%s\\n"',source)
        self.assertIn("first_preflight_or_owner_failure.txt",source)

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


    def test_r6_actual_first_scan_gate_is_not_outer_archive_phase_and_gz_crash_has_no_stack(self):
        """Exact 2026-11-19 WSLg r6YhIvPx numeric facts, no real ROS/Gazebo.
        This is a regression contract, NOT a simulated performance recovery.
        """
        with tempfile.TemporaryDirectory() as tmp:
            d=fake_record(Path(tmp))
            verdict=json.loads((d/"nvidia.g07_wslg_sensor_truth.json").read_text())
            verdict["reasons"]=["SAFETY_RECEIPT_TTL_300MS_BLOCKED"]
            verdict["metrics"]["raw"].update({
                "count":151,"max_receipt_gap_sec":.297708,
                "first_receipt_ttl_breach_at_index":None})
            verdict["metrics"]["safety"].update({
                "count":150,"clear_count":150,"max_receipt_gap_sec":.303153,
                "first_receipt_ttl_breach_at_index":129})
            verdict["rtf_diagnostics"]["ros_clock_rtf"]=.752343
            verdict["scan_receipts_compact"]={
                "raw":None,"safety":{
                    "before":{"host_monotonic_sec":7964.014425,
                              "source_stamp_ns":68901000000},
                    "after":{"host_monotonic_sec":7964.317578,
                             "source_stamp_ns":69000000000},
                    "gap_sec":.303153}}
            (d/"nvidia.g07_wslg_sensor_truth.json").write_text(
                json.dumps(verdict))
            (d/"nvidia.launch.log").write_text(
                "[INFO] [collision_monitor-16]: process has finished cleanly [pid 222]"+chr(10)+
                "[ERROR] [gz-21]: process has died [pid 111, exit code -11]"+chr(10))
            (d/"attempt_state.txt").write_text(
                "phase=NATIVE_ARCHIVE_VALIDATION"+chr(10)+
                "owner_rc=3"+chr(10)+"outer_rc=3"+chr(10)+
                "mode=--nvidia-causal"+chr(10))
            run=subprocess.run(["bash",str(SCRIPT),"--analyze-existing"],
                env={"PATH":os.environ["PATH"],"HOME":str(Path(tmp)),
                     "GITHUB_ACTIONS":"true"},
                capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,0,(run.stdout,run.stderr))
            arc=d.parent/("d06-forensic-"+d.name+".tar.gz")
            with tarfile.open(arc,"r:gz") as tar:
                report=json.load(tar.extractfile("forensic/summary.json"))
            self.assertEqual(report["first_failure_stage"],
                             "NATIVE_ARCHIVE_VALIDATION")
            self.assertEqual(report["first_actionable_safety_gate"],
                             "SAFETY_RECEIPT_TTL_300MS_BLOCKED")
            self.assertEqual(report["native_shutdown_first_crash"],
                             "GAZEBO_SERVER")
            self.assertEqual(report["gazebo_server_crash_stack"],
                             "NOT_CAPTURED")
            self.assertFalse(report["causal_root_confirmed"])
            self.assertAlmostEqual(
                report["safety"]["max_receipt_gap_sec"],.303153)
            self.assertEqual(report["native_no_goal_gazebo_server_exit_code"],-11)
            self.assertFalse(report["no_goal_acceptance"])


if __name__ == "__main__":
    unittest.main()
