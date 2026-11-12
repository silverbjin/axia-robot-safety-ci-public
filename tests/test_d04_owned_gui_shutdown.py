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
import threading
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


def test_other_process_group_in_same_owned_session_is_stopped(tmp_path):
    """ROS child may change its PGID but remains in D04 launch session."""
    from d04_owned_gui_shutdown import stop_owned
    child = tmp_path / "fake_yolo_other_pgid.py"
    child.write_text("import time\nwhile True: time.sleep(0.2)\n")
    parent = subprocess.Popen(
        [sys.executable, "-c",
         "import subprocess,sys;"
         "c=subprocess.Popen([sys.executable,sys.argv[1]],"
         "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,"
         "stderr=subprocess.DEVNULL,process_group=0);"
         "print(c.pid,flush=True)", str(child)],
        start_new_session=True, stdout=subprocess.PIPE, text=True,
    )
    pid = int(parent.stdout.readline())
    parent.wait(timeout=5)
    assert os.getpgid(pid) == pid
    assert os.getsid(pid) == parent.pid
    try:
        evidence = {}
        stop_owned([("package_launch", parent)], evidence,
                   interrupt_timeout=0.4, terminate_timeout=0.4)
        assert not _alive(pid), "DIFFERENT_PGID_GUI_LEFT_ALIVE"
        assert evidence["shutdown_group_audit"]["package_launch"]["residual_count"] == 0
    finally:
        _force_clean(parent.pid)
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def test_closing_first_gazebo_gui_ends_hold_early(tmp_path):
    from d04_owned_gui_shutdown import wait_for_gui_hold
    # The process name is matched from owned /proc cmdline, not system-wide.
    parent, gui = _create_orphan_within_owned_session(tmp_path)
    gui_path = tmp_path / "fake_yolo_image_view.py"
    gazebo_path = tmp_path / "mock_gz-sim-gui.py"
    gazebo_path.write_bytes(gui_path.read_bytes())
    another = subprocess.Popen(
        [sys.executable, str(gazebo_path)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        # Use parent's existing session via a small fork from test subprocess
        # instead of injecting a GUI into unrelated user's process group.
    )
    # Separate session would be correctly ignored. For deterministic test,
    # spawn gazebo named process via an owned session leader.
    another.terminate()
    another.wait(timeout=3)
    _force_clean(parent.pid)
    leader = subprocess.Popen(
        [sys.executable, "-c",
         "import subprocess,sys,time;"
         "c=subprocess.Popen([sys.executable,sys.argv[1]],"
         "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,"
         "stderr=subprocess.DEVNULL);print(c.pid,flush=True);"
         "time.sleep(3)",
         str(gazebo_path)],
        start_new_session=True, stdout=subprocess.PIPE, text=True,
    )
    gui_pid = int(leader.stdout.readline())
    assert _alive(gui_pid)
    try:
        timer = threading.Timer(0.4, lambda: os.kill(gui_pid, signal.SIGTERM))
        timer.start()
        started = time.monotonic()
        result = wait_for_gui_hold(leader.pid, 4, poll_interval=0.05)
        assert result["reason"] == "GAZEBO_GUI_EXITED_OR_RESTARTED", result
        assert result["observed_gazebo_gui"] is True
        assert time.monotonic() - started < 2.5
        timer.join(timeout=2)
    finally:
        _force_clean(leader.pid)


def test_real_gate_binds_gazebo_gui_disappearance_to_shutdown():
    gate = GATE.read_text()
    assert "wait_for_gui_hold(" in gate
    assert "GAZEBO_GUI_EXITED_OR_RESTARTED" in gate
    assert gate.index("wait_for_gui_hold(") < gate.index("stop_owned(proc, verdict)")
