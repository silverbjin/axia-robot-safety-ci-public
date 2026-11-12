"""D04 ROS CLI WSL2 regressions. Public CI fake-ROS contract, not a live Gazebo test."""
from pathlib import Path
import os
import subprocess

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/axia_d04_ros_cli_diagnose.sh"
YOLO_SHA="94d2dd500cb26027ee9c019f4d3a02029ac615cc"
D04_SHA="f2edba114dd0540d1f27a1e216bfda2b885c5cb9"

def fake_env(tmp_path):
    home=tmp_path/"home"
    home.mkdir()
    ros=tmp_path/"ros_setup.bash"
    yolo=tmp_path/"yolo_setup.bash"
    d04=tmp_path/"d04_setup.bash"
    ros.write_text("export MOCK_ROS_SOURCED=1\n")
    yolo.write_text("export MOCK_YOLO_SOURCED=1\n")
    d04.write_text("export MOCK_D04_SOURCED=1\n")
    bin_dir=tmp_path/"bin"
    bin_dir.mkdir()
    fake=bin_dir/"ros2"
    fake.write_text("""#!/usr/bin/env bash
case "$1 $2 $3" in
  "pkg prefix yolo_msgs")
    [[ "$MOCK_YOLO_SOURCED" == 1 ]] && exit 0 || exit 1 ;;
  "interface show yolo_msgs/msg/DetectionArray")
    [[ "$MOCK_YOLO_SOURCED" == 1 ]] || exit 1
    printf 'std_msgs/Header header\\nyolo_msgs/Detection[] detections\\n'; exit 0 ;;
  "topic list -t")
    [[ "$MOCK_LIVE" == 0 ]] && exit 0
    echo '/camera/image_raw [sensor_msgs/msg/Image]'
    echo '/yolo/cam0/detections [yolo_msgs/msg/DetectionArray]'; exit 0 ;;
  "topic type /yolo/cam0/detections")
    echo 'yolo_msgs/msg/DetectionArray'; exit 0 ;;
  "topic info -v")
    [[ "$MOCK_LIVE" == 0 ]] && { echo "Unknown topic '$4'"; exit 1; }
    if [[ "$4" == /camera/image_raw && ! -f "$MOCK_PROBE_STATE/camera_once" ]]; then
      touch "$MOCK_PROBE_STATE/camera_once"
      echo "Unknown topic '$4'"; exit 1
    fi
    echo 'Publisher count: 1'; exit 0 ;;
  "topic hz /camera/image_raw"|"topic hz /yolo/cam0/detections")
    [[ "$MOCK_LIVE" == 0 ]] && { echo 'does not appear to be published'; exit 1; }
    echo 'average rate: 4.500'; exit 0 ;;
esac
echo "UNKNOWN MOCK ros2 arguments: $*" >&2
exit 5
""")
    fake.chmod(0o755)
    env=os.environ.copy()
    env.update({
        "HOME":str(home),
        "PATH":str(bin_dir)+":"+os.environ["PATH"],
        "AXIA_D04_CLI_ROS_SETUP":str(ros),
        "AXIA_D04_CLI_YOLO_SETUP":str(yolo),
        "AXIA_D04_CLI_D04_SETUP":str(d04),
        "MOCK_PROBE_STATE":str(tmp_path),
        "MOCK_LIVE":"1",
    })
    return env

def run(tmp_path,*args,env=None):
    return subprocess.run(["bash",str(RUNNER),*args],cwd=tmp_path,env=env,
                          text=True,capture_output=True,timeout=16)

def test_runner_exists_and_bash_syntax():
    assert RUNNER.is_file(), "RED: no overlay-aware D04 CLI; yolo_msgs type invalid"
    assert subprocess.run(["bash","-n",str(RUNNER)],capture_output=True).returncode==0
    source=RUNNER.read_text()
    assert YOLO_SHA in source and D04_SHA in source
    assert "source " in source
    assert "ros2 interface show yolo_msgs/msg/DetectionArray" in source

def test_doctor_sources_custom_detection_type_from_any_cwd(tmp_path):
    env=fake_env(tmp_path)
    result=run(tmp_path,"--doctor",env=env)
    assert result.returncode==0,result.stdout+result.stderr
    assert "D04_CLI_YOLO_MSGS_TYPE_READY" in result.stdout
    assert "D04_CLI_LIVE_DATA=NOT_CHECKED" in result.stdout
    assert "D04_CLI_ROS_DOMAIN_ID=40" in result.stdout
    assert "D04_CLI_DISCOVERY_RANGE=LOCALHOST" in result.stdout

def test_missing_yolo_overlay_blocks_before_ros2_topics(tmp_path):
    env=fake_env(tmp_path)
    env["AXIA_D04_CLI_YOLO_SETUP"]=str(tmp_path/"missing_yolo_setup.bash")
    result=run(tmp_path,"--doctor",env=env)
    assert result.returncode==2
    assert "D04_CLI_YOLO_OVERLAY_MISSING" in result.stdout
    assert "D04_CLI_YOLO_MSGS_TYPE_READY" not in result.stdout

def test_live_retries_transient_graph_info_then_checks_two_message_rates(tmp_path):
    env=fake_env(tmp_path)
    result=run(tmp_path,"--live",env=env)
    assert result.returncode==0,result.stdout+result.stderr
    assert "D04_CLI_CAMERA_TOPIC_INFO_RETRY" in result.stdout
    assert "D04_CLI_CAMERA_RATE_OBSERVED" in result.stdout
    assert "D04_CLI_DETECTION_RATE_OBSERVED" in result.stdout
    assert "D04_CLI_LIVE_OBSERVATION=PASS_CLI_SAMPLING_ONLY" in result.stdout

def test_no_live_topics_is_not_bridge_failure(tmp_path):
    env=fake_env(tmp_path)
    env["MOCK_LIVE"]="0"
    result=run(tmp_path,"--live",env=env)
    assert result.returncode==3
    assert "D04_CLI_LIVE_OBSERVATION=UNAVAILABLE" in result.stdout
    assert "D04_CLI_BRIDGE_BROKEN" not in result.stdout

def test_public_workflow_has_no_private_ci():
    flow=(ROOT/".github/workflows/d04-course-docs-regression.yml").read_text()
    assert "instructor-private-doc-commands" not in flow
    assert "axia-instructor-sealed" not in flow
    assert "secrets.AXIA_CLOUD_CI" not in flow
