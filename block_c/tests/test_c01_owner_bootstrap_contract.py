"""RED then GREEN: public Owner WSL2 bootstrap is pinned, no motion or private code."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'axia_c01_owner_wsl2_once.sh'
SOURCE_SHA = '766ef987fc0357fdf171fa0926dbef65c6aae972'


def test_bootstrap_exists_and_static_self_check():
    assert SCRIPT.is_file(), 'C01_OWNER_BOOTSTRAP_NOT_PUBLISHED'
    p = subprocess.run(['bash', '-n', str(SCRIPT)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    p = subprocess.run(['bash', str(SCRIPT), '--self-check'], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    assert 'C01_BOOTSTRAP_SELF_CHECK_PASS' in p.stdout


def test_bootstrap_pins_exact_verified_student_commit():
    src = SCRIPT.read_text()
    assert SOURCE_SHA in src
    assert 'rev-parse HEAD' in src
    assert 'C01_SOURCE_SHA_MISMATCH' in src
    assert 'block_C/scripts/c01_fixture_once.sh' in src
    for unsafe in ('pkill', 'sudo ', '/cmd_vel', 'ros2 action send_goal', 'git reset --hard'):
        assert unsafe not in src


def test_ci_runs_same_clone_path_as_owner_wsl2():
    workflow = (ROOT.parent / '.github' / 'workflows' / 'block-c-c01-l0.yml').read_text()
    assert 'AXIA_C01_SOURCE_DIR=' not in workflow, 'CI must not bypass Owner clone/sha verification path'
    assert 'bash block_c/scripts/axia_c01_owner_wsl2_once.sh --run' in workflow
