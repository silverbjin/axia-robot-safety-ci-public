"""D08 Task04 WSLg GUI: code path is same public source, no moving Goal.

Static controls only; L0 never establishes a WSLg screen-rendering PASS.
"""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))
from d08_one_world_official_nav2_launch import make_official_nav2_command

def test_gui_mode_opt_in_keeps_default_actual_public_ci_headless(tmp_path):
    # Use existing verified XML fixture from the nav2 command static test.
    s=(ROOT/"d08/harness/d08_one_world_official_nav2_launch.py").read_text()
    assert "owner_gui=False" in s
    assert "headless:=False" in s
    assert "use_rviz:=True" in s
    assert "headless:=True" in s
    assert "use_rviz:=False" in s

def test_owner_gui_reuses_same_world_nav2_and_existing_3_path_obs():
    s=(ROOT/"d08/scripts/d08_public_gazebo_l2.py").read_text()
    assert "--owner-gui" in s
    assert "owner_gui" in s and "live_person_range" in s
    assert "D08_OWNER_WSLG_REAL_GUI_REQUESTED" in s
    assert "run_physical_replan" in s
    assert "owner_gui_user_stopped" in s
    assert "D08_OWNER_GUI_CTRLC_ACK" in s
    assert "NavigateToPose.Goal(" not in s

def test_official_action_path_is_published_only_to_readonly_rviz_topic():
    s=(ROOT/"d08/harness/d08_same_world_replan.py").read_text()
    assert 'create_publisher(NavPath,"/axia/d08/official_path_readonly"' in s
    assert "path_pub.publish(path)" in s
    assert "result.result.path" in s
    assert "cmd_vel" not in s or "cmd_vel_published" in s

def test_owner_script_pins_public_source_and_never_deletes_user_work():
    p=ROOT/"d08/scripts/d08_owner_no_goal_bootstrap.sh"
    s=p.read_text()
    assert s.startswith("#!/usr/bin/env bash")
    for opt in ("--self-check","--doctor","--run"):
        assert opt in s
    assert "AXIA_D08_PUBLIC_SHA" in s
    assert "sha256sum -c" in s
    assert "set +u" in s and "/opt/ros/jazzy/setup.bash" in s
    assert "ros2 launch yolo_bringup yolo.launch.py" in s
    assert "--owner-gui" in s
    for bad in ("reset --hard","pkill","rm -rf"):
        assert bad not in s
