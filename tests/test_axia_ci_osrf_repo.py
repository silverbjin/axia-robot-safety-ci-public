"""OSRF Gazebo Harmonic APT bootstrap: fail closed, exact official signed repo."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "axia_ci_enable_osrf_gazebo_repo.sh"


def test_osrf_signed_apt_source_ubuntu_noble_only():
    s = SCRIPT.read_text()
    assert "https://packages.osrfoundation.org/gazebo/ubuntu-stable" in s
    assert "https://packages.osrfoundation.org/gazebo.gpg" in s
    assert "signed-by=" in s and "pkgs-osrf-archive-keyring.gpg" in s
    assert 'VERSION_ID' in s and '24.04' in s and 'ubuntu' in s
    assert "apt-get update" in s
    assert "apt-cache madison" in s
    assert "libgz-sim8" in s and "libsdformat14" in s
    assert 'curl -k' not in s and 'apt-key add' not in s
    assert 'trusted=yes' not in s


def test_self_check_has_no_install_side_effects():
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True)
    result = subprocess.run(["bash", str(SCRIPT), "--self-check"],
                            capture_output=True, text=True, timeout=6)
    assert result.returncode == 0, result.stderr
    assert "OSRF_REPO_CONTRACT_OK" in result.stdout
    assert "NO_APT_MUTATION" in result.stdout
