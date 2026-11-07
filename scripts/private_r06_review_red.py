#!/usr/bin/env python3
"""Protected R06 REVIEW RED: prove ACK shape and symlink parent regressions."""
import json
from pathlib import Path
import re
import subprocess
import sys
PIN='3978aa711afcb49953342bd3a4c00441e87255a3'
def main():
    p=Path('_instructor_private')
    status='REVIEW_RED_NOT_PROVEN'
    try:
        sha=subprocess.run(['git','rev-parse','HEAD'],cwd=p,check=True,
                     capture_output=True,text=True,timeout=10).stdout.strip()
        if sha!=PIN:raise ValueError('PIN_MISMATCH')
        x=subprocess.run([sys.executable,'-m','unittest','discover','-s',
                'tests/unit','-p','test_p1_t08_local_batch.py','-v'],
                cwd=p,capture_output=True,text=True,timeout=50)
        # Suppress private stdout/stderr, publish allowlisted counts only.
        ran=re.search(r'Ran (\d+) tests? in ',x.stderr)
        if x.returncode!=0 and ran and int(ran.group(1))==11 and (
                'test_malformed_typed_ack_provenance_fails_closed_not_crash' in x.stderr
                and 'test_field_shell_rejects_symlinked_output_ancestor' in x.stderr):
            status='EXPECTED_REVIEW_RED_REPRODUCED'
    except (OSError,ValueError,subprocess.SubprocessError):
        pass
    print('AXIA_LOCAL_R06_REVIEW '+json.dumps({'status':status,'source_sha':PIN,
         'scope':'NO_GAZEBO_NO_FAULT_NO_MOTION','gate_accepted':False},
         sort_keys=True))
    return 0 if status=='EXPECTED_REVIEW_RED_REPRODUCED' else 3
if __name__=='__main__':sys.exit(main())
