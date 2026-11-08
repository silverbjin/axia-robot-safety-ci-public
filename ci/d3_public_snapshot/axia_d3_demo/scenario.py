"""Guided Gazebo-only D3 classroom scene. No robot motion/Goal publisher.

The instructor initiates P1's approved navigation separately. This controller
moves only a simulation proxy, then (with a separate explicit approval) calls
P1's *existing* scan_drop fault service. It does not bypass P1 safety.
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

from .cli import PROXY, _model_file, build_spawn_command, validate_stage
from .contract import append_event, evaluate_events, read_events


class ScenarioBlocked(RuntimeError):
    pass


def validate_path(world, start, end):
    world, sx, sy = validate_stage(world, *start)
    _, ex, ey = validate_stage(world, *end)
    distance = math.hypot(ex - sx, ey - sy)
    if not (0.3 <= distance <= 3.0):
        raise ValueError('proxy path must be 0.3..3.0 m (checked in Gazebo first)')
    return world, (sx, sy), (ex, ey)


def build_pose_command(world, name, x, y):
    world, x, y = validate_stage(world, x, y)
    if name != PROXY:
        raise ValueError('only the D3 pedestrian proxy may be moved')
    # Gazebo Harmonic UserCommands: /world/<name>/set_pose (gz.msgs.Pose -> gz.msgs.Boolean)
    request = ('name: "' + PROXY + '" position: { x: ' + str(x) +
               ' y: ' + str(y) + ' z: 0 } orientation: { w: 1 }')
    return ['gz', 'service', '-s', '/world/' + world + '/set_pose',
            '--reqtype', 'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean',
            '--timeout', '5000', '--req', request]


def pose_ok(output):
    return bool(re.search(r'(?m)\bdata\s*:\s*true\b|^\s*true\s*$', output, re.IGNORECASE))


def fault_ok(output):
    return bool(re.search(r'\bsuccess\s*(?:=|:)\s*True\b', output, re.IGNORECASE))


def latest_live_state(events, now):
    """Most recent P1 state must be NORMAL, and recent odom must show motion."""
    states = [e for e in events if isinstance(e, dict) and e.get('kind') == 'p1_state']
    odoms = [e for e in events if isinstance(e, dict) and e.get('kind') == 'odom']
    if not states or not odoms:
        return False
    state, odom = states[-1], odoms[-1]
    if state.get('state') != 'NORMAL':
        return False
    if not all(type(e.get('ts_mono')) in (int, float) and math.isfinite(e['ts_mono'])
               for e in (state, odom)):
        return False
    if not (0 <= now - state['ts_mono'] <= 2.0 and 0 <= now - odom['ts_mono'] <= 2.0):
        return False
    v, w = odom.get('v'), odom.get('w')
    return (type(v) in (int, float) and math.isfinite(v) and abs(v) >= .05
            and type(w) in (int, float) and math.isfinite(w))


def dynamic_verified(events):
    """Stronger than legacy static D3 oracle; requires observed model movement."""
    result = evaluate_events(events)
    if result.status != 'DEMO_OBSERVED':
        return result.status
    visible = None
    movement = None
    fault = None
    for e in events:
        if e['kind'] == 'obstacle_visible' and visible is None:
            visible = e['ts_mono']
        elif e['kind'] == 'obstacle_moved' and e.get('name') == PROXY and movement is None:
            movement = e['ts_mono']
        elif e['kind'] == 'fault_status' and e.get('mode') == 'DROP_SCAN' and fault is None:
            fault = e['ts_mono']
    return 'DEMO_OBSERVED' if (visible is not None and movement is not None and fault is not None
                                and visible <= movement < fault) else 'INCONCLUSIVE'


class ScenarioDriver:
    def __init__(self, *, runner=None, input_fn=input, evidence_reader=read_events,
                 clock=time.monotonic, sleep=time.sleep, out=print):
        self.runner = runner or subprocess.run
        self.input_fn = input_fn
        self.evidence_reader = evidence_reader
        self.clock = clock
        self.sleep = sleep
        self.out = out

    def _call(self, command, *, timeout=20):
        try:
            res = self.runner(command, text=True, capture_output=True, timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ScenarioBlocked('external command failed: ' + str(exc)) from exc
        if res.returncode:
            raise ScenarioBlocked('command failed (' + str(res.returncode) + '): ' +
                                  str(res.stderr or res.stdout)[-800:])
        return str(res.stdout or '') + '\n' + str(res.stderr or '')

    def _wait_for_movement(self, evidence, seconds):
        until = self.clock() + seconds
        while self.clock() < until:
            if latest_live_state(self.evidence_reader(evidence), self.clock()):
                return True
            self.sleep(.1)
        return False

    def preview(self, world, start, end, *, steps=8, duration_s=4., acknowledge_sim=False):
        """Show human-shaped proxy moving even before Nav2 is ready.

        No Fault, ROS publisher, P1 command, Goal or Reset. A separate
        preview is deliberately not eligible as D3 acceptance evidence.
        """
        world, start, end = validate_path(world, start, end)
        if not acknowledge_sim:
            return 'BLOCKED_SIM_APPROVAL'
        if not (type(steps) is int and 4 <= steps <= 20 and
                type(duration_s) in (int,float) and 2. <= duration_s <= 15.):
            raise ValueError('preview steps 4..20 / duration 2..15 required')
        if not os.environ.get('GZ_PARTITION', '').startswith('axia_d3_'):
            return 'BLOCKED_GZ_PARTITION'
        services = self._call(['gz', 'service', '-l'], timeout=10)
        if '/world/' + world + '/set_pose' not in services or '/world/' + world + '/create' not in services:
            return 'BLOCKED_WORLD_SERVICES'
        self._call(build_spawn_command(world, *start, _model_file()), timeout=40)
        self.out('[PREVIEW] Proxy created; moving from ' + str(start) + ' to ' + str(end))
        for step in range(1, steps+1):
            x = start[0] + step / steps * (end[0] - start[0])
            y = start[1] + step / steps * (end[1] - start[1])
            output = self._call(build_pose_command(world, PROXY, x, y), timeout=9)
            if not pose_ok(output):
                return 'BLOCKED_PROXY_POSE_REJECTED'
            self.out(f'[PREVIEW_MOVE] {step}/{steps}: ({x:.2f}, {y:.2f})')
            self.sleep(duration_s/steps)
        self.out('[PREVIEW] Motion completed. No Scan Fault or P1 motion was requested.')
        self.out('[NOTE] Model remains in Gazebo; remove it before starting live scenario.')
        return 'PREVIEW_MOVED'

    def run(self, *, world, start, end, evidence, dry_run=False,
            acknowledge_sim=False, acknowledge_fault=False, ready_timeout_s=30.0,
            duration_s=4.0, steps=8, operator_choice=None):
        world, start, end = validate_path(world, start, end)
        if dry_run:
            self.out('[PLAN] Only Gazebo proxy will move; P1 provides goal, stop and fault service')
            self.out('[PLAN] Steps: ready→spawn→visible approval→move→explicit scan_drop→stop/diag→operator')
            return 'PLAN_ONLY'
        if not acknowledge_sim:
            return 'BLOCKED_SIM_APPROVAL'
        if not acknowledge_fault:
            return 'BLOCKED_FAULT_APPROVAL'
        if not (isinstance(steps, int) and 4 <= steps <= 20 and 2.0 <= duration_s <= 15.0):
            raise ValueError('steps 4..20 and duration 2..15 seconds only')
        if not os.environ.get('GZ_PARTITION', '').startswith('axia_d3_'):
            return 'BLOCKED_GZ_PARTITION'
        if not os.environ.get('ROS_DOMAIN_ID', '').isdecimal():
            return 'BLOCKED_ROS_DOMAIN'
        evidence = Path(evidence).expanduser()
        if evidence.is_symlink():
            return 'BLOCKED_EVIDENCE_SYMLINK'
        self.out('[WAIT] P1 must already be NORMAL and odom must indicate movement')
        if not self._wait_for_movement(evidence, ready_timeout_s):
            return 'BLOCKED_NO_LIVE_MOTION'
        prior_fault = [e for e in self.evidence_reader(evidence) if e.get('kind') == 'fault_status']
        if prior_fault and prior_fault[-1].get('mode') != 'NORMAL':
            return 'BLOCKED_FAULT_ALREADY_ACTIVE'
        services = self._call(['gz', 'service', '-l'], timeout=10)
        if '/world/' + world + '/set_pose' not in services or '/world/' + world + '/create' not in services:
            return 'BLOCKED_WORLD_SERVICES'
        self._call(build_spawn_command(world, *start, _model_file()), timeout=40)
        append_event(evidence, 'stage_spawned', world=world, name=PROXY)
        self.out('[GAZEBO] Spawned proxy at ' + str(start))
        if self.input_fn('Inspect Gazebo: confirm proxy visible (type YES-VISIBLE): ').strip() != 'YES-VISIBLE':
            return 'BLOCKED_VISUAL_NOT_CONFIRMED'
        append_event(evidence, 'obstacle_visible', name=PROXY)
        fault_requested = False
        for step in range(1, steps + 1):
            # Abort before calling fault if the P1 already stopped for an unrelated hazard.
            states = [e for e in self.evidence_reader(evidence) if e.get('kind') == 'p1_state']
            if not fault_requested and states and states[-1].get('state') != 'NORMAL':
                return 'BLOCKED_P1_STOPPED_BEFORE_FAULT'
            fraction = step / steps
            x = start[0] + fraction * (end[0] - start[0])
            y = start[1] + fraction * (end[1] - start[1])
            out = self._call(build_pose_command(world, PROXY, x, y), timeout=9)
            if not pose_ok(out):
                return 'BLOCKED_PROXY_POSE_REJECTED'
            append_event(evidence, 'obstacle_moved', name=PROXY, step=step)
            self.out(f'[MOVE] {step}/{steps}: ({x:.2f},{y:.2f})')
            if step == 2:
                # Existing P1 Fault Injector, ONLY after explicit user approval.
                # Fail closed on missing/disabled status and wrong source state.
                status = [e for e in self.evidence_reader(evidence) if e.get('kind') == 'fault_status']
                if not status or status[-1].get('enabled') is not True:
                    return 'BLOCKED_FAULT_DISABLED'
                out = self._call(['ros2', 'service', 'call', '/axia/fault/scan_drop',
                                  'std_srvs/srv/Trigger', '{}'], timeout=12)
                if not fault_ok(out):
                    return 'BLOCKED_FAULT_SERVICE_REJECTED'
                fault_requested = True
                self.out('[FAULT] Existing P1 scan_drop service accepted')
            self.sleep(duration_s / steps)
        if not fault_requested:
            return 'BLOCKED_FAULT_NOT_SENT'
        self.out('[WAIT] Observing fault_status + PROTECTIVE_STOP + ERROR diagnostic + odom stop...')
        until = self.clock() + 20.0
        while self.clock() < until:
            events = self.evidence_reader(evidence)
            if any(e.get('kind') == 'p1_state' and e.get('state') == 'PROTECTIVE_STOP' for e in events):
                # Static oracle excludes operator decision; do not claim success yet.
                if evaluate_events(events).missing == ('OPERATOR_HOLD_OR_END',):
                    break
            self.sleep(.2)
        else:
            return 'INCONCLUSIVE_STOP_OR_DIAGNOSTICS'
        if operator_choice is None:
            operator_choice = self.input_fn('Stop observed. Choose HOLD or END (never auto-rearm): ').strip()
        if operator_choice not in ('HOLD', 'END'):
            return 'BLOCKED_OPERATOR_DECISION'
        append_event(evidence, 'operator_decision', choice=operator_choice)
        result = dynamic_verified(self.evidence_reader(evidence))
        self.out('[RESULT] ' + result + ' (education-only, not E-Stop certification)')
        return result


def main(argv=None):
    ap = argparse.ArgumentParser(description='AXIA D3 guided moving-proxy scene (SIM ONLY)')
    ap.add_argument('--mode', choices=('preview','live'), default='preview')
    ap.add_argument('--world', required=True)
    for name in ('start-x', 'start-y', 'end-x', 'end-y'):
        ap.add_argument('--' + name, type=float, required=True)
    ap.add_argument('--evidence')
    ap.add_argument('--duration-s', type=float, default=4.0)
    ap.add_argument('--steps', type=int, default=8)
    ap.add_argument('--ready-timeout-s', type=float, default=30.)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--ack-sim-only', action='store_true')
    ap.add_argument('--ack-fault', action='store_true')
    ap.add_argument('--operator-choice', choices=('HOLD', 'END'))
    p = ap.parse_args(argv)
    driver = ScenarioDriver()
    try:
        if p.mode == 'preview':
            if p.ack_fault:
                raise ValueError('--ack-fault is only for live mode')
            result = driver.preview(world=p.world, start=(p.start_x, p.start_y),
                end=(p.end_x,p.end_y), steps=p.steps, duration_s=p.duration_s,
                acknowledge_sim=p.ack_sim_only)
        else:
            if not p.evidence:
                raise ValueError('--evidence required in live mode')
            result = driver.run(world=p.world, start=(p.start_x, p.start_y),
                end=(p.end_x, p.end_y), evidence=p.evidence,
                dry_run=p.dry_run, acknowledge_sim=p.ack_sim_only,
                acknowledge_fault=p.ack_fault, duration_s=p.duration_s,
                steps=p.steps, ready_timeout_s=p.ready_timeout_s,
                operator_choice=p.operator_choice)
    except (ValueError, ScenarioBlocked, EOFError, KeyboardInterrupt) as ex:
        print('[BLOCKED] ' + str(ex), file=sys.stderr)
        return 2
    print('[SCENARIO] ' + result)
    return 0 if result in ('PLAN_ONLY','PREVIEW_MOVED','DEMO_OBSERVED') else 3


if __name__ == '__main__':
    raise SystemExit(main())