"""Public-only release gate: no instructor checkout and no teacher solution executed."""
import hashlib
import json
import os
from pathlib import Path

import pytest

STUDENT=Path(os.environ.get('AXIA_BLOCK_C_STUDENT_ROOT','student'))
PIN='dff7b4a2710525a72287f5416b7b613a9d979f1e'


def test_c06_standalone_student_manifest_has_no_teacher_code():
    m=json.loads((STUDENT/'block_C/release/PUBLIC_STUDENT_MANIFEST.json').read_text())
    assert m['data_source']=='SYNTHETIC_COURSE_FIXTURE'
    assert m['days']==['D09','D10','D11','D12']
    assert m['student_scaffold_expected_red'] is True
    assert m['private_hidden_tests_included'] is False
    assert m['private_model_weights_included'] is False
    assert m['release_approved'] is False and m['owner_wsl2_verified'] is False
    assert m['control_authority'] is False and m['certified_estop'] is False


def test_c06_student_artifact_sha256_matches_release_manifest():
    m=json.loads((STUDENT/'block_C/release/PUBLIC_STUDENT_MANIFEST.json').read_text())
    assert len(m['file_sha256'])>=10
    for name,digest in m['file_sha256'].items():
        assert '..' not in Path(name).parts and not Path(name).is_absolute()
        fp=STUDENT/'block_C'/name
        assert fp.is_file(),name
        assert hashlib.sha256(fp.read_bytes()).hexdigest()==digest,name


def test_c06_student_todo_not_teacher_source():
    paths=[str(x.relative_to(STUDENT/'block_C')).lower() for x in (STUDENT/'block_C').rglob('*') if x.is_file()]
    assert not any(word in p for p in paths for word in ('hidden_tests','teacher_solution','instructor/','ae_checkpoint.pt','.env'))
    assert all(any(x in p for p in paths) for x in ['student_eda_todo.py','student_if_todo.py','student_ae_todo.py','student_event_todo.py'])


def test_c06_immutable_student_source_ref():
    actual=os.environ.get('AXIA_BLOCK_C_STUDENT_SHA')
    assert actual==PIN
