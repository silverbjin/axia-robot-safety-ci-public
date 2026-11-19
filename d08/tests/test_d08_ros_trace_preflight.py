"""RED: ROS 2 Jazzy official userspace tracing must be preflighted in CI.

Only instrument the existing no-goal Gazebo job. No local Owner changes,
no ROS/Nav2 patches, no /cmd_vel and no safety-threshold adjustments.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d08/scripts/d08_ros_trace_preflight.sh"
WORKFLOW=ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml"

def test_readonly_ros2_trace_preflight_script_exists():
    assert SCRIPT.is_file()
    source=SCRIPT.read_text()
    assert "ros2 run tracetools status" in source
    assert "ros2 trace start" in source
    assert "ros2 trace stop" in source
    assert "--snapshot-mode" in source
    assert "D08_ROS_TRACE_PREFLIGHT_L2_PASS" in source
    assert "cmd_vel" not in source
    assert "set_pose" not in source

def test_public_gazebo_job_installs_only_jazzy_tracing_bindings_when_enabled():
    source=WORKFLOW.read_text()
    assert "AXIA_D08_ROS_TRACE_PREFLIGHT" in source
    assert "ros-jazzy-ros2trace" in source
    assert "d08/scripts/d08_ros_trace_preflight.sh" in source
    assert "D08_ROS_TRACE_PREFLIGHT" in source
