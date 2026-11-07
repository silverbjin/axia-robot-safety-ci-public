#!/usr/bin/env python3
"""Private R06 RED verification, safe one module test only, no raw disclosure."""
import json
from pathlib import Path
import subprocess
import sys
PIN='2f2df394f8ec04c196afb095ad2c53ea0e374670'
def main():
    p=Path('_instructor_private')
    try:
        sha=subprocess.run(['git','rev-parse','HEAD'],cwd=p,check=True,
                 capture_output=True,text=True,timeout=10).stdout.strip()
        if sha!=PIN:raise ValueError('SHA_MISMATCH')
        x=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests/unit',
                     '-p','test_p1_t08_local_batch.py','-v'],cwd=p,
                      capture_output=True,text=True,timeout=40)
        ok=x.returncode!=0 and 'ModuleNotFoundError' in x.stderr and (
            'p1_t08_local_batch' in x.stderr)
        status='EXPECTED_RED_REPRODUCED' if ok else 'RED_NOT_PROVEN'
    except (OSError,ValueError,subprocess.SubprocessError):
        status='RED_NOT_PROVEN'
    print('AXIA_LOCAL_R06_TDD '+json.dumps({'status':status,'stage':'R06_LOCAL_BATCH',
           'source_sha':PIN,'goal_sent':False,'fault_injected':False,
           'gate_accepted':False},sort_keys=True))
    return 0 if status=='EXPECTED_RED_REPRODUCED' else 3
if __name__=='__main__':sys.exit(main())
