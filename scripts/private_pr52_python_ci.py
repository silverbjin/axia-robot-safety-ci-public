#!/usr/bin/env python3
"""Sealed exact-SHA P0 + full P1 Python no-motion tests for PR #52.

Never emits private stdout, traceback, source, JUnit, artifacts or secrets.
This is an externally scoped substitute CI, NOT a native private GH check
and NOT Gazebo Goal, Fault, WSL2 acceptance or E-Stop certification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

PIN = 'fdf54edf3286d40c1c6338ec0068cf7f9accfefd'
SCOPES = ('python',)
_SUITES = (
 ('P0_UNIT', [sys.executable,'-m','unittest','discover','-s','tests/p0','-v'],120),
 ('P0_COMPILE',[sys.executable,'-m','compileall','-q','tools','tests',
              'ros2_ws/src/axia_safety_bringup'],45),
 ('P1_UNIT_ALL',[sys.executable,'-m','pytest','-q','tests/unit'],360),
)
_ALLOW_TYPES = {'AssertionError','ImportError','ModuleNotFoundError',
                'AttributeError','TypeError','ValueError','KeyError',
                'SyntaxError','RuntimeError','TimeoutError','SystemExit'}


def junit_failure_fingerprints(path: Path):
    """Constant-length, non-reversible hashes; NEVER raw test names."""
    if not path.is_file():
        return {'junit_valid': False, 'cases':0, 'failures':0,'errors':0,'skipped':0,
                'failure_categories':[]}
    try:
        root=ET.parse(path).getroot()
        testcases=root.findall('.//testcase')
        if not testcases:
            raise ValueError('JUNIT_EMPTY')
        states={'junit_valid':True,'cases':len(testcases),'failures':0,'errors':0,
                'skipped':0,'failure_categories':[]}
        for case in testcases:
            for kind in ('failure','error','skipped'):
                bad=case.find(kind)
                if bad is not None:
                    states[{'failure':'failures','error':'errors','skipped':'skipped'}[kind]]+=1
                    if kind != 'skipped' and len(states['failure_categories'])<12:
                        rawtype=bad.attrib.get('type','').split('.')[-1]
                        label=rawtype if rawtype in _ALLOW_TYPES else 'OTHER'
                        name=(case.attrib.get('classname','')+'::'+case.attrib.get('name',''))
                        digest=hashlib.sha256(name.encode('utf-8')).hexdigest()[:12]
                        states['failure_categories'].append({'kind':kind,'type':label,
                                                               'case_fingerprint':digest})
        return states
    except (ET.ParseError,ValueError,OSError):
        return {'junit_valid':False,'cases':0,'failures':0,'errors':0,'skipped':0,
                'failure_categories':[]}


def run(private_root: Path):
    summary={'status':'BLOCKED','pin_checked':False,'gate_accepted':False,
             'goal_sent':False,'fault_injected':False,'native_private_actions_fixed':False,
             'scope':'P0_AND_ALL_P1_PYTHON_NO_ROS_OR_GAZEBO','stages':[]}
    try:
        root=private_root.resolve(strict=True)
        sha=subprocess.run(['git','rev-parse','HEAD'],cwd=root,check=True,
            capture_output=True,text=True,timeout=10).stdout.strip()
        if sha != PIN:
            raise ValueError('CHECKOUT_SHA_MISMATCH')
        summary['pin_checked']=True
        env=dict(os.environ)
        env['PYTHONPATH']=os.pathsep.join(str(root / x) for x in (
            'ros2_ws/src/axia_safety_supervisor','ros2_ws/src/axia_fault_injector',
            'ros2_ws/src/axia_scenario_verifier','tools',))
        with tempfile.TemporaryDirectory(prefix='axia_pr52_pure_',
                    dir=os.environ.get('RUNNER_TEMP') or None) as temp:
            work=Path(temp)
            all_ok=True
            for stage,base,timeout in _SUITES:
                command=list(base)
                junit=work/(stage+'.xml')
                if stage=='P1_UNIT_ALL':
                    command.append('--junitxml='+str(junit))
                with (work/(stage+'.private.log')).open('wb') as log:
                    try:
                        result=subprocess.run(command,cwd=root,env=env,stdout=log,
                            stderr=subprocess.STDOUT,timeout=timeout,check=False)
                        rc=result.returncode
                    except subprocess.TimeoutExpired:
                        rc=124
                    except OSError:
                        rc=127
                metadata={'stage':stage,'rc_zero':rc==0}
                if stage=='P1_UNIT_ALL':
                    metadata.update(junit_failure_fingerprints(junit))
                    metadata['status']=('PASS' if rc==0 and metadata['junit_valid']
                        and metadata['cases']>0 and metadata['failures']==0
                        and metadata['errors']==0 and metadata['skipped']==0 else 'BLOCKED')
                elif stage=='P0_UNIT':
                    # The original workflow expects unittest discovery and 0 test failure.
                    raw=(work/(stage+'.private.log')).read_text(errors='replace')
                    count=re.findall(r'Ran (\d+) tests? in ',raw)
                    metadata['tests']=int(count[-1]) if count else 0
                    metadata['status']='PASS' if rc==0 and metadata['tests']>0 else 'BLOCKED'
                else:
                    metadata['status']='PASS' if rc==0 else 'BLOCKED'
                all_ok &= metadata['status']=='PASS'
                summary['stages'].append(metadata)
            summary['status']='PYTHON_SCOPED_PASS' if all_ok else 'PYTHON_SCOPED_BLOCKED'
    except (ValueError,TypeError,OSError,subprocess.SubprocessError):
        summary['reason']='SOURCE_OR_RUNNER_BLOCKED'
    print('AXIA_PR52_PUBLIC_PYTHON '+json.dumps(summary,sort_keys=True),flush=True)
    return 0 if summary['status']=='PYTHON_SCOPED_PASS' else 3


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--private-root',type=Path,required=True)
    ap.add_argument('--scope',choices=SCOPES,required=True)
    a=ap.parse_args()
    sys.exit(run(a.private_root))
