"""RED first: ROS and Goal owner unchanged; throttle educational GUI CPU contention.

Actual 2026-11-15 concurrent Gazebo L2 found CM RMW receive 393.580ms
while same CM publication source gap was 69.596ms. This contracts display
CPU affinity and frame budget; it does not claim proven DDS root cause.
"""
from pathlib import Path
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
SELECTOR=ROOT/"d06/live/d06_gui_cpu_plan.py"
SIDECAR=ROOT/"d06/scripts/d06_rviz_sidecar.sh"
RVIZ=ROOT/"d06/rviz/d06_safety_bubble.rviz"

def test_gui_cpu_plan_selects_first_affinity_cpu_and_never_bag_last_cpu():
    assert SELECTOR.is_file()
    run=subprocess.run([sys.executable,str(SELECTOR),"--cpus","2,5,9"],
                       text=True,capture_output=True,check=False)
    assert run.returncode==0,run.stderr
    assert run.stdout.strip()=="2" # Owner G07 rosbag stays max CPU 9

def test_gui_cpu_plan_fails_closed_if_single_cpu_no_separation_available():
    run=subprocess.run([sys.executable,str(SELECTOR),"--cpus","5"],
                       text=True,capture_output=True,check=False)
    assert run.returncode!=0
    assert "INSUFFICIENT" in run.stderr

def test_owner_sidecar_display_only_on_separate_cpu_with_lower_priority():
    s=SIDECAR.read_text()
    assert "d06_gui_cpu_plan.py" in s
    assert "taskset -c" in s
    assert 'nice -n 19 rviz2' in s
    assert 'nice -n 7 /usr/bin/python3' in s
    assert "D06_GUI_AFFINITY" in s
    assert "YES-P2-G07-GOAL" not in s
    assert "AXIA_G07_CI_SIM_GOAL_ALLOWED" not in s

def test_rviz_frame_rate_bounded_but_scan_odom_tf_and_bubble_still_visible():
    s=RVIZ.read_text()
    assert "Frame Rate: 3" in s
    for name in ("/scan","/odom","/robot_description","/axia/d06/rviz/bubble"):
        assert name in s
    assert "NOT_OFFICIAL_CM" in s
