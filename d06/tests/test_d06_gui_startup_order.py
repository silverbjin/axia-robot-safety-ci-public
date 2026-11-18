"""Fail-first: do not overload official Nav2 Lifecycle startup with RViz."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SIDECAR=(ROOT/"d06/scripts/d06_rviz_sidecar.sh").read_text()

def test_owner_rviz_sidecar_waits_for_actual_nav2_startup_ready_before_gui():
    assert "startup_verdict.json" in SIDECAR
    assert "SMOKE_READY" in SIDECAR
    assert "D06_GUI_NAV2_STARTUP_READY_NO_GOAL" in SIDECAR
    assert SIDECAR.index("D06_GUI_NAV2_STARTUP_READY_NO_GOAL") < SIDECAR.index("setsid taskset")

def test_no_forged_ready_goal_or_new_publisher_in_display_sidecar():
    for bad in ("AXIA_G07_CI_SIM_GOAL_ALLOWED=1","echo YES-P2-G07-GOAL",
                "ros2 action send_goal","ros2 topic pub /cmd_vel"):
        assert bad not in SIDECAR
    assert "D06_GUI_NAV2_STARTUP_MISSING_OR_UNVERIFIED" in SIDECAR
