"""G07 Owner bootstrap fail-closed contracts. No Goal or Fault in CI."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "axia_p2_g07_owner_l3_once.sh"
PIN = "1216d8589b2a8ac4c7e75aedaa7854eb7b2470b3"
BRANCH = "integration/p1-p2-mvp-shell-consent-20261110"


def run(*args):
    return subprocess.run(["bash", str(WRAPPER), *args],
                          input="", text=True, capture_output=True, timeout=8)


def test_wrapper_exists_and_shell_syntax():
    assert WRAPPER.is_file(), "RED: verified L2 G07-only public bootstrap missing"
    subprocess.run(["bash", "-n", str(WRAPPER)], check=True, timeout=8)


def test_self_check_pin_and_no_owner_execution():
    response = run("--self-check")
    assert response.returncode == 0, response.stderr
    assert PIN in response.stdout
    assert "L3_NOT_RUN" in response.stdout
    assert "G07" in response.stdout


def test_fail_closed_on_unknown_cases_and_arguments():
    for args in (("--case", "G05"), ("--case", "G06"), ("--case", "G07"),
                 ("--all",), ("--self-check", "G07")):
        assert run(*args).returncode != 0, args


def test_owner_tty_required_before_private_clone():
    response = run()
    assert response.returncode != 0
    assert "TTY" in response.stderr
    assert "Cloning into" not in response.stdout + response.stderr


def test_sha_tty_and_owner_consent_contract_preserved():
    data = WRAPPER.read_text()
    assert "readonly SHA='" + PIN + "'" in data
    assert "readonly BRANCH='" + BRANCH + "'" in data
    for required in ("gh auth status", "git -C", "rev-parse HEAD",
                     "status --porcelain", "AXIA_P2_OWNER_PINNED_SHA",
                     "scripts/p2_owner_l3_wsl2.sh", "--case G07", "/dev/tty"):
        assert required in data
    assert "yes |" not in data.lower()
    assert "echo YES-" not in data
    assert "main" not in data.split("readonly BRANCH=")[1].split("\n", 1)[0]
