"""D04 Jazzy ROS package contracts — NO synthetic YOLO inference accepted."""
from __future__ import annotations
import copy
import importlib.util
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import pytest

def package_root():
    parent=Path(__file__).resolve().parents[1]
    options=(parent, parent/"d04"/"axia_d04_vision_demo")
    for item in options:
        if (item/"package.xml").is_file():
            return item
    return options[-1]

ROOT=package_root()
sys.path.insert(0,str(ROOT))
from axia_d04_vision_demo.overlay import make_overlay
from axia_d04_vision_demo.config import build_yolo_config, validate_assets, PINNED_ONNX_SHA256


def sample_paths(tmp):
    waffle=tmp/"waffle.sdf.xacro"
    waffle.write_text("""<?xml version="1.0"?>
    <sdf xmlns:xacro="http://www.ros.org/wiki/xacro">
      <xacro:arg name="namespace" default=""/>
      <model name="turtlebot3_waffle">
        <link name="camera_link"><sensor name="depth" type="depth"/></link>
        <plugin name="DiffDrive"><topic>$(arg namespace)/cmd_vel</topic></plugin>
      </model>
    </sdf>""")
    pi=tmp/"pi.sdf"
    pi.write_text("""<sdf><model><link><sensor name="camera" type="camera">
       <topic>camera/image_raw</topic><gz_frame_id>camera_rgb_frame</gz_frame_id>
       <camera><camera_info_topic>camera/camera_info</camera_info_topic>
       <image><width>640</width><height>480</height><format>R8G8B8</format></image>
       </camera>
       </sensor></link></model></sdf>""")
    world=tmp/"world.sdf.xacro"
    world.write_text("""<sdf xmlns:xacro="http://www.ros.org/wiki/xacro"><world name="default">
      <plugin filename="gz-sim-sensors-system"><render_engine>ogre2</render_engine></plugin>
    </world></sdf>""")
    dae=tmp/"walk.dae";dae.write_text("<COLLADA/>")
    return waffle,pi,world,dae


def test_package_metadata_and_launch_present():
    assert (ROOT/"package.xml").is_file()
    assert (ROOT/"setup.py").is_file()
    assert (ROOT/"launch/d04_p1_yolo.launch.py").is_file()
    assert (ROOT/"resource/axia_d04_vision_demo").is_file()
    root=ET.parse(ROOT/"package.xml").getroot()
    assert root.findtext("name")=="axia_d04_vision_demo"
    assert root.findtext("export/build_type")=="ament_python"


def test_overlay_source_unchanged_and_single_camera(tmp_path):
    waffle,pi,world,dae=sample_paths(tmp_path)
    data_before=[p.read_bytes() for p in (waffle,pi,world,dae)]
    result=make_overlay(waffle,pi,world,dae,tmp_path/"generated",cpu_renderer=True)
    assert [p.read_bytes() for p in (waffle,pi,world,dae)]==data_before
    robot=ET.parse(result["robot_sdf"]).getroot()
    sensors=robot.findall(".//sensor")
    assert len(sensors)==2
    assert [s.get("name") for s in sensors].count("axia_d04_rgb")==1
    assert robot.find(".//plugin[@name='DiffDrive']/topic").text=="$(arg namespace)/cmd_vel"
    scene=ET.parse(result["world"]).getroot()
    assert scene.find(".//actor[@name='axia_d04_person']") is not None
    assert scene.find(".//actor/collision") is None
    assert scene.find(".//plugin[@filename='gz-sim-sensors-system']/render_engine").text=="ogre"
    assert result["p1_model_control_modified"] is False


def test_overlay_rejects_missing_camera_or_unexpected_dimensions(tmp_path):
    waffle,pi,world,dae=sample_paths(tmp_path)
    pi.write_text(pi.read_text().replace("<width>640</width>","<width>320</width>"))
    with pytest.raises(ValueError):
        make_overlay(waffle,pi,world,dae,tmp_path/"out")


def test_yolo_config_uses_upstream_onnx_pipeline_only(tmp_path):
    model=tmp_path/"model.onnx";model.write_bytes(b"dummy-for-config-not-inference")
    text=build_yolo_config(model)
    assert "/yolo/yolo_node:" in text
    assert 'plugins: ["detection", "debug"]' in text
    assert "rgb_topic: /camera/image_raw" in text
    assert "provider: cpu" in text
    assert "yolo_ros/DetectionPlugin" in text
    assert "yolo_ros/DebugPlugin" in text
    for banned in ("/cmd_vel", "TrackingPlugin", "Detect3DPlugin","model_repo: unileon-robotics"):
        assert banned not in text


def test_model_sha_fail_closed(tmp_path):
    model=tmp_path/"model.onnx";model.write_bytes(b"WRONG_MODEL")
    actor=tmp_path/"walk.dae";actor.write_bytes(b"<COLLADA/>")
    with pytest.raises(ValueError,match="SHA256"):
        validate_assets(model,actor)
    assert len(PINNED_ONNX_SHA256)==64


def test_launch_is_opt_in_no_control_publisher():
    source=(ROOT/"launch/d04_p1_yolo.launch.py").read_text()
    assert "IncludeLaunchDescription" in source
    assert "ros_gz_image" in source
    assert "yolo_bringup" in source
    assert "allow_fault_injection" in source
    assert "create_publisher(" not in source
    assert "send_goal_async(" not in source
    assert "collision_monitor" not in source


def test_no_private_teacher_code_or_weights_in_package():
    allowed_suffixes={".py",".xml",".md",".txt",".cfg",".yaml",".xacro",""}
    paths=[p for p in ROOT.rglob("*") if p.is_file()]
    assert not any(p.suffix in (".onnx",".pt",".pkl") for p in paths)
    assert not any("hidden_test" in p.name or "block_b_reference" in p.name for p in paths)
