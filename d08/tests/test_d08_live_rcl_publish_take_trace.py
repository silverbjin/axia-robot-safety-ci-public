"""RED: the EXISTING D08 no-Goal L2 must trace bridge publisher and ROS take live.

Only evidence. Keep native Gazebo, the independent ROS process and the original
Observer; do not relax the 500ms receive gap or fabricate a successful scan.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "d08/scripts/d08_ros_trace_live_ci.sh"
WORKFLOW = ROOT / ".github/workflows/d08-main-no-goal-real-gazebo-l2.yml"

def test_actual_l2_trace_start_before_ros_process_and_stop_after_failure():
    workflow = WORKFLOW.read_text()
    assert SCRIPT.is_file(), "D08_LIVE_RCL_TRACE_RED_NO_REAL_SESSION_WRAPPER"
    assert "d08/scripts/d08_ros_trace_live_ci.sh start" in workflow
    assert "d08/scripts/d08_ros_trace_live_ci.sh stop" in workflow
    assert "if: always() && github.head_ref == 'diag/d08-live-rcl-publish-take-20261119'" in workflow
    assert workflow.index("d08/scripts/d08_ros_trace_live_ci.sh start") < workflow.index(
        "python3 -u d08/scripts/d08_public_gazebo_l2.py")
    assert workflow.index("d08/scripts/d08_ros_trace_live_ci.sh stop") > workflow.index(
        "python3 -u d08/scripts/d08_public_gazebo_l2.py")

def test_trace_is_userspace_bounded_evidence_not_safety_pass():
    src = SCRIPT.read_text()
    assert "ros2 trace start" in src and "ros2 trace stop" in src
    assert "rcl_publish" in src and "rcl_take" in src
    assert "D08_BRIDGE_RCL_TRACE" in src
    assert "UNDETERMINED" in src
    assert "500ms" not in src or "UNCHANGED" in src
    assert "rm -rf" not in src
