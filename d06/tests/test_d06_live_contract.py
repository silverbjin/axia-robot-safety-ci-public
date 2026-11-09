"""Static gate: D06 L1 runner cannot accidentally become a robot controller."""
import ast
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"d06_cm_live_gate.py"

def test_readable_and_isolated_command_paths():
    s=SCRIPT.read_text()
    ast.parse(s)
    assert '"/axia/d06/test/cmd_in"' in s
    assert '"/axia/d06/test/cmd_out"' in s
    assert '"/axia/d06/test/scan"' in s
    assert '"ros2","run","nav2_collision_monitor","collision_monitor"' in s
    assert 'node.create_publisher(Twist,"/axia/d06/test/cmd_in",10)' in s
    assert 'node.count_publishers("/cmd_vel")' in s
    assert 'create_publisher(Twist,"/cmd_vel"' not in s
    assert 'NavigateToPose' not in s
    assert 'certified_estop":False' in s

def test_requires_real_official_CM_outputs_and_state():
    s=SCRIPT.read_text()
    assert 'node.create_subscription(Twist,"/axia/d06/test/cmd_out"' in s
    assert 'node.create_subscription(CollisionMonitorState' in s
    assert '"CLEAR":0,"SLOWDOWN":2,"STOP":1' in s
    assert '0.20*0.30+0.010' in s
    assert '"PASS_OFFICIAL_JAZZY_CM_CLEAR_SLOWDOWN_STOP"' in s
    assert 'result["ros_actual"]=True' in s

def test_fail_closed_but_not_falsely_gazebo_verified():
    s=SCRIPT.read_text()
    assert '"gazebo_actual":False' in s
    assert 'result["status"]="BLOCKED"' not in s or '"status":"BLOCKED"' in s
    assert 'rclpy.spin_once' in s
    assert 'if result["status"]=="PASS_OFFICIAL_JAZZY_CM_CLEAR_SLOWDOWN_STOP" else 2' in s
