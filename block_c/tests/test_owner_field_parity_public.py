"""Public repro of Owner WSL2 manifest false-PASS and absolute-authoring-path failures.

The exact PUBLIC Owner shell runner is used for CI and WSL2. Private instructor
code is never checked out by this CI. A synthetic public test mirror is used.
"""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

CI = Path(__file__).resolve().parents[2]
RUNNER = CI / 'block_c/scripts/axia_block_c_owner_final_once.sh'
STUDENT = Path(os.environ.get('AXIA_BLOCK_C_PUBLIC_STUDENT_ROOT', '/nonexistent')) / 'block_C'
C01 = ('generator.py', 'normal_train.csv', 'normal_valid.csv', 'test_mixed.csv',
       'schema.json', 'scenario_manifest.json', 'PROVENANCE.md', 'SHA256SUMS')
C05 = ('event_contract.py', 'ros_diagnostic_bridge.py', 'ros_l1_probe.py', 'sample_events.jsonl')


@pytest.fixture()
def pair(tmp_path):
    assert STUDENT.joinpath('release/PUBLIC_STUDENT_MANIFEST.json').is_file(), STUDENT
    teacher = tmp_path / 'teacher'
    (teacher / 'release').mkdir(parents=True)
    shutil.copytree(STUDENT / 'fixtures', teacher / 'fixtures')
    shutil.copytree(STUDENT / 'day12/ros_transport', teacher / 'day12/shared')
    (teacher / 'tests').mkdir()
    (teacher / 'tests/test_if.py').write_text("from pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\nFEATURES=ROOT/'day09'/'reference_outputs'\n")
    files = [*(f'fixtures/{x}' for x in C01),
             *(f'day12/shared/{x}' for x in C05), 'tests/test_if.py']
    hashes = {f: hashlib.sha256((teacher/f).read_bytes()).hexdigest() for f in files}
    manifest = {
        'release_approved': False, 'owner_wsl2_verified': False,
        'control_authority': False, 'certified_estop': False,
        'data_source': 'SYNTHETIC_COURSE_FIXTURE', 'file_sha256': hashes,
    }
    (teacher / 'release/RELEASE_MANIFEST.json').write_text(json.dumps(manifest)+'\n')
    return teacher, STUDENT, tmp_path


def exercise(pair):
    teacher, student, base = pair
    env = os.environ.copy()
    env.update({
        'AXIA_BLOCK_C_CI_TEACHER_DIR': str(teacher),
        'AXIA_BLOCK_C_CI_STUDENT_DIR': str(student),
        'AXIA_BLOCK_C_OWNER_ROOT': str(base / 'runs'),
    })
    proc = subprocess.run(['bash', str(RUNNER), '--ci-parity'],
                          text=True, capture_output=True, env=env, timeout=30)
    runs = list((base/'runs').glob('run-*/verdict.json'))
    assert len(runs) == 1, [r.as_posix() for r in runs]
    report = json.loads(runs[0].read_text())
    status = (runs[0].parent/'evidence/stage_status.tsv').read_text()
    return proc, report, status


def test_public_ci_uses_exact_owner_runner_with_same_integrity_function(pair):
    p, v, stages = exercise(pair)
    assert p.returncode == 0, p.stdout + p.stderr
    assert 'BLOCK_C_STAGE_PASS=MANIFEST_SHA_AND_PARITY' in p.stdout
    assert 'BLOCK_C_CI_MANIFEST_PARITY_PASS_NO_WSL2' in p.stdout
    assert 'MANIFEST_SHA_AND_PARITY\tPASS' in stages
    # Public CI cannot assert Owner WSL2 acceptance by executing a fixture.
    assert v['status'] == 'HOLD' and v['owner_wsl2_verified'] is False
    assert v['release_approved'] is False


def test_corrupted_manifest_sha_fails_closed_not_false_pass(pair):
    teacher = pair[0]
    p = teacher/'release/RELEASE_MANIFEST.json'
    manifest = json.loads(p.read_text())
    manifest['file_sha256']['tests/test_if.py'] = '0'*64
    p.write_text(json.dumps(manifest)+'\n')
    proc, verdict, stages = exercise(pair)
    assert proc.returncode != 0
    assert 'BLOCK_C_STAGE_HOLD=MANIFEST_SHA_AND_PARITY' in proc.stderr
    assert 'MANIFEST_SHA_AND_PARITY\tPASS' not in stages
    assert 'MANIFEST_SHA_AND_PARITY\tHOLD_RC_' in stages
    assert verdict['release_approved'] is False
    assert verdict['stage_results']['MANIFEST_SHA_AND_PARITY'].startswith('HOLD_RC_')


def test_changed_file_without_manifest_rehash_fails_closed(pair):
    teacher = pair[0]
    (teacher/'tests/test_if.py').write_text("FEATURES=Path('/mnt/data/old-authoring-only')\n")
    proc, _, stages = exercise(pair)
    assert proc.returncode != 0
    assert 'MANIFEST_SHA_AND_PARITY\tPASS' not in stages


def test_malicious_manifest_path_fails_closed(pair):
    teacher = pair[0]
    p = teacher/'release/RELEASE_MANIFEST.json'
    m = json.loads(p.read_text())
    m['file_sha256']['../outside.txt'] = 'a'*64
    p.write_text(json.dumps(m)+'\n')
    proc, _, stages = exercise(pair)
    assert proc.returncode != 0
    assert 'MANIFEST_SHA_AND_PARITY\tPASS' not in stages


def test_authoring_absolute_path_is_rejected_even_with_matching_sha(pair):
    teacher = pair[0]
    f = teacher/'tests/test_if.py'
    f.write_text("from pathlib import Path\nFEATURES=Path('/mnt/data/axia_block_c_delivery/results/c02')\n")
    mpath = teacher/'release/RELEASE_MANIFEST.json'
    m = json.loads(mpath.read_text())
    m['file_sha256']['tests/test_if.py'] = hashlib.sha256(f.read_bytes()).hexdigest()
    mpath.write_text(json.dumps(m)+'\n')
    proc, _, stages = exercise(pair)
    assert proc.returncode != 0
    assert 'AUTHORING_ABSOLUTE_PATH' in (proc.stdout + proc.stderr)
    assert 'MANIFEST_SHA_AND_PARITY\tPASS' not in stages


def test_missing_tracked_file_fails_closed(pair):
    (pair[0]/'tests/test_if.py').unlink()
    proc, _, stages = exercise(pair)
    assert proc.returncode != 0
    assert 'MANIFEST_SHA_AND_PARITY\tPASS' not in stages


def test_no_private_repo_token_or_motion_command_in_public_runner():
    text = RUNNER.read_text()
    assert 'INSTRUCTOR_SHA=961b574e7623eede6ae94bf7b9cf06e62dc3674a' not in text
    assert 'INSTRUCTOR_SHA=eb91a334ab8ad826eb863afbb56a55f0b4991a53' in text
    for unsafe in ('git push', 'git reset --hard', 'ros2 action send_goal', 'wsl --shutdown', 'pkill -9'):
        assert unsafe not in text
    assert '--ci-parity' in text and '--run' in text


def test_owner_stage_python_failures_checked_without_errexit_side_effects():
    source = RUNNER.read_text()
    assert "<<'PY' || return $?" in source  # manifest Python integrity check
    assert 'BLOCK_C_STAGE_HOLD=MANIFEST_SHA_AND_PARITY' not in source  # generic run_step records it
    assert 'run_step MANIFEST_SHA_AND_PARITY check_manifests_and_source_parity' in source
