"""L0 owner-profile parity tests: NEVER use synthetic values to claim real CI parity."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'d08/ci/check_owner_userspace.py'
CONTRACT=ROOT/'d08/ci/owner_userspace_contract_20261111.json'
spec=importlib.util.spec_from_file_location('owner_parity',SRC)
parity=importlib.util.module_from_spec(spec)
spec.loader.exec_module(parity)

def sample():
    c=json.loads(CONTRACT.read_text())
    a={k:c[k] for k in ('os','architecture','python_major_minor',
                        'python_full_version','ros_distro','gz_sim_version',
                        'critical_packages','official_file_sha256')}
    return c, a

def test_exact_collected_owner_critical_metadata_and_software_versions():
    c,_=sample()
    assert c['os']=={'id':'ubuntu','version_id':'24.04',
                     'version_codename':'noble'}
    assert c['python_full_version']=='3.12.3'
    assert c['gz_sim_version']=='8.15.0'
    assert c['critical_packages']['ros-jazzy-nav2-collision-monitor']==(
        '1.3.13-1noble.20260921.030324')
    assert c['critical_packages']['ros-jazzy-nav2-minimal-tb3-sim']==(
        '1.0.1-1noble.20261006.041307')
    assert len(c['critical_packages'])==15
    assert len(c['official_file_sha256'])==5

def test_fake_matching_inventory_never_claims_wsl2_or_gpu_parity(tmp_path):
    c, a=sample()
    result=parity.compare(c,a)
    assert result['status']=='CRITICAL_USERSPACE_PARITY_PASS'
    assert result['wsl2_kernel_parity'] is False
    assert result['wslg_gui_gpu_parity'] is False
    assert result['full_639_package_clone'] is False
    assert result['goal_sent'] is False
    report=tmp_path/'out.json'
    inventory=tmp_path/'fake.json'
    inventory.write_text(json.dumps(a))
    cp=subprocess.run([sys.executable,str(SRC),'--inventory',str(inventory),
                       '--strict','--report',str(report)],
                      capture_output=True,text=True,timeout=10)
    assert cp.returncode==0,cp.stderr
    assert json.loads(report.read_text())['wsl2_kernel_parity'] is False

def test_package_mismatch_blocks_even_if_os_and_gz_match():
    c,a=sample()
    a['critical_packages']=dict(a['critical_packages'])
    a['critical_packages']['ros-jazzy-nav2-collision-monitor']='1.3.14'
    result=parity.compare(c,a)
    assert result['status']=='CRITICAL_USERSPACE_PARITY_BLOCKED'
    assert 'ros-jazzy-nav2-collision-monitor' in result['mismatches']['critical_packages']

def test_missing_official_nav2_file_blocks():
    c,a=sample()
    a['official_file_sha256']=dict(a['official_file_sha256'])
    a['official_file_sha256']['nav2_minimal_tb3_sim/worlds/tb3_sandbox.sdf.xacro']=None
    result=parity.compare(c,a)
    assert result['status']=='CRITICAL_USERSPACE_PARITY_BLOCKED'

def test_python_patch_mismatch_blocks():
    c,a=sample()
    a['python_full_version']='3.12.11'
    assert parity.compare(c,a)['status']=='CRITICAL_USERSPACE_PARITY_BLOCKED'

def test_no_automatic_goal_or_certified_estop_claim():
    c,a=sample()
    r=parity.compare(c,a)
    assert r['goal_sent'] is False
    assert r['certified_estop'] is False
    assert c['run_contract']['ros_automatic_discovery_range']=='LOCALHOST'
