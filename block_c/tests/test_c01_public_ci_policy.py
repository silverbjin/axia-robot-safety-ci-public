"""C-01 public-only acceptance contract: no private source/hidden tests in CI."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / 'docs' / 'AXIA_PUBLIC_CI_VERIFICATION_POLICY_20261115_KO.md'
WORKFLOW = ROOT / '.github' / 'workflows' / 'block-c-c01-l0.yml'
RUNNER = ROOT / 'block_c' / 'scripts' / 'axia_c01_owner_wsl2_once.sh'
PIN = '766ef987fc0357fdf171fa0926dbef65c6aae972'


def test_policy_exists_and_scopes_acceptance():
    text = POLICY.read_text(encoding='utf-8')
    for marker in ('PUBLIC_CI_ONLY', 'PRIVATE_CI_NOT_RELEASE_GATE',
                   'NO_PRIVATE_CHECKOUT', 'OWNER_WSL2_NOT_VERIFIED',
                   'APPROVED_BASELINE_UNCHANGED', 'NO_MAIN_MERGE_WITHOUT_APPROVAL'):
        assert marker in text, marker
    assert 'G07' in text and 'TTL' in text


def test_c01_public_ci_pins_public_source_and_executes_owner_path():
    wf = WORKFLOW.read_text(encoding='utf-8')
    src = RUNNER.read_text(encoding='utf-8')
    assert PIN in src
    assert 'git clone' in src and 'rev-parse HEAD' in src
    assert 'bash block_c/scripts/axia_c01_owner_wsl2_once.sh --run' in wf
    assert 'test_c01_public_ci_policy.py' in wf
    for content in (wf, src):
        for forbidden in ('axia-robot-safety-instructor.git',
                          'repository: silverbjin/axia-robot-safety-instructor',
                          'hidden_tests/test_c01_hidden.py',
                          'AXIA_CLOUD_CI', '/cmd_vel', 'ros2 action send_goal'):
            assert forbidden not in content, forbidden


def test_public_owner_runner_static_no_motion():
    assert subprocess.run(['bash','-n',str(RUNNER)], capture_output=True).returncode == 0
    got = subprocess.run(['bash',str(RUNNER),'--self-check'],capture_output=True,text=True)
    assert got.returncode == 0
    assert 'NO_ROS_NO_GOAL' in got.stdout
