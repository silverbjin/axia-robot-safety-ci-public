#!/usr/bin/env python3
"""One official Jazzy/Gazebo no-goal run to check a redacted Nav2 log oracle.

Never emits raw private ROS logs, source, rosbag2, or session identifiers.
This is a diagnostic experiment, not an acceptance or stop/E-Stop test.
"""
from pathlib import Path
import argparse
import json
import os
import tempfile
import sys

from private_nav2_phase_oracle_v2 import classify_nav2_shutdown_phase


def tail_private_log(path: Path, *, max_bytes: int = 12_000_000) -> tuple[str, str]:
    if not isinstance(max_bytes, int) or max_bytes < 1 or max_bytes > 12_000_000:
        return '', 'INVALID_BOUND'
    try:
        with Path(path).open('rb') as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size-max_bytes))
            content = f.read(max_bytes)
        return content.decode('utf-8', errors='replace'), ('TAIL_READ' if size > max_bytes else 'FULL_READ')
    except OSError:
        return '', 'LOG_MISSING'


def run(private_root: Path) -> int:
    import private_ci_bridge as bridge
    blocked = True
    summary = {'status': 'BLOCKED', 'gate_accepted': False,
               'goal_sent': False, 'fault_injected': False, 'certified_estop_verified': False}
    try:
        root = bridge.validate_private_commit(private_root)
        env = bridge.private_runtime_env(root, os.environ)
        with tempfile.TemporaryDirectory(prefix='axia_nav2_phase_private_',
                                         dir=os.environ.get('RUNNER_TEMP') or None) as temp:
            tmp = Path(temp)
            setup = tmp / 'upstream' / 'install' / 'setup.bash'
            data = tmp / 'single'
            env.update(AXIA_NAV2_LIFECYCLE_OVERLAY_SETUP=str(setup),
                       AXIA_NAV2_USE_COMPOSITION='False',
                       AXIA_T08_PRE_GOAL_NO_GOAL_CI='YES_READ_ONLY',
                       AXIA_T08_R01_READ_ONLY_BINDING='NO',
                       AXIA_SMOKE_RESULTS_DIR=str(data),
                       ROS_DOMAIN_ID='171',
                       GZ_PARTITION='axia_nav2_phase_smoke1_no_goal_' + str(os.environ.get('GITHUB_RUN_ID','local')))
            bridge.scrubbed_run('UPSTREAM_OVERLAY',
                ['bash', 'scripts/build_official_nav2_lifecycle_overlay.sh', str(tmp/'upstream')],
                root, env, tmp, 1200)
            try:
                bridge.scrubbed_run('NAV2_PHASE_READONLY_ONE',
                    ['bash', 'scripts/run_p1_gazebo_smoke_ci.sh'],
                    root, env, tmp, 650)
                blocked = False
            except bridge.GateBlocked:
                blocked = True
            text, read_status = tail_private_log(data/'launch.log')
            observation = classify_nav2_shutdown_phase(text)
            summary['log_read'] = read_status
            summary['navigation'] = observation['navigation']
            summary['localization'] = observation['localization']
            observed = any(observation[name]['shutdown_started']
                           for name in ('navigation','localization'))
            summary['status'] = ('DIAGNOSTIC_OBSERVED' if observed and not blocked
                                 else 'BLOCKED')
            print('AXIA_NAV2_PHASE_SMOKE1 ' + json.dumps(summary,sort_keys=True),flush=True)
            return 0 if observed and not blocked else 3
    except bridge.GateBlocked:
        summary['reason']='PRIVATE_STAGE_BLOCKED'
    except Exception:
        summary['reason']='UNCLASSIFIED_PRIVATE_ERROR'
    print('AXIA_NAV2_PHASE_SMOKE1 '+json.dumps(summary,sort_keys=True),flush=True)
    return 3


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--private-root',type=Path,required=True)
    sys.exit(run(p.parse_args().private_root))
