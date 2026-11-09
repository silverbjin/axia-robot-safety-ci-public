#!/usr/bin/env python3
"""Non-invasive AXIA P1 D04 overlay: official Nav2 Waffle + official ROBOTIS Pi RGB.

Outputs temporary SDF xacro and world xacro. Never modifies source files.
No ROS commands, motor publishers, or P1 code is included.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

XACRO_NS = "http://www.ros.org/wiki/xacro"
ET.register_namespace("xacro", XACRO_NS)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_overlay(waffle: Path, pi: Path, world: Path, dae: Path, out: Path,
                 *, cpu_renderer: bool = False) -> dict:
    """The only robot-model change is a single camera sensor under camera_link."""
    for item in (waffle, pi, world, dae):
        if not item.is_file():
            raise FileNotFoundError(item)
    out.mkdir(parents=True, exist_ok=True)
    b = ET.parse(waffle)
    p = ET.parse(pi)
    w = ET.parse(world)
    bl = b.find(".//model/link[@name='camera_link']")
    pl = p.find(".//sensor[@name='camera'][@type='camera']")
    if bl is None or pl is None:
        raise ValueError("Missing official Waffle camera_link or Waffle Pi RGB camera")
    if b.find(".//sensor[@name='axia_d04_rgb']") is not None:
        raise ValueError("Duplicate camera overlay")
    if pl.findtext("topic") != "camera/image_raw":
        raise ValueError("Unsupported upstream RGB topic")
    img = pl.find("camera/image")
    if (img is None or img.findtext("width") != "640" or
            img.findtext("height") != "480" or
            img.findtext("format") != "R8G8B8"):
        raise ValueError("Unexpected official Waffle Pi RGB image contract")
    before = len(b.findall(".//sensor"))
    sensor = deepcopy(pl)
    sensor.set("name", "axia_d04_rgb")
    # The existing Nav2 Waffle camera_link already contains the depth sensor.
    # Set sensor local pose; do not change any link/joint/drive dynamics.
    pose = sensor.find("pose")
    if pose is None:
        pose = ET.SubElement(sensor, "pose")
    pose.text = "0 0 0 0 0 0"
    bl.append(sensor)
    if len(b.findall(".//sensor")) != before + 1:
        raise ValueError("Overlay changed unexpected sensor count")

    world_node = w.find(".//world")
    if world_node is None:
        raise ValueError("Missing world")
    if world_node.find("actor[@name='axia_d04_person']") is not None:
        raise ValueError("Duplicate actor")
    actor = ET.fromstring(f"""<actor name="axia_d04_person">
      <skin><filename>{dae.resolve()}</filename><scale>1.0</scale></skin>
      <animation name="walk"><filename>{dae.resolve()}</filename>
      <interpolate_x>true</interpolate_x></animation>
      <script><loop>true</loop><auto_start>true</auto_start>
        <trajectory id="0" type="walk" tension="1.0">
          <!-- A 6-s *simulation-time* loop. Camera-facing visual human only.
               No actor collision, robot goal or cmd_vel side effects. -->
          <waypoint><time>0</time><pose>0.8 -0.5 1.0 0 0 3.14159</pose></waypoint>
          <waypoint><time>2</time><pose>0.8 -0.72 1.0 0 0 3.14159</pose></waypoint>
          <waypoint><time>4</time><pose>0.8 -0.28 1.0 0 0 3.14159</pose></waypoint>
          <waypoint><time>6</time><pose>0.8 -0.5 1.0 0 0 3.14159</pose></waypoint>
        </trajectory>
      </script>
    </actor>""")
    world_node.append(actor)
    world_before = w.find(".//plugin[@filename='gz-sim-sensors-system']/render_engine")
    if world_before is None:
        raise ValueError("Official Nav2 Gazebo Sensors plugin missing")
    original_renderer = world_before.text
    if cpu_renderer:
        world_before.text = "ogre"
    robot_path = out / "axia_d04_waffle_rgb.sdf.xacro"
    world_path = out / "axia_d04_human_world.sdf.xacro"
    b.write(robot_path, encoding="unicode", xml_declaration=True)
    w.write(world_path, encoding="unicode", xml_declaration=True)
    return {
        "robot_sdf": str(robot_path.resolve()),
        "world": str(world_path.resolve()),
        "official_waffle_sha256": sha256(waffle),
        "official_pi_sha256": sha256(pi),
        "official_world_sha256": sha256(world),
        "actor_dae_sha256": sha256(dae),
        "overlay_robot_sha256": sha256(robot_path),
        "overlay_world_sha256": sha256(world_path),
        "renderer": world_before.text,
        "original_renderer": original_renderer,
        "robot_sensor_count_before": before,
        "robot_sensor_count_after": len(b.findall(".//sensor")),
        "actor_count": len(world_node.findall("actor")),
        "p1_model_control_modified": False,
        "actor_physics_collision": False,
        "goal_sent": False,
    }


def main():
    a = argparse.ArgumentParser()
    for param in ("waffle", "pi", "world", "dae", "out"):
        a.add_argument("--" + param.replace("_", "-"), required=True, type=Path)
    a.add_argument("--cpu-renderer", action="store_true")
    v = vars(a.parse_args())
    result = make_overlay(v["waffle"], v["pi"], v["world"], v["dae"],
                          v["out"], cpu_renderer=v["cpu_renderer"])
    f = v["out"] / "overlay_manifest.json"
    f.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
