"""D06 public main: verified read-only ROS L1 observer; NO Goal/Guard admission."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MON=ROOT/"d06/live/d06_readonly_monitor.py"
PROBE=ROOT/"d06/live/d06_ros_l1_visual_probe.py"
RVIZ=ROOT/"d06/rviz/d06_safety_bubble.rviz"
WF=ROOT/".github/workflows/d06-readonly-observer-main-ci.yml"

def test_no_new_robot_publisher_and_explicit_annotation_only():
    src=MON.read_text()
    nodes=ast.parse(src)
    pubs=[n for n in ast.walk(nodes) if isinstance(n,ast.Call)
       and isinstance(n.func,ast.Attribute) and n.func.attr=="create_publisher"]
    assert len(pubs)==1
    assert "MarkerArray" in ast.unparse(pubs[0])
    assert "/axia/d06/rviz/bubble" in ast.unparse(pubs[0])
    for forbidden in ("send_goal_async(", "create_publisher(Twist",
                      "ros2 action send_goal", "stop_owned("):
        assert forbidden not in src
    assert "NOT_OFFICIAL_CM" in src and "NOT_CM_VERDICT" in src

def test_readonly_real_ros_probe_distinguishes_actual_l1_from_g07():
    src=PROBE.read_text()
    for expect in ("real ROS", "goal_sent", "cmd_vel_published",
                   "gazebo_actual", "count_publishers(\"/cmd_vel\")",
                   "D06_READONLY_REAL_ROS_L1_PASS"):
        assert expect in src
    assert "send_goal_async(" not in src
    assert "PASS_READONLY_REAL_ROS_L1" in src

def test_rviz_config_is_educational_not_control():
    src=RVIZ.read_text()
    for need in ("/scan", "/odom", "/axia/d06/rviz/bubble",
                 "rviz_default_plugins/MarkerArray"):
        assert need in src
    assert "/cmd_vel" not in src

def test_workflow_only_public_actual_ros_l1_and_no_private_checkout():
    src=WF.read_text()
    for forbidden in ("axia-instructor-sealed", "AXIA_CLOUD_CI",
                     "repository: silverbjin/axia-robot-safety-instructor",
                     "YES-P2-G07-GOAL", "d06_gazebo_rviz_owner_wsl2_once.sh"):
        assert forbidden not in src
    assert "D06_PUBLIC_READONLY_ROS_L1_PASS" in src
    assert "D06_WSLG_G07_L3_HOLD" in src
