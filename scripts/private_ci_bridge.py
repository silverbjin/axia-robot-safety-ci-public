#!/usr/bin/env python3
"""Public orchestration, private execution: print ONLY allowlisted counters.

No private stdout/stderr, JUnit XML, rosbag, source or credentials may be published.
All evidence here is EPHEMERAL. This is NOT the final acceptance runner.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

PIN = '8c57dad5d4d03d132bbee99020e5e36fc7673c80'
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
    'SCAN_STABLE_WINDOW_MISSING_OR_BAD',
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
        for private_field, public_field in (
            ('observer_scan_intervals', 'observer_scan_intervals'),
            ('observer_scan_gaps_over_0p5s', 'observer_scan_gaps_over_0_5s'),
            ('observer_scan_invalid_intervals', 'observer_scan_invalid_intervals'),
            ('clock_samples', 'clock_samples'),
        ):
            value = prestart.get(private_field)
            if private_field == 'clock_samples':
                value = rtf.get('clock_samples')
            record[public_field] = (value if type(value) is int and
                0 <= value <= 1000000 else 'UNAVAILABLE')
        observer_max = prestart.get('observer_scan_max_gap_sec')
        record['observer_scan_max_gap_sec'] = (
            round(observer_max, 4) if type(observer_max) in (int,float)
            and 0 <= observer_max <= 100 else 'UNAVAILABLE')
        window = prestart.get('scan_stable_window')
        window = window if isinstance(window, dict) else {}
        record['scan_window_status'] = (
            window.get('status') if window.get('status') in
            ('WINDOW_VERIFIED', 'WINDOW_OVERRUN', 'WINDOW_INVALID',
             'WINDOW_INSUFFICIENT') else 'UNAVAILABLE')
        for attr in ('intervals', 'over_0p5s', 'invalid'):
            value = window.get(attr)
            record['scan_window_' + attr] = (
                value if type(value) is int and 0 <= value <= 1000000
                else 'UNAVAILABLE')
        allowed_warnings = ('ROSBAG_RX_GAP_NOT_SUPERVISOR_DEADLINE',
                            'BOOT_CALLBACK_OVERRUN_BEFORE_STABLE_WINDOW')
        original_warnings = report.get('observation_warnings')
        original_warnings = (original_warnings if isinstance(original_warnings,list)
                             else [])
        record['observation_warnings'] = [
            suffix for suffix in allowed_warnings
            if f'run_{i}:{suffix}' in original_warnings]
        control = _private_json(folder / 'shutdown_control.json')
        record['shutdown_control_status'] = (
            control.get('status') if control.get('status') in
            ('SHUTDOWN_CONFIRMED','SHUTDOWN_BLOCKED') else 'UNAVAILABLE')
        reasons = (
            'BOTH_MANAGERS_ACKNOWLEDGED_SHUTDOWN',
            'NAVIGATION_SERVICE_UNAVAILABLE',
            'NAVIGATION_SERVICE_RESPONSE_TIMEOUT',
            'NAVIGATION_SERVICE_REPORTED_FAILURE',
            'NAVIGATION_SERVICE_EXCEPTION',
            'LOCALIZATION_SERVICE_UNAVAILABLE',
            'LOCALIZATION_SERVICE_RESPONSE_TIMEOUT',
            'LOCALIZATION_SERVICE_REPORTED_FAILURE',
            'LOCALIZATION_SERVICE_EXCEPTION',
            'LOCALIZATION_PREPAUSE_SERVICE_RESPONSE_TIMEOUT',
            'LOCALIZATION_PREPAUSE_SERVICE_REPORTED_FAILURE',
            'LOCALIZATION_PREPAUSE_SERVICE_EXCEPTION',
            'PREPAUSE_NOT_AUTHORIZED',
            'SHUTDOWN_EXCEPTION', 'SIMULATION_MARKERS_MISSING',
            'ROS_JAZZY_REQUIRED', 'INVALID_TIMEOUT',
        )
        record['shutdown_control_reason'] = (
            control.get('reason') if control.get('reason') in reasons
            else 'UNRECOGNIZED')
        requested = control.get('prepause_requested')
        record['prepause_requested'] = (
            requested if type(requested) is bool else 'UNAVAILABLE')
        managers = control.get('managers')
        managers = managers if isinstance(managers,dict) else {}
        for key in ('navigation', 'localization'):
            entry = managers.get(key)
            entry = entry if isinstance(entry,dict) else {}
            success = entry.get('success')
            record[key + '_shutdown_ack'] = (
                success if type(success) is bool else 'UNAVAILABLE')
            for private_key in ('discovery_wall_sec','response_wall_sec',
                                'elapsed_wall_sec'):
                value = entry.get(private_key)
                record[key + '_' + private_key] = (
                    round(value, 3) if type(value) in (int,float)
                    and 0 <= value <= 300 else 'UNAVAILABLE')
        localization = managers.get('localization')
        localization = localization if isinstance(localization,dict) else {}
        previous = localization.get('prepause')
        previous = previous if isinstance(previous,dict) else {}
        ack = previous.get('success')
        record['localization_prepause_ack'] = (
            ack if type(ack) is bool else 'UNAVAILABLE')
        ready = localization.get('service_ready_after_timeout')
        record['localization_service_ready_after_timeout'] = (
            ready if type(ready) is bool else 'UNAVAILABLE')
        manager_active = localization.get('manager_active_after_timeout')
        manager_states = (
            'ACTIVE','INACTIVE','NO_RESPONSE','SERVICE_UNAVAILABLE',
            'SERVICE_ERROR','INVALID_RESPONSE')
        record['localization_manager_active_after_timeout'] = (
            manager_active if type(manager_active) is str
            and manager_active in manager_states else 'UNAVAILABLE')
        states = localization.get('managed_nodes_after_timeout')
        states = states if isinstance(states,dict) else {}
        allowed_states = (
            'UNCONFIGURED','INACTIVE','ACTIVE','FINALIZED',
            'UNKNOWN','SERVICE_UNAVAILABLE','NO_RESPONSE','SERVICE_ERROR')
        for name in ('amcl', 'map_server'):
            value = states.get(name)
            record[name + '_state_after_timeout'] = (
                value if value in allowed_states else 'UNAVAILABLE')
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


def private_pytest_cases(path, expected_count=7):
    """Discover top-level private test functions without publishing test names."""
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    cases = [node.name for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
             and node.name.startswith('test_')]
    if (len(cases) != expected_count or len(set(cases)) != expected_count
            or any(not name.isidentifier() for name in cases)):
        raise GateBlocked('T06_COLLECTION_MISMATCH')
    return cases


def classify_private_junit_failure(path):
    """Strict enum-based diagnosis; never serialize private traceback or test ID."""
    if not Path(path).is_file():
        return 'JUNIT_MISSING'
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return 'JUNIT_INVALID'
    failures = [x for x in root.iter() if x.tag in ('failure', 'error')]
    if not failures:
        return 'NONZERO_WITHOUT_JUNIT_FAILURE'
    text = ' '.join((str(x.get('message', '')) + ' ' + str(x.text or ''))
                    for x in failures).lower()
    rules = (
        ('initial health never ready', 'BOOT_HEALTH'),
        ('goal authorization missing', 'GOAL_AUTHORIZATION'),
        ('authorized goal did not produce nonzero', 'MOTION_COMMAND_SETUP'),
        ('unexpected stop cause', 'TRIP_REASON_RACE'),
        ('missing navigatetopose cancellation', 'ACTION_CANCEL_MISSING'),
        ('goal cancellation must reach terminal', 'CANCEL_NOT_TERMINAL'),
        ('test service not ready', 'SERVICE_DISCOVERY'),
        ('ros service response timeout', 'SERVICE_RESPONSE_TIMEOUT'),
        ('not in', 'ASSERTION_FAILED'),
    )
    for needle, code in rules:
        if needle in text:
            return code
    return 'OTHER_ASSERTION_OR_FIXTURE'


def run_isolated_t06(root, env, tmpdir, setup):
    """Seven private cases x three fresh ROS contexts, all mandatory."""
    path = FAKE_FAULT_FILES[0]
    cases = private_pytest_cases(root / path)
    problems = []
    for repetition in range(1, 4):
        for index, name in enumerate(cases, start=1):
            stage = f'T06_R{repetition}_CASE_{index:02d}'
            domain = 180 + (repetition - 1) * len(cases) + index
            junit = tmpdir / (stage + '.xml')
            cmd = bash_with_ros_overlay(
                setup, ['python3', '-m', 'pytest', '-q',
                        f'{path}::{name}', f'--junitxml={junit}'])
            try:
                scrubbed_run(stage, cmd, root, dict(env, ROS_DOMAIN_ID=str(domain)),
                             tmpdir, 135, junit)
            except GateBlocked:
                problems.append((repetition, index))
                print('AXIA_PRIVATE_T06_DIAGNOSTIC ' + json.dumps({
                    'repeat': repetition,
                    'case': f'T06-{index:02d}',
                    'status': 'BLOCKED',
                    'reason': classify_private_junit_failure(junit),
                    'private_log_uploaded': False,
                    'gate_accepted': False
                }, sort_keys=True), flush=True)
    print('AXIA_PRIVATE_T06_SUMMARY ' + json.dumps({
        'cases': len(cases), 'repetitions': 3,
        'executions': len(cases) * 3,
        'blocked_cases': len(problems),
        'status': 'PASS' if not problems else 'BLOCKED',
        'gate_accepted': False
    }, sort_keys=True), flush=True)
    if problems:
        raise GateBlocked('T06_ISOLATED_CASES_BLOCKED')


def isolated_fault_suites():
    """Stable category labels only; no hidden test names or exception details."""
    return (
        ('T06_FAULT', FAKE_FAULT_FILES[0], 181),
        ('T04_ACTION', FAKE_FAULT_FILES[1], 182),
        ('T05_LAUNCH', FAKE_FAULT_FILES[2], 183),
    )


def preloc_settings(gate):
    """Exact flags for no-motion comparison, not final G00/G03/G04."""
    if gate == 'gazebo3':
        return 3, False
    if gate == 'gazebo3-prepause':
        return 3, True
    if gate == 'gazebo10':
        return 10, False
    raise GateBlocked('UNSUPPORTED_GATE')


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
                # T06: seven case-level isolated ROS contexts (not one shared
                # module process). Each case's private traceback is ephemeral.
                run_isolated_t06(root, env, tmpdir, setup_file)
                # T04/T05 maintain independent process and DDS domain.
                for stage, path, domain in isolated_fault_suites()[1:]:
                    suite_env = dict(env, ROS_DOMAIN_ID=str(domain))
                    junit = tmpdir / (stage + '.xml')
                    cmd = bash_with_ros_overlay(
                        setup_file, ['python3', '-m', 'pytest', '-q',
                                     path, f'--junitxml={junit}'])
                    scrubbed_run(stage, cmd, root, suite_env, tmpdir, 600, junit)
        elif gate in ('gazebo3', 'gazebo3-prepause', 'gazebo10'):
            count, prepause = preloc_settings(gate)
            if prepause:
                # No-goal only: the private shutdown tool separately refuses
                # this opt-in outside AXIA_T08_PRE_GOAL_NO_GOAL_CI.
                env['AXIA_P1_SHUTDOWN_LOCALIZATION_PREPAUSE'] = 'YES'
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
    parser.add_argument('--gate', choices=('unit-middleware', 'fake-faults', 'gazebo3', 'gazebo3-prepause', 'gazebo10'), required=True)
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
