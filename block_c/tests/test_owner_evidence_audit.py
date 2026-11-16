"""Public synthetic evidence fixtures: real Owner private artifacts stay OFF public CI."""
from __future__ import annotations
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AUDITOR = ROOT / 'block_c/scripts/axia_block_c_evidence_audit.py'
STAGES = (
    'WSL2_GATE','TOOLS_AND_JAZZY','PUBLIC_CI_PROVENANCE','EXACT_REPO_CHECKOUT',
    'MANIFEST_SHA_AND_PARITY','PYTHON312_PINNED_DEPENDENCIES','INSTRUCTOR_PYTHON_L0',
    'STUDENT_PYTHON_L0','STUDENT_EXPECTED_RED','C02_C05_MODEL_PIPELINE',
    'JAZZY_COLCON_PACKAGE_BUILD','INSTRUCTOR_STUDENT_JAZZY_L1','AE_EVENT_TO_JAZZY_DDS_L1',
)
DDS = ('evidence/instructor_ros_l1/ros_l1', 'evidence/student_ros_l1/ros_l1',
       'evidence/model_to_ros_l1')

def enc(x):
    if isinstance(x, bytes):return x
    if isinstance(x, str):return x.encode('utf-8')
    return (json.dumps(x,sort_keys=True)+'\n').encode()

def fixture_data():
    v={'profile':'BLOCK_C_EDUCATION_MVP_D09_D12','status':'READY_FOR_OWNER_APPROVAL',
       'release_decision':'OWNER_APPROVAL_REQUIRED','exit_code':0,'owner_wsl2_verified':True,
       'release_approved':False,'main_merged':False,'safety_control_authority':False,
       'certified_estop':False,'gazebo_actual':False,'production_guard_ttl_verified':False,
       'instructor_source_sha':'eb91a334ab8ad826eb863afbb56a55f0b4991a53',
       'student_source_sha':'dff7b4a2710525a72287f5416b7b613a9d979f1e',
       'public_ci_source_sha':'18631cf070b4c2afb994aa49013fee69224d2aa1',
       'last_stage':STAGES[-1],'stage_results':{name:'PASS' for name in STAGES}}
    files={'verdict.json':enc(v),
           'evidence/stage_status.tsv':enc('stage\tresult\n'+''.join(s+'\tPASS\n' for s in STAGES)),
           'evidence/instructor_unit/pytest.xml':enc('<testsuites><testsuite tests="32" failures="0" errors="0" skipped="0"/></testsuites>'),
           'evidence/student_unit/pytest.xml':enc('<testsuites><testsuite tests="5" failures="0" errors="0" skipped="0"/></testsuites>'),
           'evidence/student_todo_expected_red.log':enc(''.join('FAILED test_todo_'+str(i)+'\n' for i in range(4))+'4 failed in 0.07s\n'),
           'lab/c03/if_metrics.json':enc({'source':'SYNTHETIC_COURSE_FIXTURE','test_invalid_count':4,
                                        'fit_on_test':False,'test_threshold_tuned':False,
                                        'confusion':{'TP':1,'TN':80,'FP':2,'FN':17}}),
           'lab/c04/ae_metrics.json':enc({'source':'SYNTHETIC_COURSE_FIXTURE','test_invalid_count':4,
                                        'fit_on_test':False,'test_threshold_tuned':False,
                                        'confusion':{'TP':18,'TN':78,'FP':4,'FN':0}}),
           'evidence/PYTHON312_PINNED_DEPENDENCIES.log':enc('''ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
Not uninstalling sympy at /usr/lib/python3/dist-packages, outside environment /tmp/fake
WARNING: Skipping /usr/lib/python3.12/dist-packages/pybind11-2.11.1.dist-info due to invalid metadata entry 'name'
ModuleNotFoundError: No module named 'torch'
Successfully installed torch-2.10.0+cpu
BLOCK_C_DEPENDENCY_PINS_PASS {"python": "3.12.3", "torch": "2.10.0+cpu"}
'''),
           'evidence/JAZZY_COLCON_PACKAGE_BUILD.log':enc('''warning: byte-compiling is disabled, skipping.
Summary: 1 package finished [2.24s]
BLOCK_C_OWNER_COLCON_JAZZY_BUILD_PASS
'''),
           'evidence/C02_C05_MODEL_PIPELINE.log':enc('BLOCK_C_PIPELINE_L0_PASS windows=424 valid_test=100 invalid_test=4 events=104\n'),
           'lab/c05/anomaly_events.jsonl':enc(''.join(json.dumps({'level':'INSUFFICIENT_DATA' if i>=100 else 'NORMAL',
                                                       'control_authority':False,'certified_estop':False})+'\n' for i in range(104)))}
    for stage in STAGES:
        files.setdefault(f'evidence/{stage}.log',enc(f'BLOCK_C_STAGE_PASS={stage}\n'))
    for n in DDS:
        d={'status':'PASS_REAL_ROS_L1_EDUCATION_ONLY','ros_actual':True,'gazebo_actual':False,
           'production_guard_ttl_verified':False,'goal_sent':False,'cmd_vel_published':False,
           'sample_count':8,'expected_count':8,'pub_rc':0,'levels':[0,1,2,3],
           'period_min_ms':99.3,'period_max_ms':100.8,'period_target_ms':100,
           'cmd_vel_publisher_count':{'/cmd_vel':0,'/cmd_vel_smoothed':0,'/cmd_vel_supervised':0,'/cmd_vel_raw':0}}
        samples=[{'level':i%4,'message':'EDUCATION ONLY / NON-CERTIFIED',
                  'keys':{'control_authority':'False','certified_estop':'False',
                          'model_id':'CPU_TORCH_AE' if n.endswith('model_to_ros_l1') else 'TRANSPORT_DEMO'}} for i in range(8)]
        files[n+'/verdict.json']=enc(d)
        files[n+'/samples.json']=enc(samples)
    return files

