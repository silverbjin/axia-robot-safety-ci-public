"""D06 latest MVP P4 G07 CPU partition reuse, RED before minimal sidecar fix.
Owner CM-only safety processes and Guard/TTL are never modified here.
CI source-only verification is not real Gazebo L2 or WSLg L3.
"""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
SELECTOR=ROOT/"d06/live/d06_gui_cpu_plan.py"
SIDECAR=ROOT/"d06/scripts/d06_rviz_sidecar.sh"

def run(*args):
    return subprocess.run([sys.executable,str(SELECTOR),*args],
                          text=True,capture_output=True,check=False)

def test_monitor_cpu_disjoint_from_official_cm_renderer_bag():
    for cpus,gui,monitor,cm,bag in (
        ("0,1,2,3",0,2,1,3),
        ("0,1,2,3,4,5,6,7",0,6,1,7),
        ("12,17,21,29,30",12,29,17,30),
    ):
        r=run("--cpus",cpus,"--role","monitor")
        assert r.returncode==0,r.stderr
        value=int(r.stdout.strip())
        assert value==monitor
        assert value not in (gui,cm,bag)
        gui_result=run("--cpus",cpus,"--role","gui")
        assert gui_result.returncode==0
        assert int(gui_result.stdout.strip())==gui

def test_monitor_cpu_fails_closed_under_four_allowed_cores():
    for cpus in ("2","2,3","2,3,4","4,4,4,4"):
        r=run("--cpus",cpus,"--role","monitor")
        assert r.returncode!=0
        assert "INSUFFICIENT" in r.stderr

def test_owner_sidecar_observer_no_longer_pinned_to_rviz_render_core():
    s=SIDECAR.read_text()
    assert "MONITOR_CPU=" in s
    assert "GUI_CPU=" in s
    assert s.count('taskset -c "$GUI_CPU"')==1
    assert 'taskset -c "$MONITOR_CPU" nice -n 7' in s
    assert "D06_MVP_CPU_PARTITION" in s
    assert "YES-P2-G07-GOAL" not in s
    assert "AXIA_G07_CI_SIM_GOAL_ALLOWED" not in s
