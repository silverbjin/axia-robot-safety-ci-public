#!/usr/bin/env python3
"""Private-runner-only real rosbag2 custody/restore verification, no Goal.

This never publishes evidence to public artifacts and never certifies E-Stop.
It proves only bytes from a real no-goal Gazebo rosbag survive one archive and
an independently named restore directory inside the same ephemeral CI runner.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile

PIN = 'd86ee9860de8924f6a5b2c5828d493fb7ef7f9eb'
_REQUIRED_TOPICS = frozenset(('/clock', '/scan'))
_RAW_NAMES = ('startup_verdict.json', 'pre_goal_gate.json',
              'supervisor_prestart.json', 'shutdown_verdict.json',
              'source_commit.txt', 'junit.xml')


class R04Blocked(ValueError):
    pass


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeError):
        raise R04Blocked('READONLY_VERDICT_MISSING') from None
    if not isinstance(data, dict):
        raise R04Blocked('READONLY_VERDICT_INVALID')
    return data


def verify_readonly_source(folder: Path, expected_sha: str) -> None:
    if not folder.is_dir() or folder.is_symlink():
        raise R04Blocked('SOURCE_DIR_INVALID')
    for name in ('nav2_goal.log', 'fault.log', 'live_trace.jsonl', 'start_ack.json'):
        if (folder/name).exists() or (folder/name).is_symlink():
            raise R04Blocked('GOAL_OR_FAULT_EVIDENCE_FORBIDDEN')
    for name in _RAW_NAMES:
        if not (folder/name).is_file() or (folder/name).is_symlink():
            raise R04Blocked('READONLY_VERDICT_MISSING')
    if (folder/'source_commit.txt').read_text(encoding='utf-8').strip() != expected_sha:
        raise R04Blocked('SOURCE_SHA_MISMATCH')
    for name, state in (('startup_verdict.json', 'SMOKE_READY'),
                        ('pre_goal_gate.json', 'PRE_GOAL_READY'),
                        ('supervisor_prestart.json', 'SUPERVISOR_PRESTART_READY'),
                        ('shutdown_verdict.json', 'SHUTDOWN_CLEAN')):
        obj = read_json(folder/name)
        if obj.get('status') != state or obj.get('gate_accepted') is not False:
            raise R04Blocked('READONLY_GATE_UNVERIFIED')
    if read_json(folder/'pre_goal_gate.json').get('goal_sent') is not False:
        raise R04Blocked('GOAL_OR_FAULT_EVIDENCE_FORBIDDEN')


def inspect_real_bag(folder: Path) -> dict:
    """Read SQLite bag without writing; reject empty/corrupt or missing topics."""
    bag = Path(folder)
    meta = bag/'metadata.yaml'
    if bag.is_symlink() or not meta.is_file() or meta.is_symlink():
        raise R04Blocked('ROSBAG_METADATA_MISSING')
    try:
        yaml_text = meta.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        raise R04Blocked('ROSBAG_METADATA_INVALID') from None
    if 'storage_identifier: sqlite3' not in yaml_text:
        raise R04Blocked('ROSBAG_STORAGE_MISMATCH')
    dbs = sorted(bag.glob('*.db3'))
    if not dbs or len(dbs) > 20:
        raise R04Blocked('ROSBAG_DB_MISSING')
    messages, counts = 0, {}
    for db in dbs:
        if not db.is_file() or db.is_symlink() or db.stat().st_size < 1024:
            raise R04Blocked('ROSBAG_DB_INVALID')
        try:
            con = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True, timeout=5)
            try:
                rows = con.execute('SELECT topics.name, COUNT(messages.id) '
                                   'FROM topics JOIN messages ON messages.topic_id = topics.id '
                                   'GROUP BY topics.name').fetchall()
            finally:
                con.close()
        except (sqlite3.DatabaseError, OSError, ValueError):
            raise R04Blocked('ROSBAG_SQLITE_INVALID') from None
        for name, count in rows:
            if not isinstance(name, str) or type(count) is not int:
                raise R04Blocked('ROSBAG_SQLITE_INVALID')
            counts[name] = counts.get(name, 0) + count
            messages += count
    if messages <= 0 or any(counts.get(topic, 0) <= 0 for topic in _REQUIRED_TOPICS):
        raise R04Blocked('ROSBAG_REQUIRED_TOPIC_MISSING')
    return {'message_count_positive': True, 'topic_count': len(counts),
            'required_topics_confirmed': True, 'db_count': len(dbs)}


def verify_ephemeral_custody(private_root: Path) -> int:
    import private_ci_bridge as bridge
    summary = {'status': 'R04_BLOCKED', 'scope': 'EPHEMERAL_NO_GOAL_ROSBAG_CUSTODY_ONLY',
               'gate_accepted': False, 'goal_sent': False, 'fault_injected': False,
               'certified_estop_verified': False, 'off_runner_storage_verified': False,
               'independent_external_review_verified': False}
    try:
        root = bridge.validate_private_commit(private_root)
        if bridge.PIN != PIN:
            raise R04Blocked('PRIVATE_PIN_MISMATCH')
        env = bridge.private_runtime_env(root, os.environ)
        env['AXIA_T08_PRE_GOAL_NO_GOAL_CI'] = 'YES_READ_ONLY'
        env['AXIA_T08_R01_READ_ONLY_BINDING'] = 'NO'
        env['AXIA_NAV2_USE_COMPOSITION'] = 'False'
        env['AXIA_P0_SIM_ONLY'] = '1'
        with tempfile.TemporaryDirectory(prefix='axia_r04_realbag_private_',
                                         dir=os.environ.get('RUNNER_TEMP') or None) as t:
            tmp = Path(t)
            env['AXIA_NAV2_LIFECYCLE_OVERLAY_SETUP'] = str(tmp/'official'/'install'/'setup.bash')
            env['AXIA_SMOKE_RESULTS_DIR'] = str(tmp/'gazebo_run')
            env['ROS_DOMAIN_ID'] = '185'
            env['GZ_PARTITION'] = 'axia_r04_realbag_' + str(os.environ.get('GITHUB_RUN_ID', 'manual'))
            bridge.scrubbed_run('R04_OFFICIAL_OVERLAY',
                ['bash', 'scripts/build_official_nav2_lifecycle_overlay.sh', str(tmp/'official')],
                root, env, tmp, 1200)
            bridge.scrubbed_run('R04_GAZEBO_NO_GOAL_CAPTURE',
                ['bash', 'scripts/run_p1_gazebo_smoke_ci.sh'], root, env, tmp, 700)
            actual = tmp/'gazebo_run'
            verify_readonly_source(actual, PIN)
            original_bag = inspect_real_bag(actual/'rosbag2')
            source = tmp/'custody_source'
            source.mkdir(mode=0o700)
            shutil.copytree(actual/'rosbag2', source/'rosbag2', symlinks=False)
            for name in _RAW_NAMES:
                shutil.copy2(actual/name, source/name)
            run_id = 'axia_r04_' + str(os.environ.get('GITHUB_RUN_ID', 'manual'))
            manifest = {'run_id': run_id, 'source_sha': PIN,
                        'evidence_kind': 'REAL_GAZEBO_READONLY_EPHEMERAL',
                        'gate_accepted': False, 'goal_sent': False}
            (source/'manifest.json').write_text(json.dumps(manifest,sort_keys=True)+'\n')
            (source/'result.json').write_text(json.dumps({
                'status':'READONLY_CUSTODY_SOURCE_VERIFIED',
                'gate_accepted':False,'goal_sent':False},sort_keys=True)+'\n')
            custody = tmp/'private_custody'
            custody.mkdir(mode=0o700)
            sys.path.insert(0, str(root))
            from tools.p1_t08_r04_private_custody import archive_run, restore_run, verify_archive
            archived = archive_run(source, custody, run_id=run_id, source_sha=PIN)
            verified = verify_archive(custody, run_id)
            restored_folder = tmp/'restored_unique_directory'
            restored = restore_run(custody,run_id,restored_folder)
            restored_bag = inspect_real_bag(restored_folder/'rosbag2')
            if original_bag != restored_bag or archived['files'] != verified['files'] or archived['files'] != restored['files']:
                raise R04Blocked('RESTORED_BAG_MISMATCH')
            try:
                baginfo = subprocess.run(['ros2','bag','info',str(restored_folder/'rosbag2')],
                                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                         check=False,timeout=40,env=env)
            except (OSError, subprocess.TimeoutExpired):
                raise R04Blocked('ROSBAG2_INFO_FAILED') from None
            if baginfo.returncode != 0:
                raise R04Blocked('ROSBAG2_INFO_FAILED')
            summary.update(status='R04_REAL_ROSBAG_EPHEMERAL_RESTORE_VERIFIED',
                           real_gazebo_capture=True, restored_binary_verified=True,
                           restored_rosbag2_info_verified=True,
                           topic_count=restored_bag['topic_count'],
                           db_count=restored_bag['db_count'],
                           file_count=restored['files'])
            print('AXIA_PRIVATE_R04 '+json.dumps(summary,sort_keys=True),flush=True)
            return 0
    except R04Blocked as exc:
        summary['reason'] = str(exc)
    except bridge.GateBlocked:
        summary['reason'] = 'PRIVATE_NO_GOAL_STAGE_BLOCKED'
    except Exception:
        summary['reason'] = 'R04_UNCLASSIFIED_PRIVATE_ERROR'
    print('AXIA_PRIVATE_R04 '+json.dumps(summary,sort_keys=True),flush=True)
    return 3


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--private-root',required=True,type=Path)
    raise SystemExit(verify_ephemeral_custody(p.parse_args().private_root))
