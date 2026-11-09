"""D05 public source-only contracts; no private instructor answers."""
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from d05_rgbd_gazebo_scene import make_world, WIDTH, HEIGHT, RGB_TOPIC, DEPTH_TOPIC

def test_single_source_geometry():
    root=ET.fromstring(make_world())
    sensors=root.findall(".//sensor[@type='rgbd_camera']")
    assert len(sensors)==1
    s=sensors[0]
    assert s.findtext("topic")=="axia/d05/rgbd"
    assert s.findtext("gz_frame_id")=="axia_d05_rgbd_optical"
    assert s.findtext("camera/image/width")==str(WIDTH)
    assert s.findtext("camera/image/height")==str(HEIGHT)
    assert RGB_TOPIC.endswith("/image") and DEPTH_TOPIC.endswith("/depth_image")
    assert len(root.findall(".//model[@name='sensor_only_calibration_box']"))==1
    assert root.find(".//include/uri").text=="model://turtlebot3_waffle_pi"

def test_actor_run_does_not_include_calibration_proxy(tmp_path):
    mesh=tmp_path/"walk.dae";mesh.write_text("dummy is only an SDF pathname")
    root=ET.fromstring(make_world(actor_mesh=mesh))
    assert len(root.findall(".//actor[@name='human_actor']"))==1
    assert not root.findall(".//model[@name='sensor_only_calibration_box']")
    assert len(root.findall(".//sensor[@type='rgbd_camera']"))==1

def test_public_runner_no_actuator_calls():
    for name in ("d05_rgbd_gazebo_scene.py","d05_rgbd_sensor_preflight.py"):
        data=(Path(__file__).resolve().parents[1]/"scripts"/name).read_text()
        assert "Twist(" not in data
        assert "NavigateToPose" not in data
        assert "create_publisher(" not in data
