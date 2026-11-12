"""Classroom D04 must use the P1/ROS/ONNX owner runner, not fake local .pt assets.

This public L0 regression deliberately does NOT run ROS, Gazebo, WSL2,
private instructor code, model inference, or a robot command.
"""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "axia_d04_classroom_wsl2_once.sh"
UPSTREAM = ROOT / "scripts" / "axia_d04_ros_package_wsl2_once.sh"
PIN = "c775820077917c4da56c6aa60001b224071664b3"
UPSTREAM_GIT_BLOB = "f999dbf0db9fe1f2d63b2a486ed3191a94a15c83"


def test_pinned_upstream_owner_script_matches_public_ci_evidence():
    data = UPSTREAM.read_bytes()
    raw = f"blob {len(data)}\0".encode() + data
    assert hashlib.sha1(raw).hexdigest() == UPSTREAM_GIT_BLOB
    script = data.decode()
    assert "AXIA_D04_PUBLIC_SHA" in script
    assert "AXIA_D04_REPEAT" in script
    assert "PASS_PACKAGED_P1_YOLO_CLEAN_" in script
    assert "gh auth status" in script


def test_classroom_script_syntax_and_static_preflight(tmp_path):
    assert SCRIPT.is_file(), "RED: there is no classroom-specific no-placeholder entrypoint"
    syntax = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert syntax.returncode == 0, syntax.stderr
    result = subprocess.run(
        ["bash", str(SCRIPT), "--self-check"],
        capture_output=True, text=True, timeout=5, cwd=tmp_path
    )
    assert result.returncode == 0, result.stderr
    assert f"D04_CLASSROOM_PUBLIC_SHA={PIN}" in result.stdout
    assert "D04_CLASSROOM_STATIC_PASS" in result.stdout
    assert "GAZEBO_NOT_RUN" in result.stdout


def test_classroom_uses_existing_ros_onnx_demo_not_missing_pt_assets():
    assert SCRIPT.is_file()
    s = SCRIPT.read_text()
    assert "axia_d04_ros_package_wsl2_once.sh" in s
    assert PIN in s
    assert "AXIA_D04_REPEAT" in s
    assert "AXIA_D04_GUI" in s
    assert "axia_licensed_assets" not in s
    assert "yolo_single_image_demo.py" not in s
    assert "pip install ultralytics" not in s
    assert "axia_d04_classroom_wsl2_once.sh" not in s.replace("#!/usr/bin/env bash", "")


def test_ci_is_not_wsl2_and_does_not_start_demo(tmp_path):
    assert SCRIPT.is_file()
    result = subprocess.run(
        ["bash", str(SCRIPT), "--preflight"],
        capture_output=True, text=True, timeout=5, cwd=tmp_path
    )
    assert result.returncode == 2
    assert "D04_CLASSROOM_WSL2_REQUIRED" in result.stdout
    assert "D04_PACKAGE_STATUS=PASS_" not in result.stdout


def test_exact_owner_runner_bash_syntax_and_self_check_do_not_require_ros(tmp_path):
    syntax = subprocess.run(["bash", "-n", str(UPSTREAM)], capture_output=True, text=True)
    assert syntax.returncode == 0, syntax.stderr
    check = subprocess.run(
        ["bash", str(UPSTREAM), "--self-check"],
        cwd=tmp_path, capture_output=True, text=True, timeout=5
    )
    assert check.returncode == 0, check.stderr
    assert "AXIA_D04_PACKAGE_WRAPPER_STATIC_OK" in check.stdout
    assert "G_D04_PACKAGE_RUNTIME=NOT_RUN" in check.stdout
