"""TDD: P1+YOLO no-command overlay. No private P1 source required for L0."""
from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import pytest
HERE=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(HERE))
def module(name):
    spec=spec_from_file_location(name,HERE/(name+".py"))
    m=module_from_spec(spec);spec.loader.exec_module(m);return m
o=module("d04_p1_vision_overlay")
p=module("d04_p1_yolo_live")

def fixture_files(tmp_path):
    waffle=tmp_path/"waffle.xacro"
    waffle.write_text("""<sdf xmlns:xacro="http://www.ros.org/wiki/xacro"><xacro:arg name="namespace" default=""/>
     <model name="turtlebot3_waffle"><link name="camera_link"/>
      <sensor name="scan" type="gpu_lidar"/>
      <plugin filename="gz-sim-diff-drive-system" name="DiffDrive">
        <topic>$(arg namespace)/cmd_vel</topic></plugin>
     </model></sdf>""")
    pi=tmp_path/"pi.sdf"
    pi.write_text("""<sdf><model><link><sensor type="camera" name="camera">
      <topic>camera/image_raw</topic>
      <camera><camera_info_topic>camera/camera_info</camera_info_topic>
      <image><width>640</width><height>480</height><format>R8G8B8</format></image>
      </camera></sensor></link></model></sdf>""")
    world=tmp_path/"world.xacro"
    world.write_text("""<sdf xmlns:xacro="http://www.ros.org/wiki/xacro"><world name="default">
      <plugin filename="gz-sim-sensors-system"><render_engine>ogre2</render_engine></plugin>
      </world></sdf>""")
    dae=tmp_path/"walk.dae"; dae.write_text("<COLLADA/>")
    return waffle,pi,world,dae

def test_overlay_adds_only_readonly_camera_and_visual_actor(tmp_path):
    waffle,pi,world,dae=fixture_files(tmp_path)
    before=waffle.read_bytes(),pi.read_bytes(),world.read_bytes()
    d=o.make_overlay(waffle,pi,world,dae,tmp_path/"out",cpu_renderer=True)
    assert (waffle.read_bytes(),pi.read_bytes(),world.read_bytes())==before
    r=ET.parse(d["robot_sdf"]).getroot()
    assert len(r.findall(".//sensor"))==2
    assert r.find(".//sensor[@name='axia_d04_rgb']") is not None
    assert r.find(".//plugin[@filename='gz-sim-diff-drive-system']/topic").text=="$(arg namespace)/cmd_vel"
    w=ET.parse(d["world"]).getroot()
    assert w.find(".//actor[@name='axia_d04_person']") is not None
    assert w.find(".//actor/collision") is None
    assert w.find(".//plugin[@filename='gz-sim-sensors-system']/render_engine").text=="ogre"
    assert d["p1_model_control_modified"] is False

def test_fail_closed_when_upstream_camera_contract_changes(tmp_path):
    args=fixture_files(tmp_path)
    pi=args[1]
    pi.write_text(pi.read_text().replace("640","320"))
    with pytest.raises(ValueError,match="RGB image contract"):
        o.make_overlay(*args,tmp_path/"out")

def test_graph_chain_comparison_detects_second_publisher():
    a={"/cmd_vel":{"publishers":[{"node_name":"collision_monitor"}],"subscriptions":[]}}
    b={"/cmd_vel":{"publishers":[{"node_name":"collision_monitor"},{"node_name":"other"}],"subscriptions":[]}}
    assert p.core_chain(a)!=p.core_chain(b)

def test_no_motor_goals_and_exact_private_commit_enforced():
    src=(HERE/"d04_p1_yolo_live.py").read_text()
    assert "send_goal_async(" not in src
    assert "create_publisher(" not in src
    assert "allow_fault_injection:=false" in src
    assert 'if sha!=a.p1_sha' in src
    assert "p1_t05_graph_oracle.py" in src

def test_no_safety_code_change_by_sensor_overlay():
    src=(HERE/"d04_p1_vision_overlay.py").read_text()
    assert "cmd_vel_supervised" not in src
    assert "collision_monitor" not in src
    assert "DiffDrive" not in src
