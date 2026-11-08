"""D04 installed package owner-runtime and one-shot WSL2 contract (source only)."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sp = spec_from_file_location("d04_packaged_p1_yolo_gate", SCRIPT_DIR / "d04_packaged_p1_yolo_gate.py")
runtime = module_from_spec(sp)
sp.loader.exec_module(runtime)


def test_packaged_launch_uses_real_ros_package_and_not_yolo_proxy(tmp_path):
    launch=runtime.build_launch_command(
        tmp_path/"axia_tb3_p1.launch.py",
        tmp_path/"model.onnx",
        tmp_path/"walk.dae",
        gui=False)
    assert launch[:4]==["ros2","launch","axia_d04_vision_demo","d04_p1_yolo.launch.py"]
    assert "headless:=true" in launch
    assert "show_image:=false" in launch
    assert not any("cmd_vel" in part for part in launch)
    assert not any("goal" in part.lower() for part in launch)


def test_gui_is_explicit_and_only_changes_visualization(tmp_path):
    launch=runtime.build_launch_command(
        tmp_path/"axia_tb3_p1.launch.py", tmp_path/"model.onnx",
        tmp_path/"walk.dae",gui=True)
    assert "headless:=false" in launch
    assert "show_image:=true" in launch
    assert "use_rviz:=false" in launch


def test_reject_wrong_p1_launch(tmp_path):
    with pytest.raises(ValueError):
        runtime.build_launch_command(
            tmp_path/"unverified.launch.py",tmp_path/"model.onnx",tmp_path/"walk.dae")


def test_owner_script_bash_syntax_and_self_check():
    script=SCRIPT_DIR/"axia_d04_ros_package_wsl2_once.sh"
    assert subprocess.run(["bash","-n",str(script)],capture_output=True).returncode==0
    result=subprocess.run(["bash",str(script),"--self-check"],capture_output=True,text=True)
    assert result.returncode==0
    assert "PACKAGE_WRAPPER_STATIC_OK" in result.stdout


def test_owner_script_exact_pins_no_motion_no_credential_leak():
    src=(SCRIPT_DIR/"axia_d04_ros_package_wsl2_once.sh").read_text()
    assert "AXIA_D04_PUBLIC_SHA" in src
    assert "c1b92d9dd3dd2cd038db16253102542d120ea87e" in src
    assert "94d2dd500cb26027ee9c019f4d3a02029ac615cc" in src
    assert "d04_packaged_p1_yolo_gate.py" in src
    assert "colcon build" in src
    assert "gh auth status" in src
    assert "cd \"$HOME\"" in src  # avoid deleted working-directory warning
    for forbidden in ("ros2 action send_goal", "ros2 topic pub /cmd_vel",
                      "gh pr merge", "git push"):
        assert forbidden not in src


def test_package_verifier_uses_actual_p1_graph_and_yolo_ros_topics():
    src=(SCRIPT_DIR/"d04_packaged_p1_yolo_gate.py").read_text()
    assert "_watch_detections_and_images" in src
    assert "graph_oracle" in src
    assert "core_chain(first[\"graph\"]) == core_chain(after[\"graph\"])" in src
    assert "PASS_P1_AND_YOLO_PACKAGE_RUNTIME" in src
    assert "create_publisher(" not in src
    assert "send_goal_async(" not in src
