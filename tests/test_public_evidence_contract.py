from pathlib import Path
import pytest
from axia_public_contracts.evidence import build_manifest, verify_manifest


def test_integrity_round_trip(tmp_path):
    (tmp_path / 'run.log').write_text('public fixture only\n', encoding='utf-8')
    manifest = build_manifest(tmp_path, ['run.log'])
    assert verify_manifest(tmp_path, manifest) == []
    (tmp_path / 'run.log').write_text('mutated', encoding='utf-8')
    assert verify_manifest(tmp_path, manifest) == ['HASH_MISMATCH:run.log']


def test_missing_file_is_fail_closed(tmp_path):
    manifest = {'run.log': '0' * 64}
    assert verify_manifest(tmp_path, manifest) == ['MISSING:run.log']


def test_reject_parent_directory_and_symlink(tmp_path):
    with pytest.raises(ValueError):
        build_manifest(tmp_path, ['../secret'])
    outside = tmp_path.parent / 'separate.txt'
    outside.write_text('not public', encoding='utf-8')
    (tmp_path / 'link').symlink_to(outside)
    with pytest.raises(ValueError):
        build_manifest(tmp_path, ['link'])
    outside.unlink()

def test_empty_manifest_must_not_succeed(tmp_path):
    assert verify_manifest(tmp_path, {}) == ['EMPTY_MANIFEST']


def test_empty_build_manifest_rejected(tmp_path):
    with pytest.raises(ValueError, match='empty'):
        build_manifest(tmp_path, [])


def test_required_entries_cannot_be_omitted(tmp_path):
    (tmp_path / 'startup.json').write_text('ready', encoding='utf-8')
    manifest = build_manifest(tmp_path, ['startup.json'])
    assert verify_manifest(tmp_path, manifest, required_files=['startup.json', 'shutdown.json']) == ['MISSING_MANIFEST_ENTRY:shutdown.json']


def test_duplicate_source_paths_rejected(tmp_path):
    (tmp_path / 'same.log').write_text('known', encoding='utf-8')
    with pytest.raises(ValueError, match='duplicate'):
        build_manifest(tmp_path, ['same.log', 'same.log'])


def test_malformed_manifest_not_accepted(tmp_path):
    assert verify_manifest(tmp_path, ['not-a-mapping']) == ['INVALID_MANIFEST']
