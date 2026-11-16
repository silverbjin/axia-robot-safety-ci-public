#!/usr/bin/env python3
"""Public-only, stdlib evidence custody/consistency audit for Block C Owner WSL2.

Does NOT execute ROS, Trainer/instructor code, or approve a release. The same
exact script can be run by public CI synthetic regression and locally against
an Owner evidence archive. Never publish actual private Owner archives to CI.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

STAGES = (
    'WSL2_GATE', 'TOOLS_AND_JAZZY', 'PUBLIC_CI_PROVENANCE',
    'EXACT_REPO_CHECKOUT', 'MANIFEST_SHA_AND_PARITY',
    'PYTHON312_PINNED_DEPENDENCIES', 'INSTRUCTOR_PYTHON_L0',
    'STUDENT_PYTHON_L0', 'STUDENT_EXPECTED_RED',
    'C02_C05_MODEL_PIPELINE', 'JAZZY_COLCON_PACKAGE_BUILD',
    'INSTRUCTOR_STUDENT_JAZZY_L1', 'AE_EVENT_TO_JAZZY_DDS_L1',
)
DDS_PATHS = (
    'evidence/instructor_ros_l1/ros_l1',
    'evidence/student_ros_l1/ros_l1',
    'evidence/model_to_ros_l1',
)
EXPECTED_SHAS = {
    'instructor_source_sha': 'eb91a334ab8ad826eb863afbb56a55f0b4991a53',
    'student_source_sha': 'dff7b4a2710525a72287f5416b7b613a9d979f1e',
    'public_ci_source_sha': '18631cf070b4c2afb994aa49013fee69224d2aa1',
}

class AuditFailure(ValueError):
    pass

def require(condition, reason):
    if not condition:
        raise AuditFailure(reason)

def _junit_count(contents):
    root = ET.fromstring(contents)
    suites = list(root.iter('testsuite'))
    require(bool(suites), 'JUNIT_NO_TESTSUITE')
    return {
        key: sum(int(suite.attrib.get(key, '0')) for suite in suites)
        for key in ('tests', 'failures', 'errors', 'skipped')
    }

def audit(archive: Path, checksum_file: Path):
    archive, checksum_file = Path(archive), Path(checksum_file)
    require(archive.is_file() and checksum_file.is_file(), 'ARCHIVE_OR_CHECKSUM_MISSING')
    required = re.fullmatch(
        r'([0-9a-f]{64})\s+\*?(AXIA_BLOCK_C_OWNER_EVIDENCE\.tar\.gz)',
        checksum_file.read_text(encoding='utf-8').strip(),
    )
    require(required is not None, 'CHECKSUM_FORMAT_OR_ORIGINAL_NAME_MISMATCH')
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    require(actual == required.group(1), 'EVIDENCE_ARCHIVE_SHA256_MISMATCH')
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        require(len(members) >= 27 and len(members) <= 500, 'EVIDENCE_ARCHIVE_MEMBER_COUNT_INVALID')
        require(sum(item.size for item in members) < 100_000_000, 'EVIDENCE_ARCHIVE_UNBOUNDED')
        names = [item.name.rstrip('/') for item in members]
        require(len(set(names)) == len(names), 'EVIDENCE_ARCHIVE_DUPLICATE_MEMBERS')
        for m in members:
            path = PurePosixPath(m.name)
            require(not path.is_absolute() and '..' not in path.parts and
                    (m.isfile() or m.isdir()), 'EVIDENCE_ARCHIVE_UNSAFE_MEMBER')
        by_name = {item.name.rstrip('/'): item for item in members}
        def read(name):
            item = by_name.get(name)
            require(item is not None and item.isfile(), 'EVIDENCE_MISSING_FILE:'+name)
            require(item.size < 10_000_000, 'EVIDENCE_FILE_TOO_LARGE:'+name)
            stream = tar.extractfile(item)
            require(stream is not None, 'EVIDENCE_UNREADABLE:'+name)
            return stream.read()
        def obj(name):
            return json.loads(read(name))
        verdict = obj('verdict.json')
        require(verdict.get('profile') == 'BLOCK_C_EDUCATION_MVP_D09_D12', 'VERDICT_PROFILE_MISMATCH')
        require(verdict.get('status') == 'READY_FOR_OWNER_APPROVAL' and
                verdict.get('release_decision') == 'OWNER_APPROVAL_REQUIRED' and
                verdict.get('exit_code') == 0, 'VERDICT_NOT_TECHNICALLY_ACCEPTED')
        require(verdict.get('owner_wsl2_verified') is True and
                verdict.get('release_approved') is False and
                verdict.get('main_merged') is False, 'VERDICT_RELEASE_BOUNDARY_VIOLATED')
        require(verdict.get('safety_control_authority') is False and
                verdict.get('certified_estop') is False and
                verdict.get('gazebo_actual') is False and
                verdict.get('production_guard_ttl_verified') is False,
                'VERDICT_SCOPE_OVERCLAIM')
        require(all(verdict.get(k) == v for k,v in EXPECTED_SHAS.items()),
                'VERDICT_PIN_MISMATCH')
        require(verdict.get('last_stage') == STAGES[-1], 'VERDICT_LAST_STAGE_MISMATCH')
        stage_lines = read('evidence/stage_status.tsv').decode('utf-8').splitlines()
        require(stage_lines == ['stage\tresult'] + [x+'\tPASS' for x in STAGES],
                'STAGES_NOT_ALL_PASS_IN_ORDER')
        require(verdict.get('stage_results') == {stage:'PASS' for stage in STAGES},
                'VERDICT_STAGE_RESULTS_INCONSISTENT')
        # A traceback in a PASS stage log used to be silently ignored by Bash.
        # Dependency probing and intentional TODO RED are the two documented exceptions.
        for stage in STAGES:
            data = read(f'evidence/{stage}.log').decode('utf-8',errors='replace')
            if stage not in ('PYTHON312_PINNED_DEPENDENCIES', 'STUDENT_EXPECTED_RED'):
                require(not re.search(r'(?m)^(Traceback \(most recent call last\):|AssertionError:|FileNotFoundError:)',data),
                        'STAGE_LOG_CONTAINS_UNREPORTED_FAILURE:'+stage)
        i = _junit_count(read('evidence/instructor_unit/pytest.xml'))
        s = _junit_count(read('evidence/student_unit/pytest.xml'))
        require(i == {'tests':32,'failures':0,'errors':0,'skipped':0}, 'INSTRUCTOR_JUNIT_FAILURE_OR_COUNT_MISMATCH')
        require(s == {'tests':5,'failures':0,'errors':0,'skipped':0}, 'STUDENT_JUNIT_FAILURE_OR_COUNT_MISMATCH')
        red = read('evidence/student_todo_expected_red.log').decode('utf-8',errors='replace')
        require(len(re.findall(r'(?m)^FAILED ',red)) == 4 and re.search(r'(?m)^4 failed in ',red),
                'STUDENT_TODO_NOT_EXACTLY_FOUR_EXPECTED_RED')
        dependency = read('evidence/PYTHON312_PINNED_DEPENDENCIES.log').decode('utf-8',errors='replace')
        require('BLOCK_C_DEPENDENCY_PINS_PASS' in dependency and
                '"torch": "2.10.0+cpu"' in dependency and
                '"python"' in dependency and '3.12.' in dependency,
                'DEPENDENCY_PINS_NOT_VERIFIED')
        build = read('evidence/JAZZY_COLCON_PACKAGE_BUILD.log').decode('utf-8',errors='replace')
        require('BLOCK_C_OWNER_COLCON_JAZZY_BUILD_PASS' in build and
                '1 package finished' in build, 'COLCON_NOT_VERIFIED')
        pipeline = read('evidence/C02_C05_MODEL_PIPELINE.log').decode('utf-8',errors='replace')
        require('BLOCK_C_PIPELINE_L0_PASS windows=424 valid_test=100 invalid_test=4 events=104' in pipeline,
                'PIPELINE_SUMMARY_NOT_VERIFIED')
        for name in ('lab/c03/if_metrics.json','lab/c04/ae_metrics.json'):
            v = obj(name)
            require(v.get('source') == 'SYNTHETIC_COURSE_FIXTURE' and
                    v.get('test_invalid_count') == 4 and
                    v.get('fit_on_test') is False and
                    v.get('test_threshold_tuned') is False and
                    sum(v.get('confusion',{}).values()) == 100,
                    'MODEL_METRICS_SCOPE_MISMATCH:'+name)
        events = [json.loads(row) for row in read('lab/c05/anomaly_events.jsonl').decode().splitlines() if row]
        require(len(events) == 104 and sum(x['level']=='INSUFFICIENT_DATA' for x in events)==4 and
                all(x['control_authority'] is False and x['certified_estop'] is False for x in events),
                'ANOMALY_EVENT_CONTRACT_FAILURE')
        timing = {}
        for prefix in DDS_PATHS:
            d = obj(prefix+'/verdict.json')
            rows = obj(prefix+'/samples.json')
            require(d.get('status') == 'PASS_REAL_ROS_L1_EDUCATION_ONLY' and
                    d.get('ros_actual') is True and d.get('gazebo_actual') is False and
                    d.get('production_guard_ttl_verified') is False and
                    d.get('goal_sent') is False and d.get('cmd_vel_published') is False and
                    d.get('sample_count') == d.get('expected_count') == len(rows) == 8 and
                    d.get('pub_rc') == 0 and d.get('levels') == [0,1,2,3],
                    'DDS_VERDICT_NOT_PASS:'+prefix)
            counts = d.get('cmd_vel_publisher_count',{})
            require(set(counts) == {'/cmd_vel','/cmd_vel_smoothed','/cmd_vel_supervised','/cmd_vel_raw'} and
                    all(x==0 for x in counts.values()),
                    'DDS_CONTROL_PUBLISHER_DETECTED:'+prefix)
            mn,mx=d.get('period_min_ms'),d.get('period_max_ms')
            require(isinstance(mn,(float,int)) and isinstance(mx,(float,int)) and
                    20<=mn<=mx<=600 and d.get('period_target_ms')==100,
                    'DDS_TIMING_BOUNDARY_VIOLATION:'+prefix)
            require({v['level'] for v in rows} == {0,1,2,3} and all(
                'EDUCATION ONLY' in v['message'] and
                v['keys']['control_authority']=='False' and
                v['keys']['certified_estop']=='False' for v in rows),
                'DDS_RECEIVED_CONTENT_INCONSISTENT:'+prefix)
            if prefix=='evidence/model_to_ros_l1':
                require(all(v['keys'].get('model_id')=='CPU_TORCH_AE' for v in rows),
                        'MODEL_TO_DDS_SOURCE_NOT_ACTUAL_AE')
            timing[{'evidence/instructor_ros_l1/ros_l1':'instructor','evidence/student_ros_l1/ros_l1':'student','evidence/model_to_ros_l1':'model_to_ros'}[prefix]]={'min_ms':mn,'max_ms':mx}
        # Nonfatal installation/setup signals are *reported*, not suppressed or called failures.
        notices = []
        for label,pattern in (
            ('existing_os_site_package_not_uninstalled', r"Not uninstalling .*outside environment"),
            ('system_pybind11_invalid_metadata', r'WARNING: Skipping .*pybind11.*invalid metadata'),
            ('pip_resolver_conflict_outside_course_scope', r"ERROR: pip's dependency resolver"),
            ('torch_initial_probe_missing_before_install', r"ModuleNotFoundError: No module named 'torch'"),
        ):
            if re.search(pattern,dependency):notices.append(label)
        if 'byte-compiling is disabled' in build:
            notices.append('colcon_setuptools_bytecompile_disabled')
        return {'audit':'PASS_SCOPED_OWNER_EDUCATION_MVP',
                'archive_sha256':actual, 'owner_wsl2_verified':True,
                'release_approved':False, 'main_merged':False,
                'instructor_tests':i['tests'],'student_tests':s['tests'],
                'student_todo_expected_red':4, 'steps_verified':len(STAGES),
                'dds':timing,'environment_notices':notices,
                'gazebo_actual':False,'production_guard_ttl_verified':False,
                'certified_estop':False}

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--checksum-file',type=Path,required=True)
    p.add_argument('--out',type=Path)
    args=p.parse_args(argv)
    try:
        result=audit(args.archive,args.checksum_file)
    except (AuditFailure,ValueError,OSError,tarfile.TarError,ET.ParseError,KeyError,TypeError) as exc:
        print(f'BLOCK_C_EVIDENCE_AUDIT=HOLD reason={str(exc)}',file=sys.stderr)
        return 1
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('BLOCK_C_EVIDENCE_AUDIT=PASS_SCOPED steps=13 instructor_tests=32 student_tests=5 dds_tests=3 release_approved=false')
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
