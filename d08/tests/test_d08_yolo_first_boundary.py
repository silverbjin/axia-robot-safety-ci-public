"""Task04 regression: zero DetectionArray must show first native runtime failure.

Source-only L0; does not claim a running YOLO/ROS node.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml"
PROBE=ROOT/"d08/scripts/d08_ui9_yolo_replay_probe.py"

def test_zero_detection_preserves_native_yolo_logs_and_ros_graph():
    s=WF.read_text()
    assert "D08_YOLO_DETECTION_FIRST_BOUNDARY" in s
    assert "D08_YOLO_LAUNCH_EXITED_BEFORE_REPLAY" in s
    assert "tail -n 140 /tmp/ui9_yolo_runtime.log" in s
    assert "ros2 node list" in s and "ros2 topic list -t" in s
    assert "ldd /tmp/axia_ui9_yolo_ws/install/lib/yolo_ros/yolo_node" in s
    assert "/tmp/ui9_yolo_runtime.log" in s
    assert "D08_REAL_GAZEBO_WAFFLE_RGBD_NO_GOAL_PASS" in s
    assert "UI9_REAL_YOLO_ROS_PERSON_DETECTION_L1_PASS" in s
    p=PROBE.read_text()
    assert "BLOCKED_UI9_REAL_YOLO_ROS_PERSON_ZERO" in p
    assert "detection_array_count" in p
    assert "ros_or_gazebo_executed" not in p
