"""D04 owner runner regressions after reported WSL2 name 'false' launch failure."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
WRAPPER=ROOT/"scripts/axia_d04_ros_package_wsl2_once.sh"
RUNTIME=ROOT/"scripts/d04_packaged_p1_yolo_gate.py"


def test_shell_owner_script_never_hides_missing_assets_in_if_condition():
    src=WRAPPER.read_text()
    assert "|| ! echo \"[D04][ASSETS]" not in src
    assert 'echo "$ONNX_SHA  $MODEL" | sha256sum -c - >/dev/null 2>&1' in src
    assert 'echo "$DAE_SHA  $ACTOR" | sha256sum -c - >/dev/null 2>&1' in src


def test_new_private_d04_package_commit_pinned():
    src=WRAPPER.read_text()
    assert 'PRIVATE_SHA="f2edba114dd0540d1f27a1e216bfda2b885c5cb9"' in src
    assert "AXIA_D04_PUBLIC_SHA" in src
    assert 'AXIA_D04_GUI' in src


def test_early_launch_failure_detected_before_long_oracle_wait():
    src=RUNTIME.read_text()
    assert "D04_PACKAGE_LAUNCH_EXITED_EARLY" in src
    assert "package_launch.log" in src
    assert "P1_GRAPH_BEFORE" in src
    assert "create_publisher(" not in src
    assert "send_goal_async(" not in src


def test_owner_wrapper_bash_syntax_and_no_motion():
    assert subprocess.run(["bash","-n",str(WRAPPER)],capture_output=True).returncode==0
    src=WRAPPER.read_text()
    assert "ros2 topic pub /cmd_vel" not in src
    assert "ros2 action send_goal" not in src
