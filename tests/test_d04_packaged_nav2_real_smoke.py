"""Public CI uses real official Nav2/Gazebo; never claims private P1 acceptance."""
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
import sys

scripts=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(scripts))
spec=spec_from_file_location("d04_package_nav2_real_smoke",scripts/"d04_package_nav2_real_smoke.py")
mod=module_from_spec(spec)
spec.loader.exec_module(mod)


def test_only_official_nav2_ci_shim_not_p1_safety_claim():
    assert "nav2_bringup" in mod.SHIM
    assert "tb3_simulation_launch.py" in mod.SHIM
    assert 'private_axia_p1_executed":False' in (scripts/"d04_package_nav2_real_smoke.py").read_text()
    assert "create_publisher(" not in mod.SHIM
    assert "axia_safety_supervisor" not in mod.SHIM


def test_runtime_smoke_uses_actual_installed_d04_launch(tmp_path):
    cmd=mod.launch_command(tmp_path/"axia_tb3_p1.launch.py",
                           tmp_path/"yolo26n.onnx",tmp_path/"walk.dae")
    assert cmd[:4]==["ros2","launch","axia_d04_vision_demo","d04_p1_yolo.launch.py"]
    assert "headless:=False" in cmd
    assert "cpu_renderer:=True" in cmd
    assert "show_image:=False" in cmd


def test_d04_ci_prohibits_false_success_and_requires_real_person():
    code=(scripts/"d04_package_nav2_real_smoke.py").read_text()
    assert "valid_person(" in code
    assert "valid_rgb(" in code
    assert "_watch_detections_and_images(" in code
    assert "launch_no_lowercase_bool_nameerror" in code
    assert "launch_no_world_file_missing" in code
    assert "send_goal_async(" not in code
    assert "create_publisher(" not in code
    assert "PASS_PACKAGED_OFFICIAL_NAV2_GAZEBO_PERSON" in code


def test_reject_any_p1_other_launch_name(tmp_path):
    try:
        mod.launch_command(tmp_path/"private.launch.py",tmp_path/"test.onnx",tmp_path/"walk.dae")
    except ValueError:
        return
    assert False
