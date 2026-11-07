#!/usr/bin/env python3
"""RED only: protected checkout of private R07 missing module and no-actuation test."""
import json
from pathlib import Path
import subprocess
import sys
PIN='08c19e550a11e5707e3bee689baa61958021d9f8'
def main():
    p=Path('_instructor_private')
    try:
        sha=subprocess.run(['git','rev-parse','HEAD'],cwd=p,check=True,
                    capture_output=True,text=True,timeout=10).stdout.strip()
        if sha!=PIN:raise ValueError('SHA_MISMATCH')
        t=subprocess.run([sys.executable,'-m','pytest','-q',
                         'tests/unit/test_p1_t08_local_r07_admission.py'],
                         cwd=p,capture_output=True,text=True,timeout=50)
        status='EXPECTED_RED_REPRODUCED' if (
            t.returncode!=0 and 'ModuleNotFoundError' in t.stdout+t.stderr
            and 'p1_t08_local_r07_admission' in t.stdout+t.stderr
            ) else 'RED_NOT_PROVEN'
    except (OSError,subprocess.SubprocessError,ValueError):
        status='RED_NOT_PROVEN'
    print('AXIA_LOCAL_R07_TDD '+json.dumps({'status':status,'source_sha':PIN,
                        'goal_sent':False,'fault_injected':False,
                        'gate_accepted':False},sort_keys=True))
    return 0 if status=='EXPECTED_RED_REPRODUCED' else 3
if __name__=='__main__':sys.exit(main())
