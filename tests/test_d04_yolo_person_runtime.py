"""G-D04-2 unit contract; never substitute it for actual ONNX/Gazebo detection."""
import importlib.util
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("d04_yolo_person_runtime", SCRIPTS / "d04_yolo_person_runtime.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def sample():
    return dict(class_id=0, class_name="person", score=0.78,
                stamp_ns=12345, center_x=300.0, center_y=200.0,
                size_x=120.0, size_y=250.0)


def test_only_real_valid_person_can_pass():
    assert m.valid_person(sample())
    for field, value in (
        ("class_id", 1), ("class_name","truck"), ("score",0.0),
        ("score",float("nan")), ("score",1.5), ("stamp_ns",0),
        ("center_x",-1), ("center_y",500), ("size_x",0),
        ("size_y",481),
    ):
        assert not m.valid_person({**sample(), field:value}), field


def test_gazebo_world_contains_single_real_visual_actor(tmp_path):
    dae = tmp_path / "walk.dae"
    dae.write_text("<COLLADA/>")
    root = ET.fromstring(m.world_with_human(dae))
    actors = root.findall(".//actor")
    assert len(actors) == 1
    assert actors[0].get("name") == "human_actor"
    assert actors[0].findtext("skin/filename") == str(dae.resolve())
    assert root.find(".//include/uri").text == "model://turtlebot3_waffle_pi"
    assert root.find(".//plugin[@filename='gz-sim-sensors-system']") is not None
    assert root.find(".//plugin[@filename='gz-sim-scene-broadcaster-system']") is not None


def test_yolo_has_only_readonly_rgb_detection_and_debug(tmp_path):
    p = tmp_path / "yolo26n.onnx"
    y = m.model_yaml(p)
    assert 'plugins: ["detection", "debug"]' in y
    assert 'rgb_topic: /camera/image_raw' in y
    assert 'provider: cpu' in y
    assert "detection3d" not in y
    assert "tracking" not in y
    assert "cmd_vel" not in y


def test_refuses_non_onnx_path(tmp_path):
    try:
        m.model_yaml(tmp_path / "unverified_model.pt")
    except ValueError:
        pass
    else:
        assert False, "must reject runtime loading of non-ONNX models"


def test_pinned_external_asset_manifest_and_zero_motor_api():
    assert len(m.PINNED_YOLO_SHA) == 40
    assert len(m.PINNED_ONNX_SHA256) == 64
    source=(SCRIPTS/"d04_yolo_person_runtime.py").read_text()
    assert "create_publisher(" not in source
    assert "send_goal_async(" not in source
    assert "fault_injector" not in source
    assert "person = verdict[\"ros_evidence\"][\"person\"]" in source
