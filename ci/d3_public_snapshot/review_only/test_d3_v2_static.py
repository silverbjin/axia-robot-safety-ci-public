"""Minimal static contract for D3 integrated classroom runners."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
SRC = Path(__file__).resolve().parents[1]


def test_entrypoint_exists():
    setup = (SRC / 'setup.py').read_text()
    assert 'd3_scene = axia_d3_demo.scenario:main' in setup


def test_human_proxy_has_obstacle_at_lidar_height():
    root = ET.parse(SRC / 'models/pedestrian_proxy.sdf')
    assert root.find('.//collision[@name="lower_body_scan_collision"]') is not None
    assert len(root.findall('.//visual')) >= 6


def test_live_script_runs_readonly_monitor_and_diag_bridge():
    script = (ROOT / 'training/d03/d3_demo/scripts/run_d3_live_scene.sh').read_text()
    assert 'd3_observer' in script and 'ros_diagnostics_bridge.py' in script
    assert 'd3_scene' in script and '--mode live' in script
    assert 'YES-D3-FAULT' in script
    assert 'D3_START_X' in script and 'D3_END_Y' in script
    for bad in ('ros2 topic pub /cmd_vel', 'ros2 service call /axia/safety/rearm',
                'ros2 service call /axia/safety/reset', 'ros2 action send_goal'):
        assert bad not in script


def test_preview_has_no_fault_authority():
    script = (ROOT / 'training/d03/d3_demo/scripts/run_d3_preview.sh').read_text()
    assert '--mode preview' in script
    assert '--ack-fault' not in script
    assert 'YES-D3-PREVIEW' in script


def test_one_shot_wsl2_preparation_never_forces_branch_or_goal():
    src = (ROOT / 'training/d03/d3_demo/scripts/d3_wsl2_prepare_once.sh').read_text()
    assert '--branch feat/d3-intrusion-scan-stop-demo-20261108' in src
    assert 'merge --ff-only' in src
    assert 'axia_d3_demo' in src and 'colcon build' in src
    assert '--preflight' in src
    for forbidden in ('reset --hard', 'git push', 'ros2 topic pub /cmd_vel',
                      'ros2 service call /axia/fault/scan_drop', '--force'):
        assert forbidden not in src


def test_wsl2_prepare_sources_ros_before_ros_cli_check():
    src=(ROOT / 'training/d03/d3_demo/scripts/d3_wsl2_prepare_once.sh').read_text()
    assert src.index('source /opt/ros/jazzy/setup.bash') < src.index('for cmd in ros2 gz;')