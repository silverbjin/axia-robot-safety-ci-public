"""Regression: ROS-sourced PYTHONPATH causes pytest11 import of missing yaml."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / 'scripts' / 'axia_d08_instructor_wsl2_once.sh'

def test_reproduce_ambient_ros_plugin_without_yaml_then_isolate(tmp_path):
    # Fake pytest11 ROS plugin reproduces the exact startup failure without ROS.
    site = tmp_path / 'ros_site_packages'
    site.mkdir()
    (site / 'fake_launch_testing.py').write_text(
        "raise ModuleNotFoundError(\"No module named 'yaml'\")\n",
        encoding='utf-8',
    )
    dist = site / 'axia_ros_pytest_fixture-1.0.dist-info'
    dist.mkdir()
    (dist / 'METADATA').write_text(
        'Metadata-Version: 2.1\nName: axia-ros-pytest-fixture\nVersion: 1.0\n',
        encoding='utf-8',
    )
    (dist / 'entry_points.txt').write_text(
        '[pytest11]\naxia_fake_ros = fake_launch_testing\n',
        encoding='utf-8',
    )
    case = tmp_path / 'test_dummy.py'
    case.write_text('def test_ok():\n    assert 1 == 1\n', encoding='utf-8')
    env = os.environ.copy()
    env.pop('PYTEST_DISABLE_PLUGIN_AUTOLOAD', None)
    env.pop('PYTEST_PLUGINS', None)
    env.pop('PYTEST_ADDOPTS', None)
    env['PYTHONPATH'] = str(site)
    command = [sys.executable, '-m', 'pytest', '-q', str(case)]
    red = subprocess.run(command, cwd=tmp_path, env=env,
                         capture_output=True, text=True, timeout=20)
    assert red.returncode != 0
    assert "No module named 'yaml'" in (red.stdout + red.stderr)
    env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    green = subprocess.run(command, cwd=tmp_path, env=env,
                           capture_output=True, text=True, timeout=20)
    assert green.returncode == 0, green.stdout + green.stderr
    assert '1 passed' in green.stdout

def test_owner_script_syntax_and_isolated_teacher_invocation():
    assert WRAPPER.is_file(), 'Owner WSL2 script must be committed for reproducibility'
    content = WRAPPER.read_text(encoding='utf-8')
    assert 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1' in content
    assert 'env -u PYTHONPATH' in content
    assert 'pytest==8.3.5' in content
    assert 'training/block_B/tests/test_d08_integration.py' in content
    assert 'training/block_B/instructor/hidden_tests/test_d08_integration_hidden.py' in content
    assert '79a201ca6f7c5f02beee26f225706c76a23f7ae1' in content
    check = subprocess.run(['bash', '-n', str(WRAPPER)], capture_output=True, text=True)
    assert check.returncode == 0, check.stderr
    static = subprocess.run(['bash', str(WRAPPER), '--self-check'],
                            capture_output=True, text=True, timeout=10)
    assert static.returncode == 0, static.stderr
    assert 'D08_OWNER_WRAPPER_STATIC_PASS' in static.stdout
