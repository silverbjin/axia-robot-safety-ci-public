#!/usr/bin/env python3
"""Reuse official Nav2 Jazzy Waffle spawn/bringup against one D08-owned Gazebo server.

This module does not implement Planner/Controller, issue a navigation Goal,
publish velocity, change CM/Guard timeouts or infer L2 from L0 evidence.
"""
from pathlib import Path
import xml.etree.ElementTree as ET


def create_official_rviz_path_overlay(base: Path, out: Path) -> Path:
    """Only retarget official Nav2 RViz Path display to original Action result.

    Keep RobotModel/TF/Scan/global/local Costmaps and every official display
    setting unchanged. A new local file is created; ROS/Nav2 installation
    and public CI headless config are never modified.
    """
    base,out=Path(base),Path(out)
    if not base.is_file() or base.is_symlink() or out.exists() or out.is_symlink():
        raise ValueError("D08_RVIZ_OFFICIAL_SOURCE_OR_DESTINATION_INVALID")
    raw=base.read_text()
    if (raw.count("Value: /plan") != 1 or
        raw.count("Class: rviz_default_plugins/Path") < 1):
        raise ValueError("D08_RVIZ_OFFICIAL_PATH_TOPIC_NOT_UNIQUE")
    out.write_text(raw.replace("Value: /plan",
        "Value: /axia/d08/official_path_readonly",1))
    return out.resolve()


def make_official_nav2_command(world_sdf: Path, robot_sdf: Path, *, owner_gui=False, rviz_config_file: Path | None=None) -> list[str]:
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
    if owner_gui:
        if (rviz_config_file is None or
            not Path(rviz_config_file).is_file() or
            Path(rviz_config_file).is_symlink()):
            raise ValueError("D08_OWNER_RVIZ_READONLY_CONFIG_REQUIRED")
    return [
        "ros2", "launch", "nav2_bringup", "tb3_simulation_launch.py",
        # D08 owns the already-validated Gazebo server. Official Nav2 still
        # owns robot spawning, localization, costmaps and RViz; it MUST NOT
        # start an independent server on a racing /tmp/nav2_*.sdf.
        'use_simulator:=False',
        "headless:=False" if owner_gui else "headless:=True",
        "use_rviz:=True" if owner_gui else "use_rviz:=False",
        "use_composition:=False", "use_respawn:=False",
        "autostart:=True", "use_sim_time:=True",
        "world:=" + str(world_sdf), "robot_sdf:=" + str(robot_sdf),
        "robot_name:=axia_d08_ci_waffle",
        "x_pose:=-2.0", "y_pose:=-0.5", "z_pose:=0.02",
    ] + (["rviz_config_file:=" + str(Path(rviz_config_file).resolve())]
         if owner_gui else [])
