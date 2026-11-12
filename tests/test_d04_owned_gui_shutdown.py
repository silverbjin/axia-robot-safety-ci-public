"""Regression: D04 GUI must not survive its owned ROS launch.

The field report says image_view closes/reopens after Gazebo exit until WSL
shutdown. Reproduce the exact first ownership bug: ROS launch parent exits
BEFORE a same-session image-view-like child. The old _stop_all() skips the
dead parent and leaks the child. No private instructor, ROS or Gazebo needed.
"""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
GATE = ROOT / "scripts/d04_packaged_p1_yolo_gate.py"
OWNER = ROOT / "scripts/axia_d04_ros_package_wsl2_once.sh"
SHUTDOWN = ROOT / "scripts/d04_owned_gui_shutdown.py"


def _alive(pid):
    try:
        p = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return p[0] not in ("Z", "X")
    except FileNotFoundError:
        return False


def _create_orphan_within_owned_session(tmp_path, ignore_signals=False):
    """Child stays in parent's start_new_session session after parent exits."""
    child = tmp_path / "fake_yolo_image_view.py"
    script = """
import signal, time
if %s:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
while True:
    time.sleep(0.3)
""" % ignore_signals
    child.write_text(script)
    parent = subprocess.Popen(
        [sys.executable, "-c",
         "import subprocess,sys;"
         "c=subprocess.Popen([sys.executable,sys.argv[1]],"
         "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,"
         "stderr=subprocess.DEVNULL);print(c.pid,flush=True)",
         str(child)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        text=True,
    )
    pid = int(parent.stdout.readline().strip())
    parent.wait(timeout=5)
    assert parent.returncode == 0
    assert _alive(pid)
    return parent, pid


def _force_clean(pgid):
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def test_red_orphan_preview_after_dead_ros_launch_is_stopped(tmp_path):
    from d04_owned_gui_shutdown import stop_owned
    parent, child_pid = _create_orphan_within_owned_session(tmp_path)
    try:
        evidence = {}
        stop_owned([("package_launch", parent)], evidence,
                   interrupt_timeout=1.0, terminate_timeout=1.0)
        assert not _alive(child_pid), "ORPHANED_IMAGE_VIEW_AFTER_LAUNCH_EXIT"
        assert evidence["shutdown_group_audit"]["package_launch"]["residual_count"] == 0
        assert evidence["shutdown_group_audit"]["package_launch"]["parent_already_exited"] is True
    finally:
        _force_clean(parent.pid)


def test_orphan_ignoring_sigint_escalates_and_fails_clean_claim(tmp_path):
    from d04_owned_gui_shutdown import stop_owned
    parent, child_pid = _create_orphan_within_owned_session(tmp_path, True)
    try:
        evidence = {}
        stop_owned([("package_launch", parent)], evidence,
                   interrupt_timeout=0.2, terminate_timeout=0.2)
        assert not _alive(child_pid)
        assert "package_launch" in evidence["shutdown_escalated"]
        assert evidence["shutdown_group_audit"]["package_launch"]["residual_count"] == 0
        assert evidence["shutdown_group_audit"]["package_launch"]["sigkill_sent"] is True
    finally:
        _force_clean(parent.pid)


def test_group_shutdown_never_kills_unrelated_preview(tmp_path):
    from d04_owned_gui_shutdown import stop_owned
    parent, child_pid = _create_orphan_within_owned_session(tmp_path)
    other = subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        evidence = {}
        stop_owned([("package_launch", parent)], evidence,
                   interrupt_timeout=0.5, terminate_timeout=0.5)
        assert not _alive(child_pid)
        assert other.poll() is None, "UNRELATED_GUI_PROCESS_KILLED"
    finally:
        _force_clean(parent.pid)
        other.terminate()
        other.wait(timeout=3)


def test_gate_uses_group_audit_and_never_auto_reopens_static_png():
    gate = GATE.read_text()
    wrapper = OWNER.read_text()
    assert "from d04_owned_gui_shutdown import stop_owned" in gate
    assert "stop_owned(proc, verdict)" in gate
    assert "shutdown_group_audit" in gate
    assert "BLOCKED_RESIDUAL_GUI_PROCESSES" in gate
    assert "xdg-open" not in wrapper, "POST_SHUTDOWN_UNOWNED_VIEWER_REOPEN"
    assert "PASS_PACKAGED_P1_YOLO_CLEAN_" in wrapper


def test_shutdown_module_is_pure_stdlib_and_read_only():
    script=SHUTDOWN.read_text()
    assert "os.killpg" in script
    assert "signal.SIGINT" in script
    assert "signal.SIGTERM" in script
    assert "signal.SIGKILL" in script
    for forbidden in ("ros2 topic pub", "ros2 action send_goal", "psutil.Process().kill", "pkill -f", "killall"):
        assert forbidden not in script
