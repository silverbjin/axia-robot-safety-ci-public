"""RED: physical G07 LiDAR and set_pose must be ready BEFORE GUI load.
Actual L2 #43673304437 first failed PREG0AL_PHYSICAL_L2 before any Goal.
No synthesized scan/startup allowed; only native Gazebo readiness receipt.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/live/d06_ci_physical_pregoal_barrier.py"

def test_physical_ready_contract_must_precede_concurrent_rviz_goal():
    assert SCRIPT.is_file(), "G07_PHYSICAL_PREG0AL_BARRIER_MISSING"
    from d06.live.d06_ci_physical_pregoal_barrier import ready
    assert ready({"status":"P2_G07_OWNER_PREGOAL_L2_READY_NO_GOAL",
                  "native_set_pose_ack":True,
                  "post_ack_distinct_ros_scan_count":2,
                  "front_m":2.01,"side_m":0.71}) is True
    assert ready({"status":"P2_G07_OWNER_PREGOAL_L2_READY_NO_GOAL",
                  "native_set_pose_ack":True,
                  "post_ack_distinct_ros_scan_count":1,
                  "front_m":2.01,"side_m":0.71}) is False
    assert ready({"status":"BLOCKED",
                  "native_set_pose_ack":True,
                  "post_ack_distinct_ros_scan_count":2,
                  "front_m":2.01,"side_m":0.71}) is False
    assert ready(None) is False
