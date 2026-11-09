"""D07 strict public source contract for official Nav2 planning, not robot motion."""
from pathlib import Path
import ast
import yaml

BASE=Path(__file__).resolve().parents[1]
YAML=BASE/"params"/"nav2_d07_planner.yaml"
SCRIPT=BASE/"scripts"/"d07_nav2_planner_l1.py"

def test_official_costmap_rolling_and_obstacle_layer():
    p=yaml.safe_load(YAML.read_text())
    assert set(p)=={"planner_server","global_costmap"}
    planner=p["planner_server"]["ros__parameters"]
    assert planner["GridBased"]["plugin"]=="nav2_navfn_planner::NavfnPlanner"
    c=p["global_costmap"]["global_costmap"]["ros__parameters"]
    assert c["rolling_window"] is True and c["track_unknown_space"] is False
    assert c["obstacle_layer"]["plugin"]=="nav2_costmap_2d::ObstacleLayer"
    assert c["inflation_layer"]["plugin"]=="nav2_costmap_2d::InflationLayer"
    assert c["obstacle_layer"]["scan"]["topic"]=="/axia/d07/test/scan"
    assert c["obstacle_layer"]["scan"]["marking"] is True
    assert c["obstacle_layer"]["scan"]["clearing"] is True

def test_l1_no_motion_publisher_and_nav2_plan_only():
    s=SCRIPT.read_text()
    ast.parse(s)
    assert 'ComputePathToPose' in s
    assert '"ros2","run","nav2_planner","planner_server"' in s
    assert '"/axia/d07/test/scan"' in s
    assert '"/cmd_vel"' in s # graph must prove zero publishers
    assert 'node.count_publishers("/cmd_vel")==0' in s
    assert "NavigateToPose" not in s
    assert "FollowPath" not in s
    assert "create_publisher(Twist" not in s
    assert '"gazebo_actual":False' in s
    assert '"certified_estop":False' in s

def test_l1_requires_real_ros_costmap_and_plans():
    s=SCRIPT.read_text()
    assert 'OccupancyGrid' in s
    assert 'node.create_subscription(OccupancyGrid' in s
    assert 'ActionClient' in s
    assert '"PASS_OFFICIAL_NAV2_COSTMAP_REPLAN_L1"' in s
    assert 'actual_obstacle_lethal_cells' in s
