"""D06 one-shot WSL2 wrapper source-only static contract."""
from pathlib import Path
import subprocess

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"axia_d06_cm_wsl2_once.sh"

def test_launcher_bash_syntax_and_local_self_check():
    p=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    r=subprocess.run(["bash",str(SCRIPT),"--self-check"],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    assert "D06_WSL2_WRAPPER_STATIC_PASS; ROS_AND_GAZEBO_NOT_RUN" in r.stdout

def test_launcher_pins_verified_public_source_and_never_claims_gazebo():
    s=SCRIPT.read_text()
    assert 'PUBLIC_SOURCE_SHA="94f4900f89f8e04c4d0a45461ac39ea9e13d6e6f"' in s
    assert 'test "$(git -C "$SRC" rev-parse HEAD)" = "$PUBLIC_SOURCE_SHA"' in s
    assert "d06_cm_live_gate.py" in s
    assert '"gazebo_actual":False' in s
    assert '"cmd_vel_published":False' in s
    assert '"certified_estop":False' in s
    assert 'ros2 topic pub' not in s
    assert 'NavigateToPose' not in s

def test_local_archive_on_failure_or_success():
    s=SCRIPT.read_text()
    assert "owner_summary.json" in s
    assert 'tar -czf "$OUT.tar.gz"' in s
    assert "sha256sum" in s and "SHA256SUMS" in s
    assert 'STATUS="PASS_OFFICIAL_JAZZY_CM_CLEAR_SLOWDOWN_STOP"' in s
    assert 'D06_OWNER_OFFICIAL_CM_L1_PASS' in s
