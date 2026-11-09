"""D05 real acceptance runner static gates, not an actual Gazebo result."""
from pathlib import Path
import ast
import sys

SCRIPTS=Path(__file__).resolve().parents[1]/"scripts"

def test_l2_gate_is_parseable_and_requires_real_sensor_callbacks():
    p=SCRIPTS/"d05_real_rgbd_l2_gate.py"
    s=p.read_text()
    ast.parse(s)
    assert "rclpy.spin_once" in s
    assert 'node.create_subscription(DetectionArray' in s
    assert 'node.create_subscription(Image' in s
    assert "depth_bridge.wait(" in s
    assert "rgb_continued_after_loss" in s
    assert "yolo_continued_after_loss" in s
    assert 'result["status"]="PASS_REAL_GAZEBO_PERSON_RANGE_VALID_TO_UNKNOWN"' in s
    assert "if actual.get(\"passed\") is True" in s
    assert "create_publisher(" not in s
    assert "NavigateToPose" not in s
    assert "/cmd_vel" not in s

def test_both_derived_scripts_have_valid_syntax():
    for p in SCRIPTS.glob("d05_*.py"):
        ast.parse(p.read_text())
