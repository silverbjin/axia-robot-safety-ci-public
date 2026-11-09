"""D07 WSL2 command wrapper Bash/static source safety contract."""
import subprocess
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"axia_d07_nav2_wsl2_once.sh"

def test_bash_parser_and_offline_self_check():
    s=subprocess.run(["bash","-n",str(SCRIPT)],text=True,capture_output=True)
    assert s.returncode==0,s.stderr
    v=subprocess.run(["bash",str(SCRIPT),"--self-check"],text=True,capture_output=True)
    assert v.returncode==0,v.stderr
    assert "D07_WSL2_WRAPPER_STATIC_OK; NAV2_AND_GAZEBO_NOT_RUN" in v.stdout

def test_immutable_verified_source_and_safety_boundaries():
    s=SCRIPT.read_text()
    assert 'SOURCE_SHA="158b7c6032d987177d1e1302bf85fd741120fd9e"' in s
    assert 'test "$(git -C "$SRC" rev-parse HEAD)" = "$SOURCE_SHA"' in s
    assert "d07_nav2_planner_l1.py" in s
    assert '"/cmd_vel"' not in s
    assert "ros2 topic pub" not in s
    assert 'gazebo_actual":False' in s
    assert 'cmd_vel_published":False' in s

def test_fail_closed_and_preserve_local_archive():
    s=SCRIPT.read_text()
    assert "owner_summary.json" in s
    assert "SHA256SUMS" in s
    assert 'tar -czf "$OUT.tar.gz"' in s
    assert 'GATE_RC=0' in s
    assert 'D07_OWNER_OFFICIAL_NAV2_L1_PASS' in s
    assert 'STATUS="PASS_OFFICIAL_NAV2_COSTMAP_REPLAN_L1"' in s
