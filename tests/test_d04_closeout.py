"""D04 closure RED: actual lifecycle shutdown, MOVING person and 3 cold starts.

L0 tests fail before implementation. L2 must exercise actual Nav2/Gazebo/ONNX.
"""
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import sys
import json
import pytest

ROOT = Path(__file__).resolve().parents[1]
S = ROOT/"scripts"
sys.path.insert(0,str(S))


def source(name):
    return (S/name).read_text(encoding="utf-8")


def test_graceful_shutdown_service_before_process_group_sigint():
    t=source("d04_packaged_p1_yolo_gate.py")
    assert "request_nav2_shutdown" in t
    assert t.index("request_nav2_shutdown(") < t.index("_stop_all(proc, verdict)")
    assert '"shutdown_quality": "NOT_EVALUATED"' in t


def test_nav2_lifecycle_helper_uses_real_service_success_not_stdout_guess():
    t=source("d04_nav2_orderly_shutdown.py")
    assert "ManageLifecycleNodes" in t
    assert "ManageLifecycleNodes.Request.SHUTDOWN" in t
    assert "/lifecycle_manager_navigation/manage_nodes" in t
    assert "/lifecycle_manager_localization/manage_nodes" in t
    assert "resp.success" in t or "response.success" in t
    assert "create_publisher(" not in t


def test_motion_metric_rejects_one_frame_and_static_false_positive():
    spec=spec_from_file_location("d04_bbox_motion_gate",S/"d04_bbox_motion_gate.py")
    m=module_from_spec(spec)
    spec.loader.exec_module(m)
    point=lambda stamp,x: {"stamp_ns":stamp,"class_name":"person","class_id":0,
                           "score":0.8,"center_x":x,"center_y":150.0,
                           "size_x":115.0,"size_y":240.0}
    assert not m.motion_evidence([point(1,200)])["passed"]
    assert not m.motion_evidence([point(1_000_000_000+i*300_000_000,200) for i in range(8)])["passed"]
    assert m.motion_evidence([point(1_000_000_000+i*500_000_000,200+4*i) for i in range(8)])["passed"]


def test_real_yolo_watcher_samples_multiple_distinct_stamped_boxes():
    t=source("d04_yolo_person_runtime.py")
    assert "person_samples" in t
    assert "require_motion" in t
    assert "motion_evidence(" in t
    assert "create_publisher(" not in t


def test_stability_requires_three_distinct_real_packaged_launches():
    t=source("d04_packaged_stability_3x.py")
    assert "d04_package_nav2_real_smoke.py" in t
    assert "range(1,4)" in t.replace(" ", "")
    assert "PASS_PACKAGED_OFFICIAL_NAV2_GAZEBO_PERSON" in t
    assert "shutdown_quality" in t
    assert "motion_verified" in t
    assert "create_publisher(" not in t


def test_owner_verdict_shutdown_warning_never_counted_as_complete_pass():
    t=source("d04_packaged_p1_yolo_gate.py")
    assert 'PASS_P1_AND_YOLO_PACKAGE_RUNTIME' in t
    assert '"shutdown_quality"' in t
    assert "WARN_SIGABRT" in t
    assert "PASS_P1_AND_YOLO_PACKAGE_CLEAN_EXIT" in t
