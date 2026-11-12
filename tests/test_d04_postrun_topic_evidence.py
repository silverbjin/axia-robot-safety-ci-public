"""Regression for user seeing unknown D04 topics AFTER a successful one-shot.

This is L0 post-run evidence assessment, not ROS/Gazebo execution.
The real gate is lifecycle-owned and uses ROS_DOMAIN_ID=40.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
READER=ROOT/"scripts/d04_classroom_read_evidence.py"
GATE=ROOT/"scripts/d04_packaged_p1_yolo_gate.py"

def fixture(root:Path, *, passing=True):
    live=root/"round-1"/"live"
    live.mkdir(parents=True)
    payload={
      "status": "PASS_P1_AND_YOLO_PACKAGE_CLEAN_EXIT" if passing else "BLOCKED_SHUTDOWN_UNCLEAN",
      "graph_stable": True,
      "person_valid": True, "rgb_valid": True, "debug_image_saved":True,
      "motion_verified":True, "goal_sent":False,"fault_injected":False,
      "shutdown_quality": "PASS_NAV2_MANAGED_NO_SIGABRT" if passing else "WARN_SIGABRT",
      "shutdown_service":{"passed": passing},
      "vision":{"camera_frames":12,"detection_frames":5,"debug_frames":5,
                "motion_evidence":{"passed":True}}
    }
    (live/"verdict.json").write_text(json.dumps(payload))
    (live/"person_samples.json").write_text(json.dumps({"samples":[{"class_name":"person"}]}))
    (live/"debug_frame.png").write_bytes(b"mock-not-a-real-image")
    (root/"owner_summary.json").write_text(json.dumps(
        {"status":"PASS_PACKAGED_P1_YOLO_CLEAN_1X" if passing else "BLOCKED",
         "gate_exit":0 if passing else 2, "wrapper_exit":0 if passing else 2}))
    (root/"repeat_summary.json").write_text(json.dumps(
        {"passed":passing,"completed_rounds":1,"required_rounds":1}))
    return root

def invoke(*args):
    return subprocess.run([sys.executable,str(READER),*args],
                          capture_output=True,text=True,timeout=5)

def test_original_live_gate_uses_isolated_domain_then_managed_shutdown():
    s=GATE.read_text()
    assert 'env["ROS_DOMAIN_ID"] = "40"' in s
    assert 'env["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"' in s
    assert 'env["GZ_PARTITION"]' in s
    assert 'GUI_DEMO_HOLD' in s
    assert s.index('GUI_DEMO_HOLD') < s.index('request_nav2_shutdown(env,out,timeout_s=65)')
    assert s.index('request_nav2_shutdown(env,out,timeout_s=65)') < s.index('_stop_all(proc, verdict)')

def test_postrun_reader_proves_saved_delivery_but_not_live_topics(tmp_path):
    root=fixture(tmp_path/"evidence")
    r=invoke("--evidence",str(root))
    assert r.returncode==0,r.stdout+r.stderr
    assert "D04_RECORDED_CAMERA_FRAMES=12" in r.stdout
    assert "D04_RECORDED_DETECTION_FRAMES=5" in r.stdout
    assert "D04_RECORDED_DEBUG_FRAMES=5" in r.stdout
    assert "D04_RECORDED_RGB_BRIDGE_YOLO=PASS_FROM_SAVED_VERDICT" in r.stdout
    assert "D04_AFTER_MANAGED_SHUTDOWN_TOPICS=NOT_EXPECTED" in r.stdout
    assert "D04_REALTIME_ROS_RECHECK=NOT_RUN" in r.stdout

def test_postrun_reader_rejects_bad_shutdown(tmp_path):
    r=invoke("--evidence",str(fixture(tmp_path/"evidence",passing=False)))
    assert r.returncode==2
    assert "D04_RECORDED_RGB_BRIDGE_YOLO=UNVERIFIED" in r.stdout

def test_postrun_reader_rejects_missing_evidence_without_relaunch(tmp_path):
    r=invoke("--evidence",str(tmp_path/"missing"))
    assert r.returncode==2
    assert "D04_EVIDENCE_MISSING" in r.stdout
    assert "can't open file" not in r.stderr
