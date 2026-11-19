"""X11 actual viewable-window probe is diagnostic-only, no Gazebo/ROS.

Real Xvfb + two mapped dummy windows were verified locally. Public CI
must confirm the exact committed probe with official RViz/Gazebo windows.
"""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from d08_x11_window_titles import classify_titles

def test_actual_mapped_titles_classification():
    assert classify_titles(["RViz2","Gazebo Sim"])=={"rviz":True,"gazebo":True}
    assert classify_titles(["RViz2"])=={"rviz":True,"gazebo":False}
    assert classify_titles([])=={"rviz":False,"gazebo":False}

def test_missing_or_incorrect_names_fail_closed():
    assert classify_titles(["RQT","CLI","FakeGazeb0"])=={"rviz":False,"gazebo":False}
    with pytest.raises(ValueError,match="TITLES_INVALID"):
        classify_titles([123])

def test_only_readonly_xlib_no_control_nodes_or_goal():
    s=(Path(__file__).resolve().parents[1]/"scripts"/"d08_x11_window_titles.py").read_text()
    assert "lib.XQueryTree" in s
    assert "lib.XGetWindowAttributes" in s
    assert "attrs.map_state==2" in s
    assert "import rclpy" not in s and "ros2 launch" not in s
    assert "os.system(" not in s and "subprocess.run(" not in s
