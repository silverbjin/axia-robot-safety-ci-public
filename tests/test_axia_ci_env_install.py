"""Only whitelisted exact-version apt specs may be proposed in container CI."""
from pathlib import Path
import importlib.util
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from axia_ci_env_compare import SCHEMA, MIN_REQUIRED
from axia_ci_env_install import selected_versions, make_plan


def sample():
    pkgs={p:'1.2.3-1noble' for p in MIN_REQUIRED}
    pkgs['ros-jazzy-ros-gz']='2.3.0-1noble'
    pkgs['ros-jazzy-rclpy']='7.0.0-1noble'
    return {
        'schema': SCHEMA, 'profile_kind':'wsl2_owner', 'wsl2_detected':True,
        'os':{'id':'ubuntu','version_id':'24.04'},
        'ros':{'distro':'jazzy'}, 'apt_packages':pkgs,
    }


def test_proposed_packages_are_core_only():
    x=sample();x['apt_packages']['other-host-package']='2.0'
    specs=selected_versions(x)
    assert 'other-host-package' not in specs
    assert 'ros-jazzy-nav2-bringup' in specs


def test_wrong_ubuntu_or_missing_owner_core_blocks():
    x=sample();x['os']['version_id']='22.04'
    with pytest.raises(ValueError, match='WRONG_OWNER_OS_OR_ROS'):
        selected_versions(x)
    x=sample();x['apt_packages'].pop(MIN_REQUIRED[0])
    with pytest.raises(ValueError,match='OWNER_MISSING_REQUIRED'):
        selected_versions(x)


def test_no_command_injection_as_package_version():
    x=sample();x['apt_packages']['ros-jazzy-ros-gz']='1;touch /tmp/axia_bad'
    with pytest.raises(ValueError,match='UNSAFE_APT'):
        selected_versions(x)


def test_unavailable_pin_never_silently_uses_latest(monkeypatch):
    import axia_ci_env_install as mod
    monkeypatch.setattr(mod,'installed_version',lambda name: '0.0')
    monkeypatch.setattr(mod,'available_versions',lambda name:set())
    plan=make_plan(sample())
    assert plan['status']=='VERSION_UNAVAILABLE'
    assert plan['exact_install_specs']==[]
    assert plan['unavailable_versions']
    assert plan['gazebo_goal_verified'] is False


def test_exact_versions_collected_not_downgraded_without_apply(monkeypatch):
    import axia_ci_env_install as mod
    monkeypatch.setattr(mod,'installed_version',lambda name: '0.0')
    monkeypatch.setattr(mod,'available_versions',lambda name:{'1.2.3-1noble','2.3.0-1noble','7.0.0-1noble'})
    plan=make_plan(sample())
    assert plan['status']=='READY_TO_PIN'
    assert 'ros-jazzy-ros-gz=2.3.0-1noble' in plan['exact_install_specs']
    assert plan['wsl2_kernel_parity'] is False
