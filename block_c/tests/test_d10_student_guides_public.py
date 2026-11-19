"""D10 public student-only source and document contract.

No instructor checkout, private models, hidden tests or safety control path.
"""
from pathlib import Path
import os
import json

STUDENT=Path(os.environ.get('AXIA_D10_STUDENT_ROOT','student'))
SHA='103c956b92434a04acddb6be85809ddaae2431d9'

def test_d10_pinned_public_student_source():
    assert os.environ.get('AXIA_D10_STUDENT_SHA')==SHA

def test_d10_student_guides_exist_and_match_two_goals():
    demo=(STUDENT/'block_C/day10/STUDENT_DEMO_GUIDE_KO.md').read_text(encoding='utf-8')
    lab=(STUDENT/'block_C/day10/STUDENT_LAB_GUIDE_KO.md').read_text(encoding='utf-8')
    readme=(STUDENT/'block_C/day10/README_KO.md').read_text(encoding='utf-8')
    assert 'Isolation Forest 기반 이상신호 탐지 구조 이해' in demo
    assert '정상 패턴 기준 이상탐지 및 조기 경고 검증 실습' in demo
    for marker in ('features_train.csv','features_valid.csv','features_test.csv',
                   'normal_valid_only','INSUFFICIENT_DATA','synthetic_delay_s=1.9',
                   'D10_STUDENT_DATA_CHECK_PASS'):
        assert marker in lab,marker
    assert 'STUDENT_DEMO_GUIDE_KO.md' in readme
    assert 'STUDENT_LAB_GUIDE_KO.md' in readme

def test_d10_reference_contract_and_student_expected_red():
    manifest=json.loads((STUDENT/'block_C/fixtures/scenario_manifest.json').read_text(encoding='utf-8'))
    assert manifest['expected_rows']=={'normal_train.csv':2400,'normal_valid.csv':800,'test_mixed.csv':1399}
    assert sum(manifest['trace_counts'].values())==46
    assert manifest['seed']==2409
    source=(STUDENT/'block_C/day10/student_if_todo.py').read_text(encoding='utf-8')
    assert 'raise NotImplementedError' in source and 'IsolationForest(' not in source

def test_d10_no_private_solution_or_safety_action_published():
    root=STUDENT/'block_C'
    paths=[str(p.relative_to(root)).lower() for p in root.rglob('*') if p.is_file()]
    assert not any(word in p for p in paths for word in ('hidden_tests','teacher_solution','instructor/','ae_checkpoint.pt','.env'))
    for name in ('STUDENT_DEMO_GUIDE_KO.md','STUDENT_LAB_GUIDE_KO.md'):
        s=(root/'day10'/name).read_text(encoding='utf-8')
        assert 'from isolation_forest_pipeline import' not in s
        assert 'create_publisher(' not in s and 'send_goal_async(' not in s
        assert 'SYNTHETIC_COURSE_FIXTURE' in s or '합성' in s
