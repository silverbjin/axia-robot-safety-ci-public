"""Bounded constant-label diagnostics for a private ROS fault JUnit.

Never print raw private test output, tracebacks, paths or source. This oracle
never promotes any failed fault or action run to PASS.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

_STOP = {
    'FAULT:scan_stale': 'SCAN_STALE',
    'FAULT:scan_invalid': 'SCAN_INVALID',
    'FAULT:cmd_stale': 'CMD_STALE',
    'FAULT:clock_stalled': 'CLOCK_STALLED',
    'HEALTH_BAD': 'HEALTH_BAD',
}
_SCAN = {
    'STALE_STAMP', 'FUTURE_STAMP', 'SCAN_TIMEOUT',
    'CLOCK_INVALID', 'INSUFFICIENT_COVERAGE',
}


def assess_fault_overlap(path):
    """Output only allowlisted cause/scan/deadline, without any private text."""
    base = {
        'diagnosis': 'NOT_AVAILABLE',
        'actual_stop_cause': 'UNAVAILABLE',
        'scan_fault_code': 'UNAVAILABLE',
        'callback_deadline': 'UNAVAILABLE',
        'gate_accepted': False,
    }
    try:
        root = ET.parse(Path(path)).getroot()
    except (OSError, ET.ParseError, ValueError, TypeError):
        return base
    values = []
    for element in root.iter():
        if element.tag in ('failure', 'error'):
            values.append((element.get('message') or '')[:100_000])
            values.append((element.text or '')[:100_000])
    if not values:
        return base
    raw = '\n'.join(values)
    match = re.search(r'\bunexpected stop cause:\s*(FAULT:[a-z_]+|HEALTH_BAD)\b', raw)
    stop = _STOP.get(match.group(1), 'UNKNOWN') if match else 'UNKNOWN'
    stamp = re.search(r"['\"]scan_fault_code['\"]\s*:\s*['\"]([A-Z_]+)['\"]", raw)
    scan_code = stamp.group(1) if stamp and stamp.group(1) in _SCAN else 'UNKNOWN'
    count = re.search(r"['\"]scan_callback_gaps_over_timeout['\"]\s*:\s*(\d+)\b", raw)
    if count:
        try:
            gap_value = int(count.group(1)[:10])
            deadline = 'OVERRUN_OBSERVED' if gap_value > 0 else 'NO_OVERRUN_OBSERVED'
        except ValueError:
            deadline = 'UNAVAILABLE'
    else:
        deadline = 'UNAVAILABLE'
    return {
        'diagnosis': 'PRIVATE_FAULT_ASSERTION_CLASSIFIED',
        'actual_stop_cause': stop,
        'scan_fault_code': scan_code,
        'callback_deadline': deadline,
        'gate_accepted': False,
    }


def assess_boot_health(path):
    """Whitelist boot readiness flags, never output ROS/private diagnostic text."""
    base = {'boot_diagnosis': 'NOT_AVAILABLE', 'boot_state': 'UNAVAILABLE',
            'clock_ok': 'UNAVAILABLE', 'scan_ok': 'UNAVAILABLE',
            'graph_ok': 'UNAVAILABLE', 'cm_ok': 'UNAVAILABLE',
            'action_ready': 'UNAVAILABLE', 'scan_fault': 'UNAVAILABLE',
            'scan_callback_gap': 'UNAVAILABLE'}
    try:
        root = ET.parse(Path(path)).getroot()
    except (OSError, ET.ParseError, ValueError, TypeError):
        return base
    failures = []
    for x in root.iter():
        if x.tag in ('failure', 'error'):
            failures.append((x.get('message') or '')[:100_000])
            failures.append((x.text or '')[:100_000])
    raw = '\n'.join(failures)
    if 'initial health never ready' not in raw:
        return base
    record = {**base, 'boot_diagnosis': 'BOOT_HEALTH_OBSERVED'}
    for key in ('clock_ok', 'scan_ok', 'graph_ok', 'cm_ok', 'action_ready'):
        match = re.search(r'\b' + key + r'=(True|False|None)\b', raw)
        if match:
            record[key] = match.group(1)
    state = re.search(r'\bstate=(BOOT_SAFE|NORMAL|LIMITED|PROTECTIVE_STOP|SW_STOP_LATCHED)\b',raw)
    if state:
        record['boot_state'] = state.group(1)
    fault = re.search(r'\bscan_fault=([A-Z_]+)\b',raw)
    if fault:
        record['scan_fault'] = fault.group(1) if fault.group(1) in _SCAN else 'UNKNOWN'
    gap = re.search(r'\bscan_callback_gap=(\d+(?:\.\d+)?)\b',raw)
    if gap:
        try:
            n = float(gap.group(1)[:20])
            record['scan_callback_gap'] = (
                'OVER_0P5' if n > 0.5 else 'NOT_OVER_0P5')
        except (ValueError, OverflowError):
            pass
    return record
