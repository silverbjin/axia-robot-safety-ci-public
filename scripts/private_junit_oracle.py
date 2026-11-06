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
