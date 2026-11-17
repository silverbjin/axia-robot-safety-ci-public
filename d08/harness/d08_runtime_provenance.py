#!/usr/bin/env python3
"""D08 Task00 one-run, one-world source identity; metadata, NOT a Gazebo PASS."""
from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Mapping

_PROXY = "axia_p2_g07_obstacle"
_VISUAL = ("axia_d08_human_mesh", "axia_d08_human_torso")


def make_runtime_provenance(world_sdf: Path, env: Mapping[str, str],
                            source_sha: str) -> dict:
    """Reject mixed scene or unpinned source before Gazebo startup.

    This is a static provenance gate for the *same run's* generated SDF.
    ROS topic source, DDS/QoS/TF freshness and visible GUI require separate
    real-runtime evidence and MUST NOT be inferred from this dictionary.
    """
    if re.fullmatch(r"[0-9a-f]{40}", source_sha or "") is None:
        raise ValueError("D08_SOURCE_SHA_UNPINNED")
    domain = str(env.get("ROS_DOMAIN_ID", ""))
    partition = str(env.get("GZ_PARTITION", ""))
    if (not domain.isascii() or not domain.isdecimal() or
            not 0 <= int(domain) <= 232 or
            not partition or partition.isspace() or
            any(ch.isspace() for ch in partition)):
        raise ValueError("D08_DOMAIN_PARTITION_INVALID")
    data = Path(world_sdf).read_bytes()
    root = ET.fromstring(data)
    worlds = root.findall("./world")
    if (root.tag != "sdf" or len(worlds) != 1 or
            worlds[0].get("name") != "default"):
        raise ValueError("D08_WORLD_NOT_UNIQUE_DEFAULT")
    world = worlds[0]
    proxies = world.findall(f"./model[@name='{_PROXY}']")
    if len(proxies) != 1 or world.findall("./actor"):
        raise ValueError("D08_PHYSICAL_PERSON_NOT_UNIQUE")
    link = proxies[0].find("./link[@name='obstacle_link']")
    if link is None or (
        len(link.findall("./collision[@name='obstacle_collision']")) != 1
    ) or (
        not any(link.find(f"./visual[@name='{name}']") is not None
                for name in _VISUAL)
    ) or (
        len(link.findall("./sensor[@name='axia_contact']")) != 1
    ):
        raise ValueError("D08_PHYSICAL_PERSON_COLLISION_VISUAL_CONTACT_MISSING")
    return {
        "source_sha": source_sha,
        "world": "default",
        "world_sdf_sha256": hashlib.sha256(data).hexdigest(),
        "human_proxy": _PROXY,
        "robot_spawn_request": "axia_d08_ci_waffle",
        "ros_domain_id": int(domain),
        "gz_partition": partition,
        "no_moving_goal": True,  # intended execution mode, NOT ROS audit
        "runtime_ros_graph_verified": False,
        "runtime_cm_scan_verified": False,
        "runtime_nav2_path_verified": False,
        "owner_wslg_pixels_verified": False,
    }
