"""L0 fail-closed contract for D06 isolated CM terminal-B observer."""
import importlib.util
import os
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "d06_cm_l1_terminal_b_readonly.py"
spec = importlib.util.spec_from_file_location("d06_terminal_b", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fake_proc(root, pid, argv, environ):
    p = root / str(pid)
    p.mkdir()
    (p / "cmdline").write_bytes(b"\0".join(x.encode() for x in argv) + b"\0")
    (p / "environ").write_bytes(b"\0".join(x.encode() for x in environ) + b"\0")


def test_exact_cm_pid_and_domain_only(tmp_path):
    fake_proc(tmp_path, 101, ["/opt/ros/jazzy/lib/nav2_collision_monitor/collision_monitor",
                "--ros-args", "--params-file", "/tmp/d06/params/collision_monitor_d06.yaml"],
              ["ROS_DOMAIN_ID=83", "ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST"])
    fake_proc(tmp_path, 102, ["/usr/bin/python3", "not_collision_monitor", "collision_monitor_d06.yaml"],
              ["ROS_DOMAIN_ID=84", "ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST"])
    assert mod.select_unique(mod.find_d06_cm(tmp_path, os.getuid())) == (101, "83", "")


def test_fail_closed_unknown_or_foreign_ros_domain(tmp_path):
    fake_proc(tmp_path, 101, ["/opt/collision_monitor", "--params-file", "collision_monitor_d06.yaml"],
              ["ROS_DOMAIN_ID=233", "ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST"])
    fake_proc(tmp_path, 102, ["/opt/collision_monitor", "--params-file", "collision_monitor_d06.yaml"],
              ["ROS_DOMAIN_ID=24", "ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET"])
    assert mod.find_d06_cm(tmp_path, os.getuid()) == []


def test_multiple_d06_cm_are_rejected(tmp_path):
    for p in (101, 102):
        fake_proc(tmp_path, p, ["/opt/collision_monitor", "--params-file", "collision_monitor_d06.yaml"],
                  [f"ROS_DOMAIN_ID={p}", "ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST"])
    try:
        mod.select_unique(mod.find_d06_cm(tmp_path, os.getuid()))
    except RuntimeError as e:
        assert "MULTIPLE_CM" in str(e)
    else:
        assert False, "multiple CM candidates must be blocked"


def test_readonly_contract_source():
    src = SCRIPT.read_text()
    assert "create_subscription" in src
    for forbidden in ("create_publisher(", "send_goal_async(", "publish(", "ros2 lifecycle set", "ros2 action send_goal"):
        assert forbidden not in src
