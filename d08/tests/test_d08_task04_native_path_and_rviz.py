"""D08 Task04 RED from actual Gazebo #44239202179 and missing RViz topic wiring.

ROS Jazzy native runtime is required for L2; these are only source contracts.
"""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))


def test_native_path_message_must_not_shadow_filesystem_path():
    src=(ROOT/"d08/harness/d08_same_world_replan.py").read_text()
    assert "from pathlib import Path" in src
    assert "out=Path(out)" in src
    assert "from nav_msgs.msg import OccupancyGrid, Odometry, Path as NavPath" in src
    assert 'create_publisher(NavPath,"/axia/d08/official_path_readonly"' in src
    assert "from nav_msgs.msg import OccupancyGrid, Odometry, Path\n" not in src


def test_official_rviz_path_topic_matches_readonly_nav2_action(tmp_path):
    from d08_one_world_official_nav2_launch import (
        create_official_rviz_path_overlay)
    base=tmp_path/"nav2_default_view.rviz"
    base.write_text("""Visualization Manager:
  Displays:
    - Class: rviz_default_plugins/Map
      Name: Global Costmap
      Topic:
        Value: /global_costmap/costmap
    - Class: rviz_default_plugins/Path
      Name: Path
      Topic:
        Value: /plan
""")
    dest=tmp_path/"d08_owner_readonly.rviz"
    created=create_official_rviz_path_overlay(base,dest)
    assert created==dest.resolve()
    out=dest.read_text()
    assert "Value: /axia/d08/official_path_readonly" in out
    assert "Value: /global_costmap/costmap" in out
    assert "Value: /plan\n" not in out
    assert base.read_text().endswith("Value: /plan\n")
    src=(ROOT/"d08/scripts/d08_public_gazebo_l2.py").read_text()
    assert "create_official_rviz_path_overlay" in src
    assert "nav2_default_view.rviz" in src
    assert "rviz_config_file" in src


def test_owner_headless_parity_and_pinned_same_engine():
    source=(ROOT/"d08/scripts/d08_owner_no_goal_bootstrap.sh").read_text()
    workflow=(ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
    launch=(ROOT/"d08/harness/d08_one_world_official_nav2_launch.py").read_text()
    for pin in (
        "94d2dd500cb26027ee9c019f4d3a02029ac615cc",
        "36dbafacb1bc532e92d02371bd70582a61105872561fc9982314854d1c7ebf72",
        "4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf"):
        assert pin in source and pin in workflow
    assert "owner_gui=False" in launch
    assert "rviz_config_file:=" in launch
    assert "use_rviz:=False" in launch
    assert "headless:=True" in launch
    assert "rviz_config_file" in launch
    assert "reset --hard" not in source
    assert "pkill" not in source
    assert "rm -rf" not in source
