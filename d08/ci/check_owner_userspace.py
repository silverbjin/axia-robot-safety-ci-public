#!/usr/bin/env python3
"""Read-only owner-vs-CI CRITICAL USERSPACE parity. Never claims WSL2 parity.

Owner profile captured 2026-11-10. No Goal, Gazebo service, or apt change.
CI installs pinned packages separately; this script validates, not repairs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/'d08/ci/owner_userspace_contract_20261111.json'
ROS_SHARE=Path('/opt/ros/jazzy/share')
REQUIRED_KEYS=('os','architecture','python_major_minor','python_full_version',
               'ros_distro','gz_sim_version','critical_packages',
               'official_file_sha256')

def _run(args):
    try:
        p=subprocess.run(args,text=True,capture_output=True,timeout=18,check=False)
        return p.stdout.strip() if p.returncode==0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None

def _os_release():
    fields={}
    try:
        for line in Path('/etc/os-release').read_text().splitlines():
            if '=' in line:
                k,v=line.split('=',1)
                fields[k]=v.strip().strip('"')
    except OSError:
        pass
    return {'id':fields.get('ID'),'version_id':fields.get('VERSION_ID'),
            'version_codename':fields.get('VERSION_CODENAME')}

def _apt_version(name):
    # Explicit argv avoids shell interpolation of dpkg's format argument.
    return _run(['dpkg-query','-W','-f=${Version}',name])

def _official_sha(path):
    parts=Path(path).parts
    if len(parts)<3 or '..' in parts or parts[0] not in ('nav2_bringup','nav2_minimal_tb3_sim'):
        return None
    target=ROS_SHARE.joinpath(*parts)
    if not target.is_file() or target.is_symlink():
        return None
    return hashlib.sha256(target.read_bytes()).hexdigest()

def collect(contract):
    versions={n:_apt_version(n) for n in contract['critical_packages']}
    files={p:_official_sha(p) for p in contract['official_file_sha256']}
    gz= _run(['gz','sim','--version']) or ''
    match=re.search(r'\b(\d+\.\d+\.\d+)\b',gz)
    # Some CLI variants do not emit --version reliably; matching the
    # exact installed gz-sim8 package is also checked separately.
    if not match and versions.get('gz-sim8-cli'):
        match=re.search(r'^(\d+\.\d+\.\d+)',versions['gz-sim8-cli'])
    return {
      'os':_os_release(),
      'architecture':platform.machine(),
      'python_major_minor':f'{sys.version_info.major}.{sys.version_info.minor}',
      'python_full_version':platform.python_version(),
      'ros_distro':os.environ.get('ROS_DISTRO'),
      'gz_sim_version':match.group(1) if match else None,
      'critical_packages':versions,
      'official_file_sha256':files,
    }

def compare(contract,actual):
    missing=[key for key in REQUIRED_KEYS if key not in contract]
    if missing:
        return {'status':'INVALID_CONTRACT','mismatches':{'contract_missing':missing},
                'wsl2_kernel_parity':False,'certified_estop':False}
    errs={}
    for key in ('os','architecture','python_major_minor','python_full_version','ros_distro',
                'gz_sim_version'):
        want=contract[key]
        got=actual.get(key)
        if got!=want:
            errs[key]={'expected':want,'actual':got}
    for key in ('critical_packages','official_file_sha256'):
        expected=contract[key]
        observed=actual.get(key,{})
        if not isinstance(expected,dict) or not isinstance(observed,dict):
            errs[key]={'error':'NOT_A_MAPPING'}
            continue
        diff={name:{'expected':value,'actual':observed.get(name)}
              for name,value in expected.items() if observed.get(name)!=value}
        if diff:errs[key]=diff
    return {
      'status':'CRITICAL_USERSPACE_PARITY_PASS' if not errs else 'CRITICAL_USERSPACE_PARITY_BLOCKED',
      'mismatches':errs,
      'package_checks':len(contract['critical_packages']),
      'official_sha256_checks':len(contract['official_file_sha256']),
      'wsl2_kernel_parity':False,
      'wslg_gui_gpu_parity':False,
      'full_639_package_clone':False,
      'goal_sent':False,
      'certified_estop':False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--contract',type=Path,default=CONTRACT)
    p.add_argument('--inventory',type=Path,help='ONLY for synthetic unit tests')
    p.add_argument('--report',type=Path)
    p.add_argument('--strict',action='store_true')
    args=p.parse_args()
    contract=json.loads(args.contract.read_text())
    actual=json.loads(args.inventory.read_text()) if args.inventory else collect(contract)
    result=compare(contract,actual)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('AXIA_D08_OWNER_'+result['status']+' package_checks='+str(result.get('package_checks',0))+
          ' official_sha256_checks='+str(result.get('official_sha256_checks',0))+
          ' WSL_KERNEL_PARITY=false WSLG_GUI_PARITY=false',flush=True)
    if result['mismatches']:
        print(json.dumps(result['mismatches'],sort_keys=True,indent=2),flush=True)
    return 0 if result['status']=='CRITICAL_USERSPACE_PARITY_PASS' or not args.strict else 2

if __name__=='__main__':
    raise SystemExit(main())
