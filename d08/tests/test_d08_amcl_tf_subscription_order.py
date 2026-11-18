"""Task02 first P0 failure #44226367924: no initial map TF despite AMCL Pose.

The ROS listener must be subscribed before official SetInitialPose service call.
Static L0 only; actual AMCL/TF confirmation requires new same SHA Gazebo L2.
"""
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[1]/
        "harness/d08_amcl_initial_pose.py")

def test_tf_listener_is_ready_before_initial_pose_service_can_broadcast():
    s=SOURCE.read_text()
    listener=s.index("listener=TransformListener(tfbuf,node,spin_thread=False)")
    service=s.index("pending=cli.call_async(req)")
    assert listener < service, "D08_P0_TF_LISTENER_SUBSCRIBE_AFTER_INITIAL_POSE_RED"

def test_amcl_scan_odom_and_safety_ttls_unmodified():
    s=SOURCE.read_text()
    assert "now-latest[\"scan\"][1]>.5" in s
    assert "now-latest[\"odom\"][1]>.5" in s
    assert 'time.monotonic()-latest["amcl_pose"][1]>1.0' in s
    assert "lookup_transform" in s
    assert "TransformBroadcaster" not in s
