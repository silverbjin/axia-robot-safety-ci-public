"""Small RED/GREEN helper contract: no ROS/Gazebo dependency."""
import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "d04_rgb_discovery_readonly.py"
spec = importlib.util.spec_from_file_location("d04_probe", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_select_rgb_not_depth():
    text = "\n".join([
        "/world/default/model/turtlebot3_waffle/link/camera_link/sensor/r200/depth_image",
        "/world/default/model/turtlebot3_waffle/link/camera_link/sensor/r200/image",
        "/world/default/model/turtlebot3_waffle/link/camera_link/sensor/r200/camera_info",
    ])
    assert module.choose_rgb_topic(text).endswith("/r200/image")


def test_no_rgb_does_not_fabricate_topic():
    assert module.choose_rgb_topic("/scan\n/clock\n/world/default/state\n") is None


def test_exclude_camera_info_and_depth():
    assert module.choose_rgb_topic("/world/default/camera_info\n/robot/depth_image\n") is None


def test_reject_invalid_image_payload():
    assert not module.image_is_valid(320, 240, "", 200)
    assert not module.image_is_valid(320, 0, "rgb8", 200)
    assert not module.image_is_valid(320, 240, "rgb8", 0)
    assert module.image_is_valid(320, 240, "rgb8", 320 * 240 * 3)


def test_no_command_publication_in_preflight():
    src = SOURCE.read_text(encoding="utf-8")
    assert "create_publisher(" not in src
    assert "send_goal_async(" not in src
    assert "fault_injector_node" not in src


def test_ros_domain_id_is_below_ephemeral_udp_threshold():
    src = SOURCE.read_text(encoding="utf-8")
    assert 'env["ROS_DOMAIN_ID"] = "40"' in src
    assert 7400 + 250 * 40 + 240 < 32768


def test_rgb_under_depth_named_sensor_is_valid():
    # Official Waffle SDF names its RGB-capable depth sensor this way.
    rgb = "/world/default/model/turtlebot3_waffle/link/camera_link/sensor/intel_realsense_r200_depth/image"
    depth = "/world/default/model/turtlebot3_waffle/link/camera_link/sensor/intel_realsense_r200_depth/depth_image"
    assert module.choose_rgb_topic(depth + "\\n" + rgb) == rgb
