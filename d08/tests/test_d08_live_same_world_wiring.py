"""D08 single actual World source contract; ROS/Gazebo is L2 only."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_pinned_engine_and_live_ranges_run_inside_one_gazebo_nav2_job():
    wf=(ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
    assert "D08_REAL_LIVE_RGBD_YOLO_D05_NAV2_THREE_PATHS_L2_PASS_NO_GOAL" in wf
    assert "--official-nav2 --official-path-phases --live-person-range" in wf
    assert "d08_live_yolo.yaml" in wf and "use_sim_time: true" in wf
    assert "D08_LIVE_SAME_WORLD_FIRST_BOUNDARY" in wf
    assert "d08-same-world-live-person-range-cm-nav2-evidence" in wf
    runner=(ROOT/"d08/scripts/d08_public_gazebo_l2.py").read_text()
    assert "D08_LIVE_RANGE_REQUIRES_SAME_WORLD_OFFICIAL_NAV2_3PATHS" in runner
    assert "d08_live_person_range_session import run_session" in runner
    assert "result['yolo_executed']=True" in runner
    assert "NavigateToPose.Goal(" not in runner
