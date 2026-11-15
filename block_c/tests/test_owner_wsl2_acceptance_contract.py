"""Public RED-first validation of a private-source-safe Owner WSL2 acceptance entrypoint.

CI does NOT checkout private Instructor files or claim an actual WSL2 result.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'block_c' / 'scripts' / 'axia_block_c_owner_final_once.sh'


def test_owner_runner_exists_and_is_shell_valid():
    assert RUNNER.is_file(), 'C_BLOCK_OWNER_ONE_SHOT_MISSING'
    p = subprocess.run(['bash', '-n', str(RUNNER)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr


def test_pinned_three_sources_and_public_ci_evidence():
    content = RUNNER.read_text()
    for expected in (
        '961b574e7623eede6ae94bf7b9cf06e62dc3674a',
        'dff7b4a2710525a72287f5416b7b613a9d979f1e',
        '18631cf070b4c2afb994aa49013fee69224d2aa1',
        '43716783675', '43720178979', '43725720019',
    ):
        assert expected in content


def test_no_private_repo_checkout_or_secret_exposure_during_public_ci():
    content = RUNNER.read_text()
    assert '--self-check' in content
    assert 'WSL2_REQUIRED' in content
    assert 'silverbjin/axia-robot-safety-instructor' in content
    assert 'GH_TOKEN=' not in content
    assert 'github_pat_' not in content
    assert 'git push' not in content
    assert 'git merge' not in content
    assert 'pkill' not in content
    assert 'wsl --shutdown' not in content
    assert 'git reset --hard' not in content
    assert 'cmd_vel' in content  # deliberate non-control proof


def test_release_is_not_automatically_approved():
    src = RUNNER.read_text()
    assert "'release_approved': False" in src
    assert 'READY_FOR_OWNER_APPROVAL' in src
    assert 'BLOCK_C_RELEASE_APPROVED=false' in src
    assert 'BLOCK_C_OWNER_ACCEPTED=HOLD' in src
    assert 'PRODUCTION_GUARD_TTL_NOT_VERIFIED' in src
    assert 'certified_estop' in src


def test_self_check_is_no_network_no_private_read():
    p = subprocess.run(['bash', str(RUNNER), '--self-check'], capture_output=True, text=True, timeout=10)
    assert p.returncode == 0, p.stdout + p.stderr
    assert 'BLOCK_C_OWNER_BOOTSTRAP_SELF_CHECK_PASS' in p.stdout
    assert 'OWNER_WSL2_NOT_RUN' in p.stdout


def test_non_wsl2_fails_closed_and_retains_hold_verdict(tmp_path):
    # Only execute on non-WSL CI or authoring runner; do NOT perform a real acceptance
    # in this public contract test.
    kernel = Path('/proc/sys/kernel/osrelease').read_text().lower()
    if 'microsoft' in kernel or 'wsl' in kernel:
        return
    env = dict(os.environ, AXIA_BLOCK_C_OWNER_ROOT=str(tmp_path / 'owner'))
    p = subprocess.run(['bash', str(RUNNER), '--run'], capture_output=True, text=True, timeout=10, env=env)
    assert p.returncode != 0
    assert 'WSL2_REQUIRED' in p.stdout + p.stderr
    verdicts = list((tmp_path / 'owner').rglob('verdict.json'))
    assert len(verdicts) == 1
    j = json.loads(verdicts[0].read_text())
    assert j['status'] == 'HOLD'
    assert j['release_approved'] is False
    assert j['owner_wsl2_verified'] is False
    assert not (tmp_path / 'owner').joinpath('private').exists()


def test_actual_model_events_reach_ros_and_colcon_cli_is_scoped():
    src = RUNNER.read_text()
    assert 'colcon --log-base ' in src and ' build --base-paths ' in src
    assert '--packages-select axia_block_c_diagnostics' in src
    assert 'day11/autoencoder_pipeline.py' in src
    assert 'day12/events.py' in src
    assert 'model_derived_8.jsonl' in src and 'ros_l1_probe.py' in src
    assert 'C02_C05_MODEL_PIPELINE' in src and 'AE_EVENT_TO_JAZZY_DDS_L1' in src


def test_manifest_hashes_and_bundle_not_gazebo_claim():
    src=RUNNER.read_text()
    assert 'hmac.compare_digest' in src and 'SHA256_MISMATCH' in src
    assert 'AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz' in src
    assert "'production_guard_ttl_verified':False" in src
    assert "'gazebo_actual':False" in src
    assert 'GZ_PARTITION=' not in src


def test_owner_evidence_contains_model_artifacts_and_ros_domain_isolation():
    src=RUNNER.read_text()
    assert 'evidence verdict.json lab' in src
    assert 'AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz.sha256' in src
    assert 'BLOCK_C_OWNER_ISOLATED_ROS_DOMAIN_ID=' in src
    assert 'export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-' not in src
