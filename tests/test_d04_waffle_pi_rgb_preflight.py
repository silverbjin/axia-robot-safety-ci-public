"""G-D04-1Pi L0 contract; actual ROS/Gazebo runtime is a distinct CI job."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import xml.etree.ElementTree as ET

SOURCE = Path(__file__).resolve().parents[1] / "scripts/d04_waffle_pi_rgb_preflight.py"
spec = spec_from_file_location("d04_pi", SOURCE)
module = module_from_spec(spec)
spec.loader.exec_module(module)


def test_validate_official_waffle_pi_sdf(tmp_path):
    xml = """<sdf><model><link><sensor name="camera" type="camera">
    <topic>camera/image_raw</topic><gz_frame_id>camera_rgb_frame</gz_frame_id>
    <update_rate>30</update_rate><camera>
      <camera_info_topic>camera/camera_info</camera_info_topic>
      <image><width>640</width><height>480</height><format>R8G8B8</format></image>
    </camera></sensor></link></model></sdf>"""
    path = tmp_path / "model.sdf"
    path.write_text(xml)
    data = module.official_camera_contract(path)
    assert (data["width"],data["height"],data["update_rate"]) == (640,480,30.0)


def test_fail_closed_on_wrong_camera_topic(tmp_path):
    data = """<sdf><model><sensor name="camera" type="camera">
      <topic>wrong</topic><camera><camera_info_topic>camera/camera_info</camera_info_topic>
      <image><width>640</width><height>480</height><format>R8G8B8</format></image>
      </camera></sensor></model></sdf>"""
    path = tmp_path / "model.sdf"
    path.write_text(data)
    try:
        module.official_camera_contract(path)
        assert False, "must refuse changed upstream sensor contract"
    except ValueError:
        pass


def test_reject_empty_invalid_rgb():
    image = {"width":640, "height":480,"encoding":"rgb8",
             "payload_size":640*480*3,"stamp_ns":1000000,"frame_id":"camera_rgb_frame"}
    assert module.valid_rgb(image)
    for name, value in [("width",320),("height",240),("encoding","32FC1"),
                        ("payload_size",0),("stamp_ns",0),("frame_id","")]:
        modified = {**image, name:value}
        assert not module.valid_rgb(modified), name
    assert not module.valid_rgb(None)


def test_camera_info_required():
    info = {"width":640,"height":480,"stamp_ns":1000,"frame_id":"camera_rgb_frame"}
    assert module.valid_camera_info(info)
    assert not module.valid_camera_info({**info,"stamp_ns":0})
    assert not module.valid_camera_info(None)


def test_world_uses_official_model_without_external_fuel_dependency():
    world = module.simple_world()
    root = ET.fromstring(world)
    assert root.find(".//include/uri").text == "model://turtlebot3_waffle_pi"
    assert "fuel.gazebosim.org" not in world
    assert root.find(".//plugin[@filename='gz-sim-sensors-system']") is not None


def test_p1_safe_domain_and_readonly():
    assert 7400 + 250 * module.DOMAIN_ID + 240 < 32768
    content = SOURCE.read_text()
    assert "create_publisher(" not in content
    assert "send_goal_async(" not in content
    assert "fault_injector" not in content
    assert "cmd_vel" not in module.simple_world()
