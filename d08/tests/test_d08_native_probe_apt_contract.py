"""RED: official OSRF Noble Apt source needed for Gazebo Python native bindings.

The original Jazzy ROS container doesn't have these packages indexed.
Only the targeted native-probe CI diagnostic job may add the signed source.
No changes to Owner/AMCL/Gazebo/CM runtime files.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml"

def test_official_gazebo_native_python_apt_source_is_signed_ci_only():
    s=WF.read_text()
    assert "packages.osrfoundation.org/gazebo.gpg" in s
    assert "pkgs-osrf-archive-keyring.gpg" in s
    assert "signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg" in s
    assert "python3-gz-transport13 python3-gz-msgs10" in s
    assert 'if [ "$AXIA_D08_NATIVE_RX_PROBE" = "1" ]; then' in s
    assert "apt-get install gz-harmonic" not in s

def test_do_not_silently_replace_ros_vendor_gazebo_libraries():
    s=WF.read_text()
    assert 'apt-get install -y -qq --no-install-recommends --no-upgrade' in s
    assert "D08_NATIVE_PYTHON_APT_IMPORT_L2_PASS" in s
