"""ROS-free educational D3 evidence contract. No motion/control authority.

DEMO_OBSERVED means timestamped observations satisfy a classroom scenario.
It does NOT certify collision avoidance or a hardware emergency stop.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time

FIELDS = {
    'p1_state': ('state', 'scan_fault_code'),
    'odom': ('v', 'w'),
    'stage_spawned': ('world', 'name'),
    'obstacle_visible': ('name',),
    'obstacle_moved': ('name', 'step'),
    'fault_status': ('mode', 'enabled'),
    'diagnostic': ('name', 'level'),
    'operator_decision': ('choice',),
}

@dataclass(frozen=True)
class Verdict:
    status: str
    missing: tuple[str, ...] = ()
    certified_estop: bool = False
    contact_free_proven: bool = False


def _is_time(v):
    return type(v) in (float, int) and math.isfinite(v) and v >= 0


def append_event(path, kind, **fields):
    """Append one allowlisted JSONL event, atomically for small records.

    Unknown fields (notably Goal IDs and raw private P1 JSON) are discarded.
    """
    if kind not in FIELDS:
        raise ValueError('unsupported D3 evidence kind')
    item = {'ts_mono': time.monotonic(), 'ts_utc': datetime.now(timezone.utc).isoformat(), 'kind': kind}
    for k in FIELDS[kind]:
        if k in fields:
            value = fields[k]
            if type(value) in (str, bool, int, float) or value is None:
                if type(value) is float and not math.isfinite(value):
                    continue
                item[k] = value
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (json.dumps(item, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode()
    fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)
    return item


def read_events(path):
    """Return an invalid sentinel on broken input, never fabricate success."""
    p = Path(path).expanduser()
    if not p.is_file():
        return []
    try:
        if p.stat().st_size > 2_000_000:
            return [{'kind': 'invalid_evidence', 'ts_mono': 0.0}]
        lines = p.read_text(encoding='utf-8').splitlines()
        if len(lines) > 20000:
            return [{'kind': 'invalid_evidence', 'ts_mono': 0.0}]
        return [json.loads(line) for line in lines if line.strip()]
    except (OSError, UnicodeError, ValueError, TypeError):
        return [{'kind': 'invalid_evidence', 'ts_mono': 0.0}]


def evaluate_events(events):
    """Verify sequence using monotonic timestamps; NOT a physical safety oracle."""
    previous = -1.0
    # Use tuples rather than class hierarchies for a minimal transparent FSM.
    phase = 0  # 0 pre-motion, 1 moving, 2 obstacle, 3 scan fault, 4 stopped
    last_normal = None
    last_moving = None
    stage_pending = False
    stop_ts = None
    zero_since = None
    has_diag = False
    observed_stillness = False
    final = False
    stopped_before_fault = False
    if not isinstance(events, list):
        return Verdict('INVALID_EVIDENCE', ('NOT_LIST',))
    for e in events:
        if not isinstance(e, dict) or e.get('kind') not in FIELDS or not _is_time(e.get('ts_mono')):
            return Verdict('INVALID_EVIDENCE', ('MALFORMED_EVENT',))
        t = e['ts_mono']
        if t < previous:
            return Verdict('INVALID_EVIDENCE', ('NON_MONOTONIC',))
        previous = t
        k = e['kind']
        if k == 'p1_state':
            if e.get('state') == 'NORMAL' and phase == 0:
                last_normal = t
            if e.get('state') == 'PROTECTIVE_STOP' and phase in (1, 2):
                stopped_before_fault = True
            if (e.get('state') == 'PROTECTIVE_STOP' and phase == 3):
                phase = 4
                stop_ts = t
                zero_since = None
        elif k == 'odom':
            v, w = e.get('v'), e.get('w')
            if not (type(v) in (float, int) and type(w) in (float, int)
                    and math.isfinite(v) and math.isfinite(w)):
                return Verdict('INVALID_EVIDENCE', ('INVALID_ODOM',))
            if phase <= 1 and abs(v) >= .05 and last_normal is not None and t-last_normal <= 2.0:
                phase = 1
                last_moving = t
            if phase == 4 and t >= stop_ts:
                if abs(v) < .03 and abs(w) < .05:
                    if zero_since is None:
                        zero_since = t
                    if t-zero_since >= 1.0:
                        observed_stillness = True
                else:
                    zero_since = None
                    observed_stillness = False
        elif k == 'stage_spawned':
            # A completed spawn command while moving is only a candidate.
            # Operator may confirm visual placement later, after inspecting GUI.
            if (phase == 1 and e.get('name') == 'd3_pedestrian_proxy'
                    and last_moving is not None and t-last_moving <= 5.0):
                stage_pending = True
        elif k == 'obstacle_visible':
            if phase == 1 and stage_pending and e.get('name') == 'd3_pedestrian_proxy':
                phase = 2
        elif k == 'fault_status':
            if phase == 2 and e.get('mode') == 'DROP_SCAN' and e.get('enabled') is True:
                phase = 3
        elif k == 'diagnostic':
            level = e.get('level')
            if (phase >= 3 and e.get('name') == 'AXIA/P1/SafetySupervisor'
                    and type(level) is int and level in (2, 3)):
                has_diag = True
        elif k == 'operator_decision':
            if (phase == 4 and has_diag and observed_stillness
                    and e.get('choice') in ('HOLD', 'END')):
                final = True
    if stopped_before_fault:
        return Verdict('INCONCLUSIVE', ('STOP_PRECEDED_SCAN_FAULT',))
    if final:
        return Verdict('DEMO_OBSERVED')
    missing = (
        'MOVING_BEFORE_INTRUSION' if phase == 0 else
        'OBSTACLE_VISIBLE' if phase == 1 else
        'SCAN_DROP_ACTIVE' if phase == 2 else
        'P1_PROTECTIVE_STOP' if phase == 3 else
        'DIAGNOSTICS_ERROR' if not has_diag else
        'ODOM_STOP_HELD' if not observed_stillness else
        'OPERATOR_HOLD_OR_END'
    )
    return Verdict('INCONCLUSIVE', (missing,))