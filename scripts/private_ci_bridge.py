#!/usr/bin/env python3
"""Public orchestration, private execution: print ONLY allowlisted counters.

No private stdout/stderr, JUnit XML, rosbag, source or credentials may be published.
All evidence here is EPHEMERAL. This is NOT the final acceptance runner.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

PIN = '72596eff4ad801054f27a3cae1cc60f305a1e6bf'
UNIT_FILES = (
    'tests/unit/test_p1_fsm.py', 'tests/unit/test_p1_watchdog.py',
    'tests/unit/test_p1_t08_scan_full_circle.py',
    'tests/unit/test_p1_t08_supervisor_prestarter.py',
    'tests/unit/test_p1_s01_bootstrap_policy.py',
    'tests/unit/test_p1_s02_scan_timing.py',
    'tests/unit/test_p1_s03_ros_observability.py',
    'tests/unit/test_p1_s04_s05_preacceptance.py',
)
DDS_FILES = (
    'tests/ros_integration/test_p1_s01_bootstrap_node.py',
    'tests/ros_integration/test_p1_t08_health_diag.py',
    'tests/ros_integration/test_p1_t08_shutdown.py',
)
FAKE_FAULT_FILES = (
    'tests/ros_integration/test_p1_t06_faults.py',
    'tests/ros_integration/test_p1_t04_action.py',
    'tests/ros_integration/test_p1_t05_launch.py',
)


class GateBlocked(RuntimeError):
    """Do not attach private command output to this exception."""


def parse_junit(file):
    if not Path(file).is_file():
        raise GateBlocked('JUNIT_MISSING')
    root = ET.parse(file).getroot()
    suites = [root] if root.tag == 'testsuite' else list(root.findall('testsuite'))
    if not suites:
        raise GateBlocked('JUNIT_INVALID')
    return {key: sum(int(x.attrib.get(key, '0')) for x in suites)
            for key in ('tests', 'failures', 'errors', 'skipped')}


def validate_private_commit(directory):
    root = Path(directory).resolve()
    if not root.is_dir():
        raise GateBlocked('CHECKOUT_MISSING')
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root,
                                check=False, capture_output=True, text=True, timeout=12)
    except (OSError, subprocess.TimeoutExpired):
        raise GateBlocked('COMMIT_PROBE_FAILED') from None
    if result.returncode != 0 or result.stdout.strip() != PIN:
        raise GateBlocked('PRIVATE_SHA_MISMATCH')
    return root


def scrubbed_run(stage, command, workdir, env, tmpdir, timeout_sec, junit=None):
    """Never stream private command stdout/stderr to public workflow logs."""
    log = Path(tmpdir) / (stage.lower() + '.private.log')
    timed_out = False
    with log.open('wb') as out:
        try:
            p = subprocess.run(command, cwd=workdir, env=env, stdout=out,
                               stderr=subprocess.STDOUT, timeout=timeout_sec, check=False)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            timed_out, rc = True, 124
        except OSError:
            rc = 127
    result = {'stage': stage, 'status': 'PASS' if rc == 0 else 'BLOCKED',
              'rc': rc, 'timed_out': timed_out, 'private_log_uploaded': False,
              'gate_accepted': False}
    if junit is not None:
        try:
            counts = parse_junit(junit)
            result.update(counts)
            if counts['tests'] < 1 or counts['failures'] or counts['errors']:
                result['status'] = 'BLOCKED'
        except (GateBlocked, ET.ParseError, ValueError):
            result['status'] = 'BLOCKED'
            result['junit_state'] = 'MISSING_OR_INVALID'
    print('AXIA_PRIVATE_BRIDGE ' + json.dumps(result, sort_keys=True), flush=True)
    if result['status'] != 'PASS':
        raise GateBlocked('PRIVATE_STAGE_BLOCKED')
    return result


def verify_gazebo_report(root, count):
    path = Path(root) / 'prelocal_report.json'
    if not path.is_file():
        raise GateBlocked('PRIVATE_REPORT_MISSING')
    data = json.loads(path.read_text(encoding='utf-8'))
    expected = 'P1_PRELOCAL_PARTIAL_3X' if count == 3 else 'P1_PRELOCAL_STABILITY_10X_READY'
    if (data.get('status') != expected or data.get('passed_runs') != count
            or data.get('gate_accepted') is not False
            or (count == 10 and data.get('g03_g04_gazebo_fault_acceptance') != 'NOT_RUN')):
        raise GateBlocked('PRIVATE_REPORT_GATE_BLOCKED')
    print('AXIA_PRIVATE_BRIDGE ' + json.dumps({
        'stage': f'GAZEBO_{count}X', 'status': 'READONLY_READY_ONLY',
        'passed_runs': count, 'supervisor_source_tested': True,
        'goal_sent': False, 'fault_injected': False, 'gate_accepted': False
    }, sort_keys=True), flush=True)


def run_gate(private_root, gate):
    root = validate_private_commit(private_root)
    env = os.environ.copy()
    env['PYTHONPATH'] = ':'.join(str(root / rel) for rel in (
        'ros2_ws/src/axia_safety_supervisor',
        'ros2_ws/src/axia_fault_injector',
        'ros2_ws/src/axia_scenario_verifier', 'tools'))
    env['ROS_DOMAIN_ID'] = '167'
    env['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'LOCALHOST'
    # Ensure private evidence (if created by original scripts) identifies PRIVATE commit.
    env['GITHUB_SHA'] = PIN
    with tempfile.TemporaryDirectory(prefix='axia_private_bridge_',
                                     dir=os.environ.get('RUNNER_TEMP') or None) as tmp:
        tmpdir = Path(tmp)
        if gate in ('unit-middleware', 'fake-faults'):
            if gate == 'unit-middleware':
                batches = [('UNIT', UNIT_FILES, 600), ('JAZZY_MIDDLEWARE', DDS_FILES, 900)]
            else:
                batches = [('JAZZY_FAKE_FAULTS', FAKE_FAULT_FILES, 1200)]
            for stage, files, limit in batches:
                junit = tmpdir / (stage + '.xml')
                cmd = ['python3', '-m', 'pytest', '-q', *files, f'--junitxml={junit}']
                scrubbed_run(stage, cmd, root, env, tmpdir, limit, junit)
        elif gate in ('gazebo3', 'gazebo10'):
            count = 3 if gate == 'gazebo3' else 10
            overlay = tmpdir / 'official-nav2-overlay'
            scrubbed_run('UPSTREAM_OVERLAY',
                         ['bash', 'scripts/build_official_nav2_lifecycle_overlay.sh', str(overlay)],
                         root, env, tmpdir, 1200)
            env['AXIA_NAV2_LIFECYCLE_OVERLAY_SETUP'] = str(overlay / 'install/setup.bash')
            env['AXIA_NAV2_USE_COMPOSITION'] = 'False'
            env['AXIA_P1_PRELOCAL_RUNS'] = str(count)
            dest = tmpdir / ('private-prelocal-' + str(count))
            env['AXIA_P1_PRELOCAL_ROOT'] = str(dest)
            scrubbed_run('GAZEBO_READONLY',
                         ['bash', 'scripts/run_p1_preacceptance_stability.sh'],
                         root, env, tmpdir, 5400 if count == 10 else 3000)
            verify_gazebo_report(dest, count)
        else:
            raise GateBlocked('UNSUPPORTED_GATE')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--private-root', required=True)
    parser.add_argument('--gate', choices=('unit-middleware', 'fake-faults', 'gazebo3', 'gazebo10'), required=True)
    args = parser.parse_args()
    try:
        run_gate(args.private_root, args.gate)
    except GateBlocked as exc:
        print('AXIA_PRIVATE_BRIDGE ' + json.dumps({
            'status': 'BLOCKED', 'reason': str(exc), 'private_code_disclosed': False,
            'gate_accepted': False}, sort_keys=True), flush=True)
        return 3
    except Exception:
        print('AXIA_PRIVATE_BRIDGE ' + json.dumps({
            'status': 'BLOCKED', 'reason': 'UNCLASSIFIED_PRIVATE_ERROR',
            'private_code_disclosed': False, 'gate_accepted': False}, sort_keys=True), flush=True)
        return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
