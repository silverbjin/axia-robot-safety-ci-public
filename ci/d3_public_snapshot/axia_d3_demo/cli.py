"""Operator-controlled Gazebo proxy stage + ROS-free evidence verification.

No Nav2 Goal, safety Start/Reset/Rearm, Fault Injector or Twist calls exist here.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from .contract import append_event, evaluate_events, read_events

PROXY = 'd3_pedestrian_proxy'
WORLD = re.compile(r'^[A-Za-z][A-Za-z0-9_]{0,39}$')


def validate_stage(world, x, y):
    if not isinstance(world, str) or not WORLD.fullmatch(world):
        raise ValueError('world must be a simple Gazebo world identifier')
    try:
        xx, yy = float(x), float(y)
    except (ValueError, TypeError) as ex:
        raise ValueError('x/y must be finite coordinates') from ex
    if not (math.isfinite(xx) and math.isfinite(yy) and abs(xx) <= 15 and abs(yy) <= 15):
        raise ValueError('x/y must be finite within the classroom sandbox [-15,15]')
    return world, xx, yy


def _format(v):
    return str(float(v))


def build_spawn_command(world, x, y, sdf_file):
    world, x, y = validate_stage(world, x, y)
    return ['ros2', 'run', 'ros_gz_sim', 'create', '-world', world,
            '-file', str(sdf_file), '-name', PROXY,
            '-x', _format(x), '-y', _format(y), '-z', '0.0']


def _model_file():
    try:
        from ament_index_python.packages import get_package_share_directory
        path = Path(get_package_share_directory('axia_d3_demo')) / 'models/pedestrian_proxy.sdf'
        if path.is_file():
            return path
    except (ImportError, LookupError):
        pass
    path = Path(__file__).resolve().parent.parent / 'models/pedestrian_proxy.sdf'
    if not path.is_file():
        raise ValueError('D3 SDF model file missing')
    return path


def _print_verdict(events):
    v = evaluate_events(events)
    print(json.dumps({'status': v.status, 'missing': v.missing,
                      'certified_estop': False, 'contact_free_proven': False}))
    return v


def cli_main(args=None):
    parser = argparse.ArgumentParser(description='AXIA D3 simulation-only classroom event tool')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('plan', help='Print safe manual scenario; no ROS command sent')
    stage = sub.add_parser('stage', help='Spawn a static human-shaped obstacle in Gazebo (manual opt-in)')
    for name in ('world', 'x', 'y', 'evidence'):
        stage.add_argument('--' + name, required=True)
    stage.add_argument('--ack-sim-only', action='store_true')
    confirm = sub.add_parser('confirm', help='Confirm obstacle was actually seen in GUI')
    confirm.add_argument('--evidence', required=True)
    confirm.add_argument('--ack-visible', action='store_true')
    dec = sub.add_parser('decision', help='Record operator HOLD or END, no ROS service')
    dec.add_argument('--evidence', required=True)
    dec.add_argument('--choice', choices=('HOLD', 'END'), required=True)
    dec.add_argument('--ack-operator', action='store_true')
    verify = sub.add_parser('verify', help='Offline check ordered evidence (not P1 acceptance)')
    verify.add_argument('--evidence', required=True)
    try:
        p = parser.parse_args(args)
        if p.command == 'plan':
            print('D3 PLAN: prior-approved verified P1 goal + robot moving in isolated simulator')
            print('STAGE_PROXY -> OPERATOR_VISUAL_CONFIRM -> SCAN_DROP (P1 service MANUAL ONLY)')
            print('-> P1 PROTECTIVE_STOP -> DIAGNOSTICS ERROR/STALE -> ODOM STOP >=1s')
            print('-> OPERATOR HOLD/END; no automated Goal/Fault/Reset/Rearm')
            return 0
        evidence = Path(p.evidence).expanduser()
        if p.command == 'stage':
            if not p.ack_sim_only:
                raise ValueError('must explicitly pass --ack-sim-only; no real robots')
            partition = os.environ.get('GZ_PARTITION', '')
            if not partition.startswith('axia_d3_'):
                raise ValueError('isolated GZ_PARTITION must start with axia_d3_')
            dom = os.environ.get('ROS_DOMAIN_ID', '')
            if not (dom.isdecimal() and 0 <= int(dom) <= 232):
                raise ValueError('valid isolated ROS_DOMAIN_ID required')
            cmd = build_spawn_command(p.world, p.x, p.y, _model_file())
            print('Gazebo spawning proxy; world/coordinates must be checked visually by operator')
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=45, check=False)
            if completed.returncode != 0:
                print((completed.stderr or completed.stdout)[-1500:], file=sys.stderr)
                raise ValueError('ros_gz_sim create failed; stage not recorded')
            append_event(evidence, 'stage_spawned', world=p.world, name=PROXY)
            print('STAGE_REQUEST_ACCEPTED: inspect Gazebo GUI; next run confirm --ack-visible')
            return 0
        if p.command == 'confirm':
            if not p.ack_visible:
                raise ValueError('operator must verify Gazebo proxy visually and pass --ack-visible')
            events = read_events(evidence)
            if not any(isinstance(e, dict) and e.get('kind') == 'stage_spawned'
                       and e.get('name') == PROXY for e in events):
                raise ValueError('no successful Gazebo stage request in evidence')
            append_event(evidence, 'obstacle_visible', name=PROXY)
            print('VISUAL_CONFIRMATION_RECORDED (manual claim, not contact sensor proof)')
            return 0
        if p.command == 'decision':
            if not p.ack_operator:
                raise ValueError('operator must explicitly pass --ack-operator')
            events = read_events(evidence)
            candidate = {'ts_mono': time.monotonic(), 'kind': 'operator_decision', 'choice': p.choice}
            if evaluate_events([*events, candidate]).status != 'DEMO_OBSERVED':
                raise ValueError('cannot make final decision yet: observed stop/diagnostics evidence missing')
            append_event(evidence, 'operator_decision', choice=p.choice)
            print('OPERATOR_DECISION_RECORDED: no Reset/Rearm/Goal command sent')
            return 0
        if p.command == 'verify':
            result = _print_verdict(read_events(evidence))
            return 0 if result.status == 'DEMO_OBSERVED' else 2 if result.status == 'INVALID_EVIDENCE' else 3
    except (OSError, ValueError, subprocess.TimeoutExpired) as ex:
        print('[BLOCKED] ' + str(ex), file=sys.stderr)
        return 2
    return 2


def main():
    raise SystemExit(cli_main())


if __name__ == '__main__':
    main()
