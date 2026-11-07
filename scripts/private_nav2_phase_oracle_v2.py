"""Redacted Nav2 lifecycle phase observer for sealed private Gazebo logs.

This parses plain text INSIDE an ephemeral private runner only; it emits
allowlisted transition/node labels. A completed lifecycle log event is an
observation, not a safety or acceptance decision.
"""
from __future__ import annotations
import re

_NODE_NAMES = frozenset({
    'amcl', 'map_server', 'controller_server', 'planner_server',
    'smoother_server', 'behavior_server', 'bt_navigator',
    'waypoint_follower', 'velocity_smoother', 'collision_monitor',
    'route_server', 'docking_server',
})
_MANAGERS = ('navigation', 'localization')
_EVENT = re.compile(r'^(Deactivating|Cleaning up|Shutting down) ([A-Za-z_0-9]+)\s*$')


def _blank():
    return {'shutdown_started': False, 'shutdown_completed': False,
            'last_phase': 'NOT_OBSERVED', 'last_node': 'NOT_OBSERVED',
            'transitions': 0}


def classify_nav2_shutdown_phase(log_text: str) -> dict:
    """Return only bounded, allowlisted fields, never raw log data."""
    rows = {name: _blank() for name in _MANAGERS}
    # Limit private input even when a child process goes into a logging loop.
    if not isinstance(log_text, str):
        log_text = ''
    for raw in log_text[-12_000_000:].splitlines()[-250_000:]:
        # ROS logger names are bracketed. Ignore non-manager messages and
        # arbitrary untrusted source text outside logger brackets.
        fields = re.findall(r'\[([^\]\n]{1,120})\]', raw)
        # ROS launch prefixes can add a process suffix (-pid), while the
        # rclcpp logger may be namespace-qualified. Neither form is private
        # data: recognize only these two fixed manager identifiers.
        managers = [name for name in _MANAGERS
                    if any(re.search(r'(?:^|[./])lifecycle_manager_' + name
                                     + r'(?:-\d+)?$', field) for field in fields)]
        if not managers:
            continue
        for manager in managers:
            event = rows[manager]
            # Strip terminal colour sequences without echoing source text.
            message = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '',
                             raw.rsplit(']', 1)[-1]).lstrip(' :\t')
            if message.startswith('Shutting down managed nodes...'):
                rows[manager] = event = _blank()
                event['shutdown_started'] = True
                event['last_phase'] = 'BEFORE_TRANSITION'
                continue
            if not event['shutdown_started']:
                continue
            if message.startswith('Managed nodes have been shut down'):
                event['shutdown_completed'] = True
                event['last_phase'] = 'FINALIZED'
                continue
            if message.startswith('Deactivate, cleanup, and shutdown nodes'):
                continue
            match = _EVENT.match(message)
            if match:
                phase, node = match.groups()
                event['last_phase'] = {
                    'Deactivating': 'DEACTIVATE',
                    'Cleaning up': 'CLEANUP',
                    'Shutting down': 'SHUTDOWN',
                }[phase]
                event['last_node'] = node if node in _NODE_NAMES else 'UNRECOGNIZED'
                event['transitions'] = min(10000, event['transitions'] + 1)
    return {'navigation': rows['navigation'], 'localization': rows['localization'],
            'gate_accepted': False}
