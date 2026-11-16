#!/usr/bin/env python3
"""Read-only AXIA D07 Owner archive scene/transport diagnosis (no ROS/Gazebo).

Not a scene pixel oracle. Compares the generated session Xacro and runtime
Gazebo SceneBroadcaster topics. Does not extract tar files or publish a Goal.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

SCENE = "gz::sim::systems::SceneBroadcaster"
EXPECTED = {"/world/default/scene/info", "/world/default/pose/info"}
MAX_MEMBER = 1_000_000


def diagnose(archive: Path) -> dict:
    result = {
        "status": "D07_H01_SCENE_DIAG_HOLD",
        "scene_source_unconditional": False,
        "scene_runtime_topics_observed": False,
        "gazebo_3d_scene_render_proven": False,
        "owner_wsl2_gui_l3_accepted": False,
        "goal_sent": False,
        "certified_estop": False,
        "sha256_sidecar_verified": False,
        "render_xwd_count": 0,
        "reason": "UNVERIFIED",
    }
    sidecar = Path(str(archive) + ".sha256")
    if not archive.is_file():
        result["reason"] = "ARCHIVE_MISSING"
        return result
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if sidecar.is_file():
        first = sidecar.read_text().strip().split()
        result["sha256_sidecar_verified"] = bool(
            first and first[0].lower() == digest.hexdigest())
    if not result["sha256_sidecar_verified"]:
        result["reason"] = "SHA256_SIDECAR_MISSING_OR_MISMATCH"
        return result

    with tarfile.open(archive, "r:gz") as tar:
        members = [m for m in tar.getmembers() if m.isfile()]
        result["render_xwd_count"] = sum(
            1 for m in members if m.name.endswith(".xwd") and
            "/gui_diagnostics/" in m.name and m.size >= 512)

        def read(suffix: str) -> str:
            matching = [m for m in members if m.name.endswith("/" + suffix)]
            if len(matching) != 1 or matching[0].size > MAX_MEMBER:
                return ""
            source = tar.extractfile(matching[0])
            return source.read().decode("utf-8", "replace") if source else ""

        world = read("real-l2/d07_gui_scene_world.sdf.xacro")
        manifest = read("real-l2/d07_gui_scene_world_manifest.json")
        topics = set(read("real-l2/d07_gui_transport_topics.txt").splitlines())
        watcher = read("real-l2/d07_gui_watcher.log")
        try:
            root = ET.fromstring(world)
            plugins = root.findall("./world/plugin")
            good_plugins = [
                p for p in plugins if p.get("name") == SCENE and
                p.get("filename") == "gz-sim-scene-broadcaster-system"]
            details = json.loads(manifest)
            result["scene_source_unconditional"] = (
                len(good_plugins) == 1
                and details.get("scene_broadcaster_count") == 1
                and details.get("scope") == "D07_H01_GUI_READONLY_SIM_ONLY"
                and details.get("overlay_sha256") ==
                    hashlib.sha256(world.encode()).hexdigest()
            )
        except (ET.ParseError, ValueError, TypeError):
            pass
        result["scene_runtime_topics_observed"] = EXPECTED <= topics
        result["watcher_children_spawned"] = (
            "D07_H01_GUI_CHILDREN_SPAWNED" in watcher)
        if not result["scene_source_unconditional"]:
            result["reason"] = "FINAL_D07_SCENE_WORLD_NOT_PROVEN"
        elif not result["scene_runtime_topics_observed"]:
            result["reason"] = "SCENE_BROADCASTER_RUNTIME_TOPICS_MISSING"
        elif not result["watcher_children_spawned"]:
            result["reason"] = "GAZEBO_GUI_CHILDREN_NOT_PROVEN"
        elif result["render_xwd_count"] < 2:
            result["reason"] = "GUI_XWD_CAPTURE_ABSENT"
        else:
            result["status"] = "D07_H01_SCENE_SOURCE_AND_TRANSPORT_VERIFIED"
            result["reason"] = "OWNER_GUI_PIXELS_REQUIRE_HUMAN_REVIEW"
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        report = diagnose(args.archive)
    except (OSError, tarfile.TarError, UnicodeError, ValueError) as exc:
        report = {
            "status": "D07_H01_SCENE_DIAG_HOLD",
            "reason": "ARCHIVE_PARSE_FAILED_" + type(exc).__name__,
            "goal_sent": False,
            "gazebo_3d_scene_render_proven": False,
            "owner_wsl2_gui_l3_accepted": False,
        }
    print("AXIA_D07_H01_SCENE_READONLY_DIAG=" +
          json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "D07_H01_SCENE_SOURCE_AND_TRANSPORT_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