def pack(tmpdir,files):
    archive=tmpdir/'sample.tar.gz'
    with tarfile.open(archive,'w:gz') as t:
        for name,data in sorted(files.items()):
            info=tarfile.TarInfo(name=name)
            info.size=len(data)
            t.addfile(info,io.BytesIO(data))
    chk=tmpdir/'SHA256SUMS'
    chk.write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz\n')
    return archive,chk

def check(tmp_path,files=None):
    assert AUDITOR.is_file(), 'Owner artifact auditor missing — TDD RED until implemented'
    archive,checksum=pack(tmp_path,fixture_data() if files is None else files)
    return subprocess.run([sys.executable,str(AUDITOR),'--archive',str(archive),
                           '--checksum-file',str(checksum)],capture_output=True,text=True,timeout=20)

def test_valid_scoped_owner_evidence_and_warning_classification(tmp_path):
    p=check(tmp_path)
    assert p.returncode==0,p.stderr
    assert 'BLOCK_C_EVIDENCE_AUDIT=PASS_SCOPED' in p.stdout
    assert 'release_approved": false' in p.stdout
    assert 'pip_resolver_conflict_outside_course_scope' in p.stdout
    assert 'colcon_setuptools_bytecompile_disabled' in p.stdout

def test_checksum_corruption_is_blocked(tmp_path):
    files=fixture_data()
    archive,checksum=pack(tmp_path,files)
    checksum.write_text('0'*64+'  AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz\n')
    p=subprocess.run([sys.executable,str(AUDITOR),'--archive',str(archive),
                      '--checksum-file',str(checksum)],capture_output=True,text=True)
    assert p.returncode!=0 and 'EVIDENCE_ARCHIVE_SHA256_MISMATCH' in p.stderr

def test_stage_pass_with_hidden_traceback_is_blocked(tmp_path):
    files=fixture_data()
    files['evidence/MANIFEST_SHA_AND_PARITY.log']=enc('Traceback (most recent call last):\nAssertionError: SHA256_MISMATCH\nBLOCK_C_STAGE_PASS=MANIFEST_SHA_AND_PARITY\n')
    p=check(tmp_path,files)
    assert p.returncode!=0 and 'STAGE_LOG_CONTAINS_UNREPORTED_FAILURE' in p.stderr

def test_disagreeing_stage_verdict_is_blocked(tmp_path):
    files=fixture_data()
    files['evidence/stage_status.tsv']=enc('stage\tresult\n'+''.join(
        s+'\t'+('HOLD_RC_1' if s=='INSTRUCTOR_PYTHON_L0' else 'PASS')+'\n' for s in STAGES))
    p=check(tmp_path,files)
    assert p.returncode!=0 and 'STAGES_NOT_ALL_PASS_IN_ORDER' in p.stderr

def test_control_publisher_or_goal_is_blocked(tmp_path):
    files=fixture_data()
    where=DDS[-1]+'/verdict.json'
    d=json.loads(files[where]);d['cmd_vel_publisher_count']['/cmd_vel']=1
    files[where]=enc(d)
    p=check(tmp_path,files)
    assert p.returncode!=0 and 'DDS_CONTROL_PUBLISHER_DETECTED' in p.stderr

def test_timing_violation_is_blocked(tmp_path):
    files=fixture_data()
    where=DDS[0]+'/verdict.json';v=json.loads(files[where]);v['period_max_ms']=900
    files[where]=enc(v)
    p=check(tmp_path,files)
    assert p.returncode!=0 and 'DDS_TIMING_BOUNDARY_VIOLATION' in p.stderr

def test_student_todo_red_expected_exactly_four(tmp_path):
    files=fixture_data()
    files['evidence/student_todo_expected_red.log']=enc('3 failed in 0.08s\n')
    p=check(tmp_path,files)
    assert p.returncode!=0 and 'STUDENT_TODO_NOT_EXACTLY_FOUR_EXPECTED_RED' in p.stderr

def test_release_true_must_not_be_autopassed(tmp_path):
    files=fixture_data()
    v=json.loads(files['verdict.json']);v['release_approved']=True
    files['verdict.json']=enc(v)
    p=check(tmp_path,files)
    assert p.returncode!=0 and 'VERDICT_RELEASE_BOUNDARY_VIOLATED' in p.stderr

def test_source_not_private_and_owner_runner_unchanged():
    assert AUDITOR.is_file()
    code=AUDITOR.read_text()
    assert 'gh repo clone' not in code and 'ros2 action send_goal' not in code
    owner=ROOT/'block_c/scripts/axia_block_c_owner_final_once.sh'
    assert owner.is_file() and '--ci-parity' in owner.read_text() and '--run' in owner.read_text()
