"""D08 public main source contract: NO Goal, no private code or safety acceptance."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
L2=ROOT/"d08/scripts/d08_public_gazebo_l2.py"
ONNX=ROOT/"d08/scripts/d08_actual_rgb_onnx_probe.py"
YOLO=ROOT/"d08/scripts/d08_ui9_yolo_replay_probe.py"
WF=ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml"

def test_ui9_real_native_pose_and_bounded_scan_are_required():
    s=L2.read_text()
    for token in ("ui9_reversible_pose_admission", "near_world_xyz_m",
                  "far_world_xyz_m", "native_set_pose_ack",
                  "D08_UI9_REAL_GAZEBO_NEAR_RESTORE_L2_PASS",
                  "actual_registered_rgbd", "goal_sent"):
        assert token in s
    for token in ("send_goal_async(", "ActionClient(", "create_publisher(Twist"):
        assert token not in s

def test_real_pixels_go_to_pinned_inference_and_ros_detection_array():
    assert "D08_ACTUAL_ONNX_PERSON_FRAME_L2_PASS" in ONNX.read_text()
    s=YOLO.read_text()
    assert "DetectionArray" in s and "real_ros_yolo_ros_detection_array" in s
    assert "UI9_REAL_YOLO_ROS_PERSON_DETECTION_L1_PASS" in WF.read_text()
    assert "ROS sensor_msgs/Image REPLAY" in s
    assert "send_goal_async(" not in s

def test_public_workflow_no_protected_or_teacher_checkout_and_no_goal():
    s=WF.read_text()
    for forbidden in (
      "environment: axia-instructor-sealed", "AXIA_CLOUD_CI",
      "repository: silverbjin/axia-robot-safety-instructor",
      "YES-P2-G07-GOAL", "p2_owner_l3_wsl2.sh",
    ):
        assert forbidden not in s
    for required in (
      "D08_UI9_REAL_GAZEBO_NEAR_RESTORE_L2_PASS",
      "D08_UI9_NEAR_ACTUAL_RGB_ONNX_PERSON_L2_PASS",
      "d08_public_gazebo_l2.py", "--lidar-pre-goal --cm-cadence-l1",
    ):
        assert required in s
