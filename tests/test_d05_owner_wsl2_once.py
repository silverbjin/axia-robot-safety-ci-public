"""D05 instructor WSL2 launcher contract. No local ROS execution in this CI."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_d05_rgbd_wsl2_once.sh"

def test_bash_parser_and_no_network_self_check():
    assert SCRIPT.is_file()
    syntax=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True)
    assert syntax.returncode==0,syntax.stderr
    check=subprocess.run(["bash",str(SCRIPT),"--self-check"],capture_output=True,text=True)
    assert check.returncode==0,check.stderr
    assert "AXIA_D05_WSL2_WRAPPER_STATIC_OK; GAZEBO_NOT_RUN" in check.stdout

def test_exact_verified_source_pins_and_safety_boundaries():
    s=SCRIPT.read_text(encoding="utf-8")
    assert 'PUBLIC_SHA="2dcd5f5cad091f9bd3e5fce71e0009d9e18d609d"' in s
    assert 'PRIVATE_SHA="e26069e3d2396e9d9ee89addfb6d7c07794ef6fb"' in s
    assert 'YOLO_SHA="94d2dd500cb26027ee9c019f4d3a02029ac615cc"' in s
    assert 'gh auth status' in s
    assert 'git -C "$SRC/instructor" fetch --depth 1 origin "$PRIVATE_SHA"' in s
    assert 'test "$(git -C "$SRC/instructor" rev-parse HEAD)" = "$PRIVATE_SHA"' in s
    assert 'test "$(git -C "$SRC/public" rev-parse HEAD)" = "$PUBLIC_SHA"' in s
    assert "AXIA_D05_WSL2_REAL_RGBD_VALID_TO_UNKNOWN_PASS" in s
    assert 'assert unknown.get("status")=="UNKNOWN"' in s
    assert 'assert v.get("yolo_continued_after_loss") is True' in s
    assert 'assert v.get("certified_estop") is False' in s
    assert "d05_real_rgbd_l2_gate.py" in s
    assert "gazebo" in s.lower()
    assert "/cmd_vel" not in s
    assert "ros2 topic pub" not in s
    assert "Goal" in s

def test_evidence_and_source_isolation():
    s=SCRIPT.read_text(encoding="utf-8")
    assert "owner_summary.json" in s
    assert 'mkdir -p "$CACHE" "$EVIDENCE_BASE"' in s
    assert "sha256sum" in s
    assert 'tar -czf "$OUT.tar.gz"' in s
    assert 'EVIDENCE=$OUT' in s
    assert 'ARCHIVE=$OUT.tar.gz' in s
    assert 'if [[ "$SRC" == "$CACHE"/checkout-* ]]; then rm -rf -- "$SRC"; fi' in s
    assert 'STATUS="PASS_REAL_GAZEBO_RGBD_VALID_TO_UNKNOWN"' in s

def test_gate_checks_real_callbacks_not_simulated_success():
    source=(ROOT/"scripts/d05_real_rgbd_l2_gate.py").read_text()
    assert 'rclpy.spin_once(node' in source
    assert 'os.killpg(depth_bridge.pid,signal.SIGINT)' in source
    assert 'and evidence["rgb_continued_after_loss"]' in source
    assert 'and evidence["yolo_continued_after_loss"]' in source
