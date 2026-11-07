#!/usr/bin/env python3
"""Protected CI-only R01 real ROS receipt binding, strictly NO-GOAL.

Public source contains only a fail-closed evidence contract. ROS raw logs,
private instructor code, rosbag2 and session identifiers remain on the
private runner, never in public stdout or uploaded artifacts.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import tempfile
import time

RECEIPTS = ('corridor', 'pre_goal_gate', 'graph', 'supervisor_prestart')
FORBIDDEN = ('start_ack.json', 'nav2_goal.log', 'fault.log', 'live_trace.jsonl')

class ReceiptBlocked(ValueError):
    """Only allowlisted error enums, never raw private messages."""


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('bad JSON shape')
        return data
    except (OSError, ValueError, TypeError, UnicodeError):
        raise ReceiptBlocked('R01_RECEIPT_MISSING') from None


def verify_receipts(root: Path, *, expected_sha: str, rounds: int, now_ns: int) -> dict:
    """Prove capture-time, same-run consistency; never grant Goal authority."""
    if not (rounds == 3 and isinstance(expected_sha, str)
            and len(expected_sha) == 40 and type(now_ns) is int and now_ns > 0):
        raise ReceiptBlocked('R01_INPUT_INVALID')
    seen_ids, seen_sessions = set(), set()
    for i in range(1, rounds + 1):
        folder = Path(root) / ('run_' + str(i))
        if not folder.is_dir() or folder.is_symlink():
            raise ReceiptBlocked('R01_RECEIPT_MISSING')
        if any((folder / name).exists() for name in FORBIDDEN):
            raise ReceiptBlocked('R01_FORBIDDEN_MUTATION_EVIDENCE')
        identity = None
        timestamps = []
        for name in RECEIPTS:
            data = _read(folder / (name + '.json'))
            record = data.get('provenance')
            if not isinstance(record, dict):
                raise ReceiptBlocked('R01_RECEIPT_MISSING')
            if record.get('source_sha') != expected_sha:
                raise ReceiptBlocked('R01_SOURCE_MISMATCH')
            if record.get('ros_domain_id') != str(170+i):
                raise ReceiptBlocked('R01_DOMAIN_MISMATCH')
            for key in ('run_id', 'session_id', 'gz_partition'):
                value = record.get(key)
                if (not isinstance(value, str) or len(value) < 8 or len(value) > 128):
                    raise ReceiptBlocked('R01_SESSION_MISMATCH')
            got = (record['run_id'], record['session_id'], record['gz_partition'])
            if identity is None:
                identity = got
            elif got != identity:
                raise ReceiptBlocked('R01_SESSION_MISMATCH')
            ts = record.get('captured_monotonic_ns')
            if type(ts) is not int or ts <= 0 or ts > now_ns:
                raise ReceiptBlocked('R01_CAPTURE_TIME_INVALID')
            timestamps.append(ts)
            # Source graph/corridor producers omit this field; NEVER accept
            # a producer asserting true, but do not synthesize nonexistent data.
            if data.get('gate_accepted') is True:
                raise ReceiptBlocked('R01_UNSAFE_GATE_FLAG')
            if name in ('pre_goal_gate', 'supervisor_prestart') and data.get('gate_accepted') is not False:
                raise ReceiptBlocked('R01_UNSAFE_GATE_FLAG')
            if name == 'corridor' and data.get('result') != 'CORRIDOR_GRID_READY':
                raise ReceiptBlocked('R01_READY_EVIDENCE_MISSING')
            if name == 'pre_goal_gate' and not (
                data.get('status') == 'PRE_GOAL_READY'
                and data.get('pending_goal_only') is True
                and data.get('goal_sent') is False):
                raise ReceiptBlocked('R01_READY_EVIDENCE_MISSING')
            if name == 'graph' and not (
                isinstance(data.get('verdict'), dict)
                and data['verdict'].get('passed') is True
                and data['verdict'].get('reasons') == []):
                raise ReceiptBlocked('R01_READY_EVIDENCE_MISSING')
            if name == 'supervisor_prestart':
                received = data.get('last_state_received_mono')
                if (data.get('status') != 'SUPERVISOR_PRESTART_READY'
                        or data.get('authorized_goal') is not False):
                    raise ReceiptBlocked('R01_READY_EVIDENCE_MISSING')
                if (type(received) not in (float,int) or received <= 0
                        or abs(int(received * 1_000_000_000) - ts) > 1000):
                    raise ReceiptBlocked('R01_SUPERVISOR_RX_TIME_MISMATCH')
        if timestamps != sorted(timestamps):
            raise ReceiptBlocked('R01_RECEIPT_ORDER_INVALID')
        if identity[0] in seen_ids or identity[1] in seen_sessions:
            raise ReceiptBlocked('R01_SESSION_MISMATCH')
        seen_ids.add(identity[0])
        seen_sessions.add(identity[1])
    return {'status':'R01_READONLY_RECEIPTS_VERIFIED','rounds':rounds,
            'receipt_count':rounds*len(RECEIPTS),
            'goal_sent':False,'gate_accepted':False,'certified_estop_verified':False}


def run(private_root: Path) -> int:
    import private_ci_bridge as b
    try:
        root = b.validate_private_commit(private_root)
        env = b.private_runtime_env(root, os.environ)
        env['AXIA_T08_R01_READ_ONLY_BINDING'] = 'YES'
        env['GITHUB_SHA'] = b.PIN
        with tempfile.TemporaryDirectory(prefix='axia_p1_r01_private_',
                                         dir=os.environ.get('RUNNER_TEMP') or None) as temp:
            tmp = Path(temp)
            overlay = tmp / 'official-nav2-overlay'
            b.scrubbed_run('UPSTREAM_OVERLAY',
                          ['bash','scripts/build_official_nav2_lifecycle_overlay.sh',str(overlay)],
                          root,env,tmp,1200)
            env['AXIA_NAV2_LIFECYCLE_OVERLAY_SETUP'] = str(overlay/'install/setup.bash')
            env['AXIA_NAV2_USE_COMPOSITION'] = 'False'
            env['AXIA_P1_PRELOCAL_RUNS'] = '3'
            dest = tmp / 'private-r01-readonly-3'
            env['AXIA_P1_PRELOCAL_ROOT'] = str(dest)
            try:
                b.scrubbed_run('R01_LIVE_GAZEBO_READONLY',
                    ['bash','scripts/run_p1_preacceptance_stability.sh'],
                    root,env,tmp,3000)
            finally:
                b.private_evidence_diagnostics(dest,3)
            b.verify_gazebo_report(dest,3)
            verdict = verify_receipts(dest,expected_sha=b.PIN,rounds=3,
                                      now_ns=time.monotonic_ns())
            print('AXIA_PRIVATE_R01 '+json.dumps(verdict,sort_keys=True),flush=True)
        return 0
    except ReceiptBlocked as exc:
        # Error values originate only from fixed literals in this file.
        print('AXIA_PRIVATE_R01 '+json.dumps({
            'status':'BLOCKED','reason':str(exc),'gate_accepted':False,
            'goal_sent':False},sort_keys=True),flush=True)
        return 3
    except b.GateBlocked:
        print('AXIA_PRIVATE_R01 '+json.dumps({
            'status':'BLOCKED','reason':'PRIVATE_BRIDGE_STAGE_BLOCKED',
            'gate_accepted':False,'goal_sent':False},sort_keys=True),flush=True)
        return 3
    except Exception:
        print('AXIA_PRIVATE_R01 '+json.dumps({
            'status':'BLOCKED','reason':'R01_UNCLASSIFIED_PRIVATE_ERROR',
            'gate_accepted':False,'goal_sent':False},sort_keys=True),flush=True)
        return 3


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--private-root',type=Path,required=True)
    return run(p.parse_args().private_root)

if __name__=='__main__':
    raise SystemExit(main())
