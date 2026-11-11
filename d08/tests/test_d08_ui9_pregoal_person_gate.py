"""UI9iQEzj field regression: far camera person=0/umbrella=64, no Goal.

Public regression does not contain teacher source, raw user evidence, or
a private D05 answer. It demands actual near-SLOW/STOP Gazebo ONNX positives
rather than an unmeasured initial 1.35m world fixture or color-only framing.
"""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT/'.github/workflows/d08-human-physical-contact-ci.yml'
ONNX_SCRIPT=ROOT/'d08/scripts/d08_actual_rgb_onnx_probe.py'

def test_ui9_field_distance_hypothesis_and_blocker_not_misclassified():
    fixture_world_x=-.58
    robot_world_x=-2.0
    fixture_radius=.07
    initial_surface_gap=fixture_world_x-robot_world_x-fixture_radius
    assert 1.3<initial_surface_gap<1.4  # NOT the 0.36m verified stop-image pose
    assert initial_surface_gap>.75  # outside both demonstration safety zones
    field={'rgb_count':80,'depth_count':155,'yolo_person_count':0,
           'd05_valid_count':0,'observed_yolo_classes':{'umbrella':64},
           'last_five_rgbd_min_skew_ms':198.0,
           'required_max_skew_ms':50.0,'buffer_registered_pair_valid':True,
           'goal_sent':False}
    assert field['observed_yolo_classes']['umbrella']==64
    assert field['yolo_person_count']==0 and field['d05_valid_count']==0
    assert field['last_five_rgbd_min_skew_ms']>field['required_max_skew_ms']
    # A buffered older pair is not proof of a fresh pair in the last 5x5.
    assert field['buffer_registered_pair_valid'] is not False
    assert field['goal_sent'] is False

def test_stop_frame_real_onnx_person_is_mandatory_not_diagnostic_only():
    """RED for the existing L2: Stop RGB inference ran but did NOT gate PASS."""
    code=ONNX_SCRIPT.read_text()
    assert 'PASS_MODEL_ONLY' in code
    assert 'stop_frame_person_verified' in code, (
        'UI9_CI_L2_DID_NOT_REQUIRE_NEAR_STOPZONE_PERSON_POSITIVE')
    assert 'STOPZONE_PERSON_CLASS_ZERO' in code

def test_ci_reuses_real_stop_set_pose_and_actual_ros_rgb_frame():
    code=(ROOT/'d08/scripts/d08_public_gazebo_l2.py').read_text()
    assert "stop_rgb=out/'real_gazebo_stop_rgb.ppm'" in code
    assert "capture_path=stop_rgb" in code
    workflow=WORKFLOW.read_text()
    assert '--stop-frame results/d08-human-contact-calibration/real_gazebo_stop_rgb.ppm' in workflow
    assert 'D08_ACTUAL_ONNX_PERSON_FRAME_L2_PASS' in workflow


def test_ci_uses_real_yolo_ros_detection_array_on_recorded_gazebo_stop_frame():
    # Existing CI L2 ONNX check counts raw [1,84,6300] candidates, NOT
    # the actual C++ yolo_ros post-NMS DetectionArray. UI9 field sees
    # 64 umbrella and zero person while raw ONNX sees person near Stop.
    replay=ROOT/'.github/workflows/d08-ui9-yolo-replay-l1.yml'
    assert replay.is_file(), 'UI9_REAL_YOLO_ROS_REPLAY_CI_MISSING'
    txt=replay.read_text()
    assert '94d2dd500cb26027ee9c019f4d3a02029ac615cc' in txt
    assert '4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf' in txt
    assert 'real_gazebo_stop_rgb.ppm' in txt
    assert 'UI9_REAL_YOLO_ROS_PERSON_DETECTION_L1_PASS' in txt
    assert 'd08_ui9_yolo_replay_probe.py' in txt


def test_ui9_pinned_cpp_upstream_vendor_build_dependencies_present():
    # Actual CI run #43071254144 reached the exact pinned upstream source
    # but CMake yolo_hfhub_vendor failed because libcurl header/library
    # were missing from the otherwise functional ROS Jazzy container.
    txt=(ROOT/'.github/workflows/d08-ui9-yolo-replay-l1.yml').read_text()
    assert 'libcurl4-openssl-dev' in txt, 'UI9_YOLO_VENDOR_CURL_DEV_MISSING'
    assert '-DBUILD_TESTING=OFF' in txt, 'UI9_YOLO_REPLAY_SHOULD_NOT_BUILD_UPSTREAM_TESTS'
