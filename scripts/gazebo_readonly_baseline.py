#!/usr/bin/env python3
"""Official Jazzy Nav2/Waffle headless, read-only startup; never an AXIA safety acceptance.

No /start, Goal, /cmd_vel or fault injection issued by this script.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for part in iter(lambda: stream.read(65536), b''):
            h.update(part)
    return h.hexdigest()


def inspect_topic(topic, env, seconds):
    """Wait for a typed message, not just the first CLI discovery attempt.

    A not-yet-advertised topic is retried only until the existing bounded
    readiness deadline; unknown CLI errors remain an immediate failure.
    """
    deadline = time.monotonic() + seconds
    attempts = 0
    last_stdout = ''
    last_stderr = ''
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {'received': False, 'error': 'READINESS_TIMEOUT',
                    'attempts': attempts, 'output_excerpt': last_stdout[:400],
                    'error_excerpt': last_stderr[:400]}
        cmd = ['ros2', 'topic', 'echo', topic, '--once']
        attempts += 1
        try:
            result = subprocess.run(cmd, env=env, text=True, capture_output=True,
                                    timeout=min(remaining, 10.0), check=False)
        except subprocess.TimeoutExpired:
            last_stderr = 'ros2 topic echo attempt timed out'
        else:
            last_stdout, last_stderr = result.stdout, result.stderr
            if result.returncode == 0:
                return {'received': True, 'attempts': attempts,
                        'return_code': result.returncode,
                        'output_excerpt': result.stdout[:400],
                        'error_excerpt': result.stderr[:400]}
            waiting_for_publisher = (
                'does not appear to be published yet' in result.stdout
                or 'Could not determine the type for the passed topic' in result.stderr)
            if not waiting_for_publisher:
                return {'received': False, 'error': 'ROS_CLI_ERROR',
                        'attempts': attempts, 'return_code': result.returncode,
                        'output_excerpt': result.stdout[:400],
                        'error_excerpt': result.stderr[:400]}
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.25, remaining))


def live_group_members(pgid):
    listing = subprocess.run(['ps', '-eo', 'pgid=,stat='],
                             capture_output=True, text=True, check=True)
    matches = []
    for line in listing.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit() and int(parts[0]) == pgid and 'Z' not in parts[1]:
            matches.append(parts[1])
    return matches


def one_run(root, number, timeout_seconds):
    target = root / f'run_{number:02d}'
    target.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env['ROS_DOMAIN_ID'] = str(120 + number)
    env['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'LOCALHOST'
    env['GZ_PARTITION'] = f'axia_public_{os.getenv("GITHUB_RUN_ID", "manual")}_{number}'
    env['TURTLEBOT3_MODEL'] = 'waffle'
    cmd = ['ros2', 'launch', 'nav2_bringup', 'tb3_simulation_launch.py',
           'headless:=True', 'use_rviz:=False', 'use_composition:=False',
           'use_respawn:=False']
    outcome = {'run': number, 'kind': 'official_nav2_gazebo_no_goal_smoke',
               'command': cmd, 'ros_domain_id': env['ROS_DOMAIN_ID'],
               'gz_partition': env['GZ_PARTITION'],
               'goal_sent': False, 'fault_injection': False,
               'supervisor_tested': False, 'gate_accepted': False,
               'start_time_unix': time.time(),
               'source_commit': env.get('GITHUB_SHA', 'UNVERIFIED'),
               'rtf_measured': False, 'scan_callback_monotonic_measured': False,
               'topics': {}, 'status': 'INCONCLUSIVE'}
    logfile = target / 'nav2_gazebo_stdout.log'
    with logfile.open('w', encoding='utf-8') as log:
        process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                   env=env, start_new_session=True)
        try:
            deadline = time.monotonic() + timeout_seconds
            for topic in ['/clock', '/scan', '/odom']:
                remaining = max(1.0, deadline - time.monotonic())
                if process.poll() is not None:
                    outcome['error'] = 'launch_terminated_early'
                    break
                result = inspect_topic(topic, env, min(remaining, 70.0))
                outcome['topics'][topic] = result
                if not result['received']:
                    outcome['error'] = 'missing_topic_message:' + topic
                    break
            else:
                outcome['status'] = 'READONLY_TOPICS_OBSERVED'
        except Exception as exc:
            outcome['error'] = f'{type(exc).__name__}:{str(exc)[:200]}'
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGINT)
                except ProcessLookupError:
                    pass
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                outcome['shutdown_escalated'] = True
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
            outcome['launch_exit_code'] = process.returncode
            time.sleep(2.0)
            outcome['residual_group_processes'] = live_group_members(process.pid)
            outcome['shutdown_clean_observed'] = (
                process.returncode in (0, -signal.SIGINT)
                and not outcome['residual_group_processes']
                and not outcome.get('shutdown_escalated', False))
    if outcome['status'] == 'READONLY_TOPICS_OBSERVED' and outcome['shutdown_clean_observed']:
        outcome['status'] = 'PUBLIC_BASELINE_SMOKE_READY'
    else:
        outcome['status'] = 'BLOCKED_OR_INCONCLUSIVE'
    outcome['end_time_unix'] = time.time()
    (target / 'verdict.json').write_text(json.dumps(outcome, indent=2) + '\n', encoding='utf-8')
    (target / 'source_commit.txt').write_text(outcome['source_commit'] + '\n', encoding='utf-8')
    files = ['nav2_gazebo_stdout.log', 'verdict.json', 'source_commit.txt']
    (target / 'SHA256SUMS').write_text(
        ''.join(f'{sha256_file(target / f)}  {f}\n' for f in files), encoding='utf-8')
    return outcome


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=int, choices=[3, 10], default=3)
    parser.add_argument('--timeout-sec', type=int, default=150)
    parser.add_argument('--output', default='results/public-gazebo')
    args = parser.parse_args()
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    outcomes = [one_run(root, i, args.timeout_sec) for i in range(1, args.runs + 1)]
    passed = sum(r['status'] == 'PUBLIC_BASELINE_SMOKE_READY' for r in outcomes)
    status = ('PUBLIC_BASELINE_READONLY_PARTIAL' if passed == args.runs
              else 'BLOCKED_OR_INCONCLUSIVE')
    report = {'status': status, 'runs': args.runs,
              'passing_readonly_runs': passed, 'supervisor_verified': False,
              'nav2_goal_verified': False, 'gazebo_fault_verified': False,
              'gate_accepted': False}
    (root / 'summary.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    return 0 if status == 'PUBLIC_BASELINE_READONLY_PARTIAL' else 2


if __name__ == '__main__':
    raise SystemExit(main())
