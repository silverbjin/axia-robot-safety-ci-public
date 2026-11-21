"""Synthetic first startup timeout; never launch ROS or expose field evidence."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/axia_g07_stabilization_wsl2_final_once.sh'


def run_failure_branch(tmp_path, startup, pregoal=None):
    native = tmp_path / 'native'
    native.mkdir()
    (native / 'startup_verdict.json').write_text(json.dumps(startup))
    if pregoal:
        folder = native / 'g07_ci_pregoal'
        folder.mkdir()
        (folder / 'pregoal_baseline.json').write_text(json.dumps(pregoal))
    source = SCRIPT.read_text()
    begin = source.index("  FIRST_FAILURE='NATIVE_RUNNER_FAILED_REVIEW_RAW'")
    end = source.index('  hold "$FIRST_FAILURE"', begin)
    branch = source[begin:end]
    result = subprocess.run(
        ['bash', '-c', 'set -Eeuo pipefail\nOUT="$1"\n' + branch +
         '\nprintf "%s\\n" "$FIRST_FAILURE"', 'synthetic', str(tmp_path)],
        text=True, capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip().splitlines()[-1]


def timeout_record(manager='LOCALIZATION'):
    detail = 'G07_NATIVE_LIFECYCLE_STARTUP_SERVICE_TIMEOUT:request_sent=True'
    return {'status': 'BLOCKED', 'goal_sent': False,
            'failed_gate': manager + '_START: ' + detail,
            'stages': [{'gate': manager + '_START', 'status': 'BLOCKED',
                        'detail': detail}]}


def test_first_localization_timeout_survives_later_bag_failure(tmp_path):
    assert run_failure_branch(tmp_path, timeout_record()) == \
        'OWNER_STARTUP_LOCALIZATION_SERVICE_TIMEOUT'


def test_first_navigation_timeout_is_distinct(tmp_path):
    assert run_failure_branch(tmp_path, timeout_record('NAVIGATION')) == \
        'OWNER_STARTUP_NAVIGATION_SERVICE_TIMEOUT'


def test_missing_startup_keeps_original_pregoal_failure(tmp_path):
    assert run_failure_branch(tmp_path, {},
        {'status': 'BLOCKED', 'first_failure': 'OWNER_PREGOAL_SCAN300'}) == \
        'OWNER_PREGOAL_SCAN300'


def test_untrusted_detail_does_not_become_failure_enum(tmp_path):
    record = timeout_record()
    record['stages'][0]['detail'] = '/private/path not an allowed failure'
    assert run_failure_branch(tmp_path, record) == 'NATIVE_RUNNER_FAILED_REVIEW_RAW'


def test_diagnostic_zip_retains_startup_boundary_files():
    source = SCRIPT.read_text()
    for name in ('native/startup_verdict.json',
                 'native/startup_verdict.localization_start.native.json',
                 'native/startup_verdict.navigation_start.native.json'):
        assert repr(name) in source
