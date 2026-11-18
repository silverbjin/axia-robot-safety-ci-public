#!/usr/bin/env python3
"""Official Nav2 Jazzy's OWN one-world Waffle launch args; never a second Gazebo.

This module does not implement Planner/Controller, issue a navigation Goal,
publish velocity, change CM/Guard timeouts or infer L2 from L0 evidence.
"""
from pathlib import Path
import xml.etree.ElementTree as ET


def make_official_nav2_command(world_sdf: Path, robot_sdf: Path, *, owner_gui=False) -> list[str]:
    world_sdf, robot_sdf = Path(world_sdf), Path(robot_sdf)
    for path in (world_sdf, robot_sdf):
        if not path.is_absolute() or not path.is_file() or path.is_symlink():
            raise ValueError("D08_OFFICIAL_NAV2_SDF_SOURCE_NOT_PINNED")
    try:
        w = ET.parse(world_sdf).getroot()
        r = ET.parse(robot_sdf).getroot()
    except ET.ParseError as ex:
        raise ValueError("D08_OFFICIAL_NAV2_SDF_PARSE_BLOCKED") from ex
    worlds = w.findall("./world")
    if len(worlds) != 1 or worlds[0].get("name") != "default":
        raise ValueError("D08_OFFICIAL_NAV2_WORLD_NOT_UNIQUE")
    model = worlds[0].find("./model[@name='axia_p2_g07_obstacle']")
    if (model is None or
        model.find("./link[@name='obstacle_link']/collision[@name='obstacle_collision']") is None):
        raise ValueError("D08_OFFICIAL_NAV2_PHYSICAL_PROXY_MISSING")
    cams = r.findall(".//sensor[@name='axia_d08_registered_rgbd']")
    scans = r.findall(".//sensor[@name='hls_lfcd_lds']")
    if (len(cams) != 1 or cams[0].get("type") != "rgbd_camera" or
        cams[0].findtext("./gz_frame_id") != "axia_d08_rgbd_optical"):
        raise ValueError("D08_OFFICIAL_NAV2_REGISTERED_RGBD_NOT_UNIQUE")
    if len(scans) != 1 or scans[0].get("type") != "gpu_lidar":
        raise ValueError("D08_OFFICIAL_NAV2_REAL_GPU_LIDAR_MISSING")
    return [
        "ros2", "launch", "nav2_bringup", "tb3_simulation_launch.py",
        "headless:=False" if owner_gui else "headless:=True",
        "use_rviz:=True" if owner_gui else "use_rviz:=False",
        "use_composition:=False", "use_respawn:=False",
        "autostart:=True", "use_sim_time:=True",
        "world:=" + str(world_sdf), "robot_sdf:=" + str(robot_sdf),
        "robot_name:=axia_d08_ci_waffle",
        "x_pose:=-2.0", "y_pose:=-0.5", "z_pose:=0.02",
    ]
