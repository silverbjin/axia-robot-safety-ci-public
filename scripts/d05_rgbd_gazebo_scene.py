#!/usr/bin/env python3
"""AXIA D05: single Gazebo RGBD sensor scene, read-only no robot command.

Reuse proven D04 official TurtleBot3 Waffle Pi world and Gazebo actor.
In sensor-only preflight, use a static box to prove real Depth pixels.
No code path can substitute a synthetic depth frame for L2.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

from d04_waffle_pi_rgb_preflight import simple_world
from d04_yolo_person_runtime import world_with_human

RGB_TOPIC = "/axia/d05/rgbd/image"
DEPTH_TOPIC = "/axia/d05/rgbd/depth_image"
FRAME = "axia_d05_rgbd_optical"
WIDTH, HEIGHT = 640, 480

RIG = """<model name="axia_d05_rgbd_rig">
  <static>true</static><pose>0.5 0 0.75 0 0 0</pose>
  <link name="rgbd_link">
    <sensor name="axia_d05_registered_rgbd" type="rgbd_camera">
      <always_on>1</always_on><update_rate>5</update_rate>
      <topic>axia/d05/rgbd</topic>
      <gz_frame_id>axia_d05_rgbd_optical</gz_frame_id>
      <camera>
        <horizontal_fov>1.047</horizontal_fov>
        <image><width>640</width><height>480</height><format>R8G8B8</format></image>
        <clip><near>0.15</near><far>8.0</far></clip>
      </camera>
    </sensor>
  </link>
</model>"""

BOX = """<model name="sensor_only_calibration_box">
  <static>true</static><pose>2.8 0 0.85 0 0 0</pose><link name="body">
  <visual name="box_visual"><geometry>
  <box><size>0.35 0.75 1.7</size></box>
  </geometry><material><ambient>0.5 0.4 0.3 1</ambient>
  <diffuse>0.5 0.4 0.3 1</diffuse></material></visual>
  </link></model>"""

def make_world(*, actor_mesh: Path | None = None) -> str:
    """Actor run has no artificial calibration obstacle in front of it."""
    source = (world_with_human(actor_mesh) if actor_mesh is not None
              else simple_world())
    if actor_mesh is not None and not Path(actor_mesh).is_file():
        raise FileNotFoundError(actor_mesh)
    if "</world></sdf>" not in source:
        raise ValueError("Unrecognized official D04 world")
    extra = RIG + (BOX if actor_mesh is None else "")
    world = source.replace("</world></sdf>",extra+"</world></sdf>")
    root = ET.fromstring(world)
    cameras = root.findall(".//sensor[@type='rgbd_camera']")
    if len(cameras) != 1:
        raise ValueError("One registered D05 RGBD sensor required")
    s = cameras[0]
    assert s.findtext("topic") == "axia/d05/rgbd"
    assert s.findtext("gz_frame_id") == FRAME
    assert s.findtext("camera/image/width") == str(WIDTH)
    assert s.findtext("camera/image/height") == str(HEIGHT)
    if actor_mesh is not None and root.find(".//model[@name='sensor_only_calibration_box']") is not None:
        raise ValueError("Cannot include surrogate depth target in person measurement")
    return world

def sha256(source: bytes) -> str:
    return hashlib.sha256(source).hexdigest()
