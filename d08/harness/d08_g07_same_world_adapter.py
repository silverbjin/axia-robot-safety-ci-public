#!/usr/bin/env python3
"""Public D08/G07 single-world SOURCE adapter, never a moving-Goal executor.

Apply the proven D08 person visual + registered RGBD to the exact G07 10Hz
Waffle and Contact world. Existing G07 Nav2/Supervisor/CM/Guard owns runtime.
The returned XML contract is STATIC until one real same-session Gazebo L2.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from d08_live_world import build_overlay


def build_g07_d08_camera_world(world: Path, robot: Path, actor_mesh: Path,
                               output: Path, *, student_sha: str) -> dict:
    if not isinstance(student_sha, str) or re.fullmatch(r"[a-f0-9]{40}", student_sha) is None:
        raise ValueError("D08_G07_STUDENT_SHA_INVALID")
    world, robot, actor_mesh, output = (Path(p) for p in
                                       (world, robot, actor_mesh, output))
    for source in (world, robot, actor_mesh):
        if source.is_symlink() or not source.is_file():
            raise ValueError("D08_G07_PINNED_SOURCE_MISSING")
    if output.exists() or output.is_symlink():
        raise ValueError("D08_G07_OUTPUT_ALREADY_EXISTS")
    w = ET.parse(world).getroot()
    r = ET.parse(robot).getroot()
    if len(w.findall("./world")) != 1 or w.find("./world").get("name") != "default":
        raise ValueError("D08_G07_ONE_DEFAULT_WORLD_REQUIRED")
    if len(w.findall(".//model[@name='axia_p2_g07_obstacle']")) != 1:
        raise ValueError("D08_G07_ONE_PHYSICAL_PERSON_REQUIRED")
    if len(w.findall(".//plugin[@name='gz::sim::systems::Contact']")) != 1:
        raise ValueError("D08_G07_CONTACT_SYSTEM_REQUIRED")
    lidar = r.findall(".//sensor[@name='hls_lfcd_lds']")
    if (len(lidar) != 1 or lidar[0].get("type") != "gpu_lidar"
            or lidar[0].findtext("./update_rate") != "10"):
        raise ValueError("D08_G07_10HZ_LIDAR_REQUIRED")
    hashes_before = [hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (world, robot, actor_mesh)]

    # Reuse D08's exact previously proven XML implementation, not a new
    # camera, separate visual Actor, movement controller or synthetic Scan.
    manifest = build_overlay(world, robot, actor_mesh, output,
                             g07_lidar_preconfigured=True)
    new_world = ET.parse(manifest["world"]).getroot()
    new_robot = ET.parse(manifest["robot_sdf"]).getroot()
    if (len(new_world.findall("./world")) != 1
            or len(new_world.findall(".//model[@name='axia_p2_g07_obstacle']")) != 1
            or len(new_world.findall(".//collision[@name='obstacle_collision']")) != 1
            or len(new_world.findall(".//plugin[@name='gz::sim::systems::Contact']")) != 1
            or len(new_robot.findall(".//sensor[@name='axia_d08_registered_rgbd']")) != 1
            or len(new_robot.findall(".//sensor[@name='hls_lfcd_lds']")) != 1
            or new_robot.findtext(".//sensor[@name='hls_lfcd_lds']/update_rate") != "10"):
        raise ValueError("D08_G07_SOURCE_OVERLAY_INVARIANT_BROKEN")
    hashes_after = [hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (world, robot, actor_mesh)]
    if hashes_before != hashes_after:
        raise ValueError("D08_G07_ORIGINAL_SOURCE_MUTATED")

    manifest.update({
        "schema": "axia_d08_g07_10hz_same_world_static_adapter_v1",
        "g07_student_source_sha": student_sha,
        "upstream_g07_lidar_10hz_preserved": True,
        "g07_contact_witness_plugin_preserved": (
            len(new_world.findall(".//plugin[@name='axia::G07S02Witness']"))
            == len(w.findall(".//plugin[@name='axia::G07S02Witness']"))),
        "no_second_gazebo_launched": True,
        "safety_timeout_parameters_modified": False,
        "yolo_direct_cm_control_claimed": False,
        "single_world_runtime_claimed": False,
        "moving_goal_verified": False,
        "d06_cm_guard_ttl_verified": False,
        "yolo_person_valid_verified": False,
    })
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return manifest
