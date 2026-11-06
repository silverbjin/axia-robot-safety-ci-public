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

PIN = '430e04fd5ce47b4909f4011d74fc6ec1dd1c338f'
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
            if counts['tests'] < 1 or counts['failures'] or counts['errors'] or counts['skipped']:
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
        'passed_runs': count, 'private_prelocal_readonly_executed': True,
        'goal_sent': False, 'fault_injected': False, 'gate_accepted': False
    }, sort_keys=True), flush=True)


def private_runtime_env(root, inherited_env):
    """Add private Python source without erasing sourced Jazzy PYTHONPATH."""
    env = dict(inherited_env)
    paths = [str(Path(root) / rel) for rel in (
        'ros2_ws/src/axia_safety_supervisor',
        'ros2_ws/src/axia_fault_injector',
        'ros2_ws/src/axia_scenario_verifier', 'tools')]
    if env.get('PYTHONPATH'):
        paths.append(env['PYTHONPATH'])
    env['PYTHONPATH'] = os.pathsep.join(paths)
    env['ROS_DOMAIN_ID'] = '167'
    env['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'LOCALHOST'
    env['GITHUB_SHA'] = PIN
    return env


def ros_workspace_build(root, env, tmpdir):
    """Build private nodes so ros2 run can resolve them; no build logs public."""
    scrubbed_run('ROS_RUNTIME_IMPORT',
                 ['python3', '-c',
                  'import rclpy; import std_srvs.srv; import nav2_msgs.action; '
                  'import lifecycle_msgs.srv; import geometry_msgs.msg'],
                 root, env, tmpdir, 45)
    install = tmpdir / 'install'
    scrubbed_run('COLCON_BUILD',
                 ['colcon', '--log-base', str(tmpdir / 'colcon_log'), 'build',
                  '--base-paths', 'ros2_ws/src',
                  '--packages-select', 'axia_safety_supervisor', 'axia_fault_injector',
                  '--build-base', str(tmpdir / 'build'),
                  '--install-base', str(install), '--merge-install'],
                 root, env, tmpdir, 600)
    if not (install / 'setup.bash').is_file():
        raise GateBlocked('COLCON_SETUP_MISSING')
    return install / 'setup.bash'


def bash_with_ros_overlay(install_setup, command):
    """Use argv for the sourced file and executable; never interpolate private paths."""
    return ['bash', '-c',
            'set -eo pipefail; source "$1"; shift; exec "$@"',
            'axia-public-ci-bridge', str(install_setup), *command]


# Explicit, finite allowlists: never echo source-controlled text or exception strings.
SAFE_EVIDENCE_FIELDS = {
    'startup_verdict.json': ('startup', 'status', ('SMOKE_READY', 'BLOCKED', 'ERROR')),
    'pre_goal_gate.json': ('pre_goal', 'status', ('PRE_GOAL_READY', 'BLOCKED', 'PRE_GOAL_BLOCKED')),
    'supervisor_prestart.json': ('supervisor', 'status', ('SUPERVISOR_PRESTART_READY', 'SUPERVISOR_PRESTART_BLOCKED')),
    'shutdown_verdict.json': ('shutdown', 'status', ('SHUTDOWN_CLEAN', 'SHUTDOWN_FAILED', 'SHUTDOWN_INCONCLUSIVE', 'BLOCKED', 'SHUTDOWN_BLOCKED')),
    'scan_timing.json': ('scan_timing', 'status', ('SCAN_TIMING_OBSERVED_ONLY',
                                                'SCAN_TIMING_REQUIRES_CALIBRATION', 'SCAN_TIMING_INVALID')),
}
SAFE_STARTUP_GATES = (
    'CLOCK_READY', 'NAVIGATION_NOT_ACTIVE', 'LOCALIZATION_START',
    'MAP_AMCL_ACTIVE', 'INITIALPOSE_MAP_CHECKED', 'AMCL_TF_READY',
    'NAVIGATION_START', 'CM_ACTIVE', 'GRAPH_READY', 'NAV2_ACTION_READY',
)


def _private_json(path):
    try:
        record = json.loads(Path(path).read_text(encoding='utf-8'))
        return record if isinstance(record, dict) else {}
    except (OSError, ValueError):
        return {}


SAFE_RTM_BLOCKERS = {
    'MISSING_RUN_DIRECTORY', 'SOURCE_COMMIT_MISMATCH',
    'P1_STARTUP_NOT_VERIFIED', 'P0_PREGOAL_G01_NOT_READY',
    'SUPERVISOR_PRESTART_NOT_STABLE', 'NAV2_SHUTDOWN_NOT_CLEAN',
    'SCAN_TIMING_UNCALIBRATED', 'UNAUTHORIZED_GOAL_OR_FAULT_EVIDENCE',
    'SHA_MANIFEST_MISSING', 'SHA_MANIFEST_EMPTY', 'SHA_LINE_INVALID',
    'SHA_DIGEST_INVALID', 'SHA_ENTRY_INVALID', 'SHA_PATH_INVALID',
    'SHA_FILESET_MISMATCH', 'SUPERVISOR_SCAN_CALLBACK_TIMING_MISSING',
    'SUPERVISOR_SCAN_CALLBACK_OVERRUN', 'RTF_OBSERVATION_MISSING',
}


def redact_rtm_failure(value):
    if isinstance(value, str) and value in SAFE_RTM_BLOCKERS:
        return value
    if isinstance(value, str) and value.startswith('SHA_MISMATCH:'):
        return 'SHA_MISMATCH'
    return 'UNRECOGNIZED'


def private_evidence_diagnostics(root, count):
    """Only enums/integers from private ephemeral evidence may reach public logs."""
    report = _private_json(Path(root) / 'prelocal_report.json')
    rows = report.get('runs')
    rows = rows if isinstance(rows, list) else []
    out = []
    for i in range(1, count + 1):
        folder = Path(root) / f'run_{i}'
        record = {'run': i, 'gate_accepted': False}
        row = rows[i - 1] if len(rows) >= i and isinstance(rows[i - 1], dict) else {}
        failures = row.get('failures')
        record['rtm_blockers'] = (
            [redact_rtm_failure(x) for x in failures[:30]]
            if isinstance(failures, list) else ['REPORT_MISSING'])
        for filename, (label, key, choices) in SAFE_EVIDENCE_FIELDS.items():
            path = folder / filename
            obj = _private_json(path)
            record[label] = 'MISSING' if not path.is_file() else (
                obj.get(key) if obj.get(key) in choices else 'UNRECOGNIZED')
            if filename == 'startup_verdict.json':
                failed_gate = obj.get('failed_gate')
                record['startup_failed_gate'] = (failed_gate
                    if failed_gate in SAFE_STARTUP_GATES else
                    'NOT_REPORTED' if failed_gate is None else 'UNRECOGNIZED')
                stages = obj.get('stages')
                record['startup_stages_passed'] = (
                    sum(x.get('status') == 'PASS' for x in stages
                        if isinstance(x, dict))
                    if isinstance(stages, list) and len(stages) <= 100 else 0)
            if filename == 'scan_timing.json':
                gaps = obj.get('gaps_over_timeout_total')
                record['scan_gaps_over_0_5s'] = (gaps if type(gaps) is int
                    and 0 <= gaps <= 1000000 else 'UNAVAILABLE')
        clock = _private_json(folder / 'clock_diagnostics.json')
        safe_clock_reasons = ('CLOCK_READY', 'CLOCK_MISSING', 'CLOCK_STALLED',
                              'CLOCK_REGRESSION', 'NODE_SIM_TIME_UNSYNCHRONIZED',
                              'PROBE_EXCEPTION', 'SIMULATION_MARKERS_MISSING')
        reason = clock.get('reason')
        record['clock_probe_reason'] = ('MISSING'
            if not (folder / 'clock_diagnostics.json').is_file() else
            reason if reason in safe_clock_reasons else 'UNRECOGNIZED')
        prestart = _private_json(folder / 'supervisor_prestart.json')
        last_message = prestart.get('last_message')
        health = last_message.get('health_diagnostics') if isinstance(last_message, dict) else None
        health = health if isinstance(health, dict) else {}
        for source_field, public_field in (
            ('scan_callback_intervals', 'callback_intervals'),
            ('scan_callback_gaps_over_timeout', 'callback_gaps_over_0_5s'),
            ('scan_callback_invalid_intervals', 'callback_invalid_intervals'),
        ):
            value = health.get(source_field)
            record[public_field] = (value if type(value) is int
                and 0 <= value <= 1000000 else 'UNAVAILABLE')
        max_gap = health.get('scan_callback_max_gap_sec')
        record['callback_max_gap_sec'] = (round(max_gap, 4)
            if type(max_gap) in (float, int) and 0 <= max_gap <= 100
            else 'UNAVAILABLE')
        rtf = prestart.get('clock_rtf')
        rtf = rtf if isinstance(rtf, dict) else {}
        record['rtf_status'] = (
            rtf.get('status') if rtf.get('status') in
            ('RTF_OBSERVED', 'RTF_INSUFFICIENT', 'RTF_CLOCK_REGRESSION')
            else 'UNAVAILABLE')
        value = rtf.get('rtf')
        record['rtf'] = (round(value, 3)
            if type(value) in (int, float) and 0 <= value <= 100
            else 'UNAVAILABLE')
        shutdown = _private_json(folder / 'shutdown_verdict.json')
        ack = shutdown.get('lifecycle_shutdown_acknowledged')
        record['shutdown_ack'] = ack if type(ack) is bool else 'UNAVAILABLE'
        fatals = shutdown.get('fatal_signatures')
        record['shutdown_fatal_count'] = (
            len(fatals) if isinstance(fatals, list) and len(fatals) < 1000
            else 'UNAVAILABLE')
        out.append(record)
        print('AXIA_PRIVATE_DIAGNOSTIC ' + json.dumps(record, sort_keys=True),
              flush=True)
    return out


def isolated_fault_suites():
    """Stable category labels only; no hidden test names or exception details."""
    return (
        ('T06_FAULT', FAKE_FAULT_FILES[0], 181),
        ('T04_ACTION', FAKE_FAULT_FILES[1], 182),
        ('T05_LAUNCH', FAKE_FAULT_FILES[2], 183),
    )


def run_gate(private_root, gate):
    root = validate_private_commit(private_root)
    env = private_runtime_env(root, os.environ)
    # Ensure private evidence (if created by original scripts) identifies PRIVATE commit.
    env['GITHUB_SHA'] = PIN
    with tempfile.TemporaryDirectory(prefix='axia_private_bridge_',
                                     dir=os.environ.get('RUNNER_TEMP') or None) as tmp:
        tmpdir = Path(tmp)
        if gate in ('unit-middleware', 'fake-faults'):
            if gate == 'unit-middleware':
                junit = tmpdir / 'UNIT.xml'
                cmd = ['python3', '-m', 'pytest', '-q',
                       *UNIT_FILES, f'--junitxml={junit}']
                scrubbed_run('UNIT', cmd, root, env, tmpdir, 600, junit)
            setup_file = ros_workspace_build(root, env, tmpdir)
            if gate == 'unit-middleware':
                junit = tmpdir / 'JAZZY_MIDDLEWARE.xml'
                cmd = bash_with_ros_overlay(
                    setup_file, ['python3', '-m', 'pytest', '-q',
                                 *DDS_FILES, f'--junitxml={junit}'])
                scrubbed_run('JAZZY_MIDDLEWARE', cmd, root, env, tmpdir, 900, junit)
            else:
                # Separate ROS middleware lifetime/Domain per suite. One
                # pytest process can leak ROS graph/executor state into the next.
                for stage, path, domain in isolated_fault_suites():
                    suite_env = dict(env, ROS_DOMAIN_ID=str(domain))
                    junit = tmpdir / (stage + '.xml')
                    cmd = bash_with_ros_overlay(
                        setup_file, ['python3', '-m', 'pytest', '-q',
                                     path, f'--junitxml={junit}'])
                    scrubbed_run(stage, cmd, root, suite_env, tmpdir, 600, junit)
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
            try:
                scrubbed_run('GAZEBO_READONLY',
                             ['bash', 'scripts/run_p1_preacceptance_stability.sh'],
                             root, env, tmpdir, 5400 if count == 10 else 3000)
            finally:
                # Test failures must be visible as predeclared status codes only.
                # Never print private logs, arbitrary exception text, or raw JSON.
                private_evidence_diagnostics(dest, count)
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
