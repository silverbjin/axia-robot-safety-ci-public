"""Three real-run evidence contract (synthetic unit fixtures never count as live PASS)."""
from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
import json
HERE=Path(__file__).resolve().parents[1]
spec=spec_from_file_location("stability",HERE/"scripts/d04_yolo_stability.py")
m=module_from_spec(spec);spec.loader.exec_module(m)

def test_evaluate_round_requires_actual_png_and_verdict(tmp_path):
    assert not m.evaluate_round(tmp_path,0)["passed"]
    (tmp_path/"verdict.json").write_text(json.dumps({
        "status":"PASS_REAL_GAZEBO_PERSON_BBOX_CONFIDENCE",
        "ros_evidence":{"camera_frames":1,"detection_frames":1,"debug_frames":1,
                        "person":{"class_name":"person","score":0.9}}}))
    assert not m.evaluate_round(tmp_path,0)["passed"]
    (tmp_path/"camera_frame.png").write_bytes(b"a")
    (tmp_path/"debug_frame.png").write_bytes(b"b")
    assert m.evaluate_round(tmp_path,0)["passed"]
    assert not m.evaluate_round(tmp_path,2)["passed"]

def test_reject_non_3x_stability():
    import pytest
    with pytest.raises(ValueError):
        m.run(2,Path("/tmp/never-run"))

def test_real_runner_is_not_a_fake_publisher():
    source=(HERE/"scripts/d04_yolo_stability.py").read_text()
    assert 'd04_yolo_person_runtime.py' in source
    assert "send_goal_async(" not in source
    assert "create_publisher(" not in source
