"""Classify actual Nav2 Collision Monitor shutdown from launch evidence.

Do not disguise the observed ROS native SIGSEGV; absence of this line is not
a formal proof of safe shutdown or certified motion stop.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

PATTERN=re.compile(
    r'^\[ERROR\] \[collision_monitor-\d+\]: process has died '
    r'\[pid \d+, exit code -11, ',re.MULTILINE)

def assess_teardown_log(text:str)->dict:
    if not isinstance(text,str):
        raise TypeError('teardown log must be text')
    observed=bool(PATTERN.search(text))
    return {'collision_monitor_exit_minus11':observed,
            'teardown_status':'CM_SIGSEGV_OBSERVED' if observed
            else 'CM_SIGSEGV_NOT_SEEN_IN_SUPPLIED_LOG',
            'clean_shutdown_certified':False,
            'goal_completion_inferred':False,
            'certified_estop':False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--log',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if not a.log.is_file():raise SystemExit('BLOCKED: missing actual launch.log')
    verdict=assess_teardown_log(a.log.read_text(errors='replace'))
    with a.out.open('x') as f:
        json.dump(verdict,f,indent=2,sort_keys=True);f.write('\n')
    print('P2_CM_TEARDOWN_AUDIT '+verdict['teardown_status'],flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
