#!/usr/bin/env python3
"""Sealed CI source gate for Instructor TDD tests, never prints private logs.

No ROS 2, Goal, Fault or sim side effects; only unittest on exact private SHA.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

RED = '13391a9fa8b053c2c9cfcf0d2c023a9c909cd1d9'
STAGES = {
    'red': {'pin': RED, 'patterns': ('test_p1_t08_r05_typed_field_gate.py',), 'expect_red': True},
    'r05': {'pin': '133f3eca2f1004a89beebbdca8f080f3eb073374', 'patterns': ('test_p1_t08_r05_typed_field_gate.py',), 'expect_red': False},
}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--private-root',type=Path,required=True)
    ap.add_argument('--stage',choices=STAGES,required=True)
    args=ap.parse_args()
    expected=STAGES[args.stage]
    p=args.private_root
    try:
        sha=subprocess.run(['git','rev-parse','HEAD'],cwd=p,check=True,
                           capture_output=True,text=True,timeout=8).stdout.strip()
        if sha!=expected['pin']:
            raise ValueError('CHECKOUT_SHA_MISMATCH')
        if args.stage != 'red':
            check=subprocess.run(['bash','-n','scripts/run_p1_t08_wsl2_field_capture.sh'],
                                 cwd=p,capture_output=True,text=True,timeout=12)
            if check.returncode!=0:
                raise ValueError('GREEN_FAILED')
            check=subprocess.run([sys.executable,'-m','compileall','-q',
                                  'tools/p1_t08_field_goal_gate.py'],
                                 cwd=p,capture_output=True,text=True,timeout=12)
            if check.returncode!=0:
                raise ValueError('GREEN_FAILED')
        outcomes=[]
        for pattern in expected['patterns']:
            x=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests/unit','-p',pattern,'-v'],
                              cwd=p,capture_output=True,text=True,timeout=80)
            outcome = x.returncode != 0
            if expected['expect_red']:
                if not outcome or ('ModuleNotFoundError' not in x.stderr
                                   and 'AssertionError' not in x.stderr):
                    raise ValueError('RED_NOT_PROVEN')
                status='EXPECTED_RED'
            else:
                if outcome:
                    raise ValueError('GREEN_FAILED')
                status='PASS'
            outcomes.append({'stage':pattern.split('.')[0].replace('test_p1_t08_',''), 'status':status})
        print('AXIA_R05_R08_TDD '+json.dumps({'status':'RED_REPRODUCED' if expected['expect_red'] else 'GREEN',
                                             'stages':outcomes,'gate_accepted':False},sort_keys=True),flush=True)
        return 0
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        reason=str(e) if isinstance(e,ValueError) and str(e) in (
            'CHECKOUT_SHA_MISMATCH','RED_NOT_PROVEN','GREEN_FAILED') else 'EXECUTION_BLOCKED'
        print('AXIA_R05_R08_TDD '+json.dumps({'status':'BLOCKED','reason':reason,'gate_accepted':False}),flush=True)
        return 3

if __name__=='__main__':
    raise SystemExit(main())
