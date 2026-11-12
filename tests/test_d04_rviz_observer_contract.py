"""D04 WSL2 RViz observer regression. PUBLIC CI; no ROS/Gazebo processes.

First RED is absence of the saved RViz config and one-click launcher.
GREEN must check read-only displays, topic QoS, overlay env, and
sidecar lifetime only. It is NOT ROS data delivery or CM TTL acceptance.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "rviz/axia_d04_robot_state.rviz"
LAUNCHER = ROOT / "scripts/axia_d04_rviz_observer.sh"
WATCHER = ROOT / "scripts/d04_rviz_hold_observer.py"
OWNER = ROOT / "scripts/axia_d04_classroom_wsl2_once.sh"


def test_rviz_layout_is_valid_saved_read_only_config():
    yaml = pytest.importorskip("yaml", reason="focused D04 public-field-regression installs PyYAML==6.0.2")
    assert CONFIG.is_file(), "RED: no one-click saved .rviz configuration"
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["Visualization Manager"]["Global Options"]["Fixed Frame"] == "odom"
    displays = config["Visualization Manager"]["Displays"]
    classes = {x["Class"]: x for x in displays}
    assert "rviz_default_plugins/RobotModel" in classes
    assert "rviz_default_plugins/TF" in classes
    assert "rviz_default_plugins/LaserScan" in classes
    assert "rviz_default_plugins/Image" in classes
    assert "rviz_default_plugins/Odometry" in classes
    assert classes["rviz_default_plugins/RobotModel"]["Description Topic"]["Value"] == "/robot_description"
    assert classes["rviz_default_plugins/LaserScan"]["Topic"]["Value"] == "/scan"
    assert classes["rviz_default_plugins/LaserScan"]["Topic"]["Reliability Policy"] == "Best Effort"
    images = [x for x in displays if x["Class"] == "rviz_default_plugins/Image"]
    assert {x["Topic"]["Value"] for x in images} == {"/camera/image_raw", "/yolo/cam0/debug_image"}
    assert all(x["Topic"]["Reliability Policy"] == "Best Effort" for x in images)
    assert all(x.get("Enabled", False) for x in images)
    assert "/tf" in CONFIG.read_text() or "rviz_default_plugins/TF" in classes
    assert not any("Publish" in str(tool) or "Goal" in str(tool) or "InitialPose" in str(tool)
                   for tool in config["Visualization Manager"]["Tools"])
    assert "nav2_rviz_plugins/Navigation 2" not in CONFIG.read_text()


def test_rviz_launcher_installs_one_click_config_without_ros(tmp_path):
    assert LAUNCHER.is_file(), "RED: no one-click RViz installer"
    assert subprocess.run(["bash", "-n", str(LAUNCHER)], capture_output=True).returncode == 0
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["AXIA_D04_RVIZ_ROS_SETUP"] = str(tmp_path / "not-installed/setup.bash")
    proc = subprocess.run(
        ["bash", str(LAUNCHER), "--install", str(CONFIG)],
        cwd=tmp_path, env=env, text=True, capture_output=True, timeout=10,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    local_config = tmp_path / ".local/share/axia-d04/rviz/axia_d04_robot_state.rviz"
    shortcut = tmp_path / "Desktop/AXIA-D04-RViz.desktop"
    assert local_config.read_bytes() == CONFIG.read_bytes()
    assert shortcut.is_file()
    assert "Exec=" in shortcut.read_text()
    assert "axia-d04-rviz" in shortcut.read_text()
    assert not any("rm -rf" in s for s in LAUNCHER.read_text().splitlines())
    doctor = subprocess.run(
        ["bash", str(LAUNCHER), "--doctor"], cwd=tmp_path, env=env,
        text=True, capture_output=True, timeout=10,
    )
    assert doctor.returncode == 2
    assert "D04_RVIZ_ROS_OVERLAY_MISSING" in doctor.stdout


def test_rviz_launcher_has_isolated_domain_and_no_command_outputs():
    assert LAUNCHER.is_file()
    content = LAUNCHER.read_text()
    assert "ROS_DOMAIN_ID=40" in content
    assert "ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST" in content
    assert "rviz2 -d" in content
    for forbidden in ("ros2 action send_goal", "ros2 topic pub /cmd_vel", "sudo apt", "SIGKILL", "AXIA_D04_REPEAT=3"):
        assert forbidden not in content


def test_hold_sidecar_launches_once_and_terminates_only_its_rviz(tmp_path):
    assert WATCHER.is_file(), "RED: no lifecycle-bound GUI_DEMO_HOLD RViz observer"
    launch = tmp_path / "rviz_mock.sh"
    trace = tmp_path / "rviz_launches.log"
    launch.write_text(
        "#!/usr/bin/env bash\n"
        "echo START >> \"$AXIA_TEST_RVIZ_TRACE\"\n"
        "exec sleep 15\n"
    )
    launch.chmod(0o755)
    env = os.environ.copy()
    env["AXIA_TEST_RVIZ_TRACE"] = str(trace)
    log = tmp_path / "observer.log"
    lines = "\n".join((
        "[D04][LAUNCH] Starting",
        "[D04][GUI_DEMO_HOLD] START",
        "[D04][GUI_DEMO_HOLD] RUNNING elapsed=10s",
        "[D04][GUI_DEMO_HOLD] DONE",
        "[D04][SHUTDOWN] Stopping",
    )) + "\n"
    out = subprocess.run(
        [sys.executable, str(WATCHER), "--launcher", str(launch), "--log", str(log)],
        input=lines, text=True, capture_output=True, cwd=tmp_path, env=env, timeout=8,
    )
    assert out.returncode == 0, out.stderr
    assert "D04_RVIZ_OBSERVER_LAUNCHED" in out.stdout
    assert trace.read_text().strip() == "START"
    assert "[D04][SHUTDOWN]" in out.stdout
    assert "D04_RVIZ_OBSERVER_STOPPED" in out.stdout
    assert "D04_PACKAGE_STATUS=PASS" not in out.stdout


def test_owner_does_not_change_exact_p1_gate_and_uses_hold_observer():
    assert "d04_rviz_hold_observer.py" in OWNER.read_text()
    assert "axia_d04_rviz_observer.sh" in OWNER.read_text()
    assert "axia_d04_robot_state.rviz" in OWNER.read_text()
    assert "AXIA_D04_RVIZ_AUTO" in OWNER.read_text()
    assert "AXIA_D04_PUBLIC_SHA" in OWNER.read_text()
    assert "axia_d04_ros_package_wsl2_once.sh" in OWNER.read_text()
    assert "AXIA_D04_DEMO_HOLD_S" in OWNER.read_text()


def test_rviz_guide_exists_and_explains_first_failure_without_safety_claim():
    guide = ROOT / "docs/D04_RVIZ_ROBOT_STATE_GUIDE_KO.md"
    assert guide.is_file(), "RED: RViz inspection tutorial not published"
    text = guide.read_text()
    for token in ("RobotModel", "LaserScan", "/scan", "/tf", "/odom", "/camera/image_raw",
                  "/yolo/cam0/debug_image", "GUI_DEMO_HOLD", "ROS_DOMAIN_ID=40",
                  "SW STOP", "E-Stop", "NO_GOAL", ".desktop"):
        assert token in text, token
