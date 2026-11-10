"""Privacy, schema, and drift regression: no ROS/Gazebo execution in this test."""
from pathlib import Path
import importlib.util
import copy
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'tools'
spec=importlib.util.spec_from_file_location('axia_ci_env_compare',
                                            TOOLS/'axia_ci_env_compare.py')
cmp=importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmp)

def fixture(wsl=True):
    apt={x:'1.2.3-1' for x in cmp.MIN_REQUIRED}
    apt.update({'ros-jazzy-ros-gz':'1.2.3-1','gz-harmonic':'8.0-1'})
    return {
      'schema':cmp.SCHEMA,
      'profile_kind':'wsl2_owner' if wsl else 'ci_linux',
      'wsl2_detected':wsl,
      'os':{'id':'ubuntu','version_id':'24.04'},
      'architecture':'x86_64',
      'python':{'major_minor':'3.12'},
      'ros':{
        'distro':'jazzy',
        'official_file_sha256':{f:'a'*64 for f in cmp.OFFICIAL_REQUIRED}
      },
      'env_allowlist':{'rmw_implementation':'rmw_fastrtps_cpp',
                       'discovery_range':'LOCALHOST'},
      'apt_packages':apt,
    }


def test_exact_userspace_parity_ignores_unmatchable_wsl_kernel():
    owner=fixture()
    ci=fixture(wsl=False)
    ci['kernel_release']='6.8.0-ubuntu'
    ci['wslg']={'dev_dxg_exists':False}
    r=cmp.compare(owner,ci)
    assert r['status']=='PARITY_READY'
    assert r['certified_estop'] is False
    assert r['gazebo_goal_test_passed'] is False


def test_one_nav2_drift_must_be_visible_and_fail_closed():
    a=fixture();b=fixture(wsl=False)
    b['apt_packages']['ros-jazzy-nav2-bringup']='9.9.9-0'
    result=cmp.compare(a,b)
    assert result['status']=='USERSPACE_DRIFT'
    assert any(x['field']=='package.ros-jazzy-nav2-bringup'
               for x in result['critical_issues'])


def test_upstream_world_sha_drift_must_be_reported():
    a=fixture();b=fixture(wsl=False)
    key='nav2_minimal_tb3_sim/worlds/tb3_sandbox.sdf.xacro'
    b['ros']['official_file_sha256'][key]='b'*64
    assert cmp.compare(a,b)['status']=='USERSPACE_DRIFT'


def test_missing_wsl2_or_missing_owner_critical_is_never_parity():
    a=fixture();b=fixture(wsl=False)
    a['wsl2_detected']=False
    assert cmp.compare(a,b)['status']=='USERSPACE_DRIFT'
    a=fixture();a['apt_packages'].pop('ros-jazzy-nav2-minimal-tb3-sim')
    assert cmp.compare(a,b)['status']=='USERSPACE_DRIFT'


def test_package_version_is_validated_not_shell_executed(tmp_path):
    a=fixture()
    a['apt_packages']['ros-jazzy-nav2-bringup']='$(touch /tmp/unsafe)'
    p=tmp_path/'bad.json'
    p.write_text(json.dumps(a))
    try:
        cmp.read_profile(p)
    except ValueError as exc:
        assert 'INVALID_PACKAGE_OR_VERSION' in str(exc)
    else:
        raise AssertionError('untrusted apt version accepted')


def test_capture_only_collects_explicit_allowlist():
    src=(TOOLS/'axia_env_profile.py').read_text()
    shell=(ROOT/'scripts/axia_wsl2_env_capture_once.sh').read_text()
    for secret in ('hostname()', 'gethostname(', 'ip addr', 'ifconfig',
                   'ssh-key', 'GITHUB_TOKEN', 'gh auth token',
                   'os.environ.copy(', 'pip freeze', 'ros2 bag'):
        assert secret not in src
        assert secret not in shell
    assert "docs/environment/wsl2_owner_profile.json" in shell
    assert "silverbjin/axia-robot-safety-instructor" in shell
    assert 'AXIA_PUBLIC_SHA' in shell
    subprocess.run(['bash','-n',
                    str(ROOT/'scripts/axia_wsl2_env_capture_once.sh')],
                   check=True)


def test_json_roundtrip_in_cli(tmp_path):
    owner=tmp_path/'owner.json';ci=tmp_path/'ci.json';out=tmp_path/'report.json'
    owner.write_text(json.dumps(fixture()))
    ci.write_text(json.dumps(fixture(wsl=False)))
    result=subprocess.run([sys.executable,str(TOOLS/'axia_ci_env_compare.py'),
        '--owner',str(owner),'--ci',str(ci),'--report',str(out)],
        capture_output=True,text=True,timeout=5)
    assert result.returncode==0,result.stderr
    assert json.loads(out.read_text())['status']=='PARITY_READY'


def test_real_linux_collector_executes_without_ros_or_network(tmp_path):
    # Runs on the actual GitHub runner; CI Linux must never claim to be WSL2.
    out=tmp_path/'ci-profile.json'
    result=subprocess.run([sys.executable,str(TOOLS/'axia_env_profile.py'),
                           '--output',str(out)],capture_output=True,text=True,
                          timeout=35,check=False)
    assert result.returncode==0,result.stderr
    document=json.loads(out.read_text())
    assert document['schema']==cmp.SCHEMA
    assert isinstance(document['apt_packages'],dict)
    assert document['privacy']['hostname_username_paths_addresses_tokens_excluded'] is True
    assert (out.stat().st_mode & 0o077)==0
    assert 'hostname' not in document and 'username' not in document
    assert 'all_environment_variables' not in document
    assert document['profile_kind'] in ('ci_linux','wsl2_owner')


def test_linux_wsl2_gate_fails_before_writing_user_profile(tmp_path):
    if 'microsoft' in __import__('platform').release().lower():
        return
    dest=tmp_path/'never-owner-profile.json'
    result=subprocess.run([sys.executable,str(TOOLS/'axia_env_profile.py'),
                           '--output',str(dest),'--require-wsl2'],
                          capture_output=True,text=True,timeout=35)
    assert result.returncode==2
    assert 'AXIA_ENV_BLOCKED_NOT_WSL2' in result.stderr
    assert not dest.exists()
