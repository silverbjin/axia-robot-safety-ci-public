"""D08 Task02 RED: old sensor-only D08 did not launch official Nav2.

These L0 tests do not prove an actual Nav2 Action, Costmap or ROS /scan.
"""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"harness"))
from d08_one_world_official_nav2_launch import make_official_nav2_command


def fixture(tmp_path, world_name="default", physical=True, camera=True, scan=True):
    w=tmp_path/"world.sdf"
    r=tmp_path/"waffle.sdf"
    world = '<sdf version="1.9"><world name="'+world_name+'">'
    if physical:
        world += '''<model name="axia_p2_g07_obstacle"><link name="obstacle_link">
        <collision name="obstacle_collision"/></link></model>'''
    world += '</world></sdf>'
    w.write_text(world)
    robot='<sdf version="1.9"><model name="waffle"><link name="camera_link">'
    if camera:
        robot += '''<sensor name="axia_d08_registered_rgbd" type="rgbd_camera">
        <gz_frame_id>axia_d08_rgbd_optical</gz_frame_id></sensor>'''
    if scan:
        robot += '<sensor name="hls_lfcd_lds" type="gpu_lidar"/>'
    robot += '</link></model></sdf>'
    r.write_text(robot)
    return w,r


def test_one_official_nav2_launch_owns_one_world_and_exact_d08_sensor(tmp_path):
    cmd=make_official_nav2_command(*fixture(tmp_path))
    assert cmd[:4]==["ros2","launch","nav2_bringup","tb3_simulation_launch.py"]
    assert sum(t.startswith("world:=") for t in cmd)==1
    assert sum(t.startswith("robot_sdf:=") for t in cmd)==1
    assert "use_composition:=False" in cmd
    assert "headless:=True" in cmd
    assert "autostart:=True" in cmd
    assert not any(t in cmd for t in ("gz","sim","NavigateToPose","FollowPath","cmd_vel"))

def test_reject_missing_physical_proxy_or_wrong_world(tmp_path):
    with pytest.raises(ValueError,match="WORLD_NOT_UNIQUE"):
        make_official_nav2_command(*fixture(tmp_path,world_name="other"))
    with pytest.raises(ValueError,match="PHYSICAL_PROXY_MISSING"):
        make_official_nav2_command(*fixture(tmp_path,physical=False))

def test_reject_unregistered_rgbd_or_missing_real_scan(tmp_path):
    with pytest.raises(ValueError,match="REGISTERED_RGBD_NOT_UNIQUE"):
        make_official_nav2_command(*fixture(tmp_path,camera=False))
    with pytest.raises(ValueError,match="REAL_GPU_LIDAR_MISSING"):
        make_official_nav2_command(*fixture(tmp_path,scan=False))
