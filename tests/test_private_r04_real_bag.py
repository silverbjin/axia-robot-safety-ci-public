"""Public synthetic contract for R04, no private files or actual ROS motion."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
FILE = SOURCE/'scripts/private_r04_real_bag_bridge.py'
spec = importlib.util.spec_from_file_location('private_r04_real_bag_bridge',FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def create_bag(base, *, clock=True, scan=True, storage='sqlite3'):
    bag = base/'rosbag2';bag.mkdir()
    (bag/'metadata.yaml').write_text('rosbag2_bagfile_information:\n  storage_identifier: '+storage+'\n')
    db = bag/'rosbag2_0.db3'
    con=sqlite3.connect(db)
    con.execute('CREATE TABLE topics(id INTEGER PRIMARY KEY, name TEXT NOT NULL)')
    con.execute('CREATE TABLE messages(id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL)')
    for tid, name, include in ((1,'/clock',clock),(2,'/scan',scan),(3,'/odom',True)):
        con.execute('INSERT INTO topics VALUES (?,?)',(tid,name))
        if include:con.execute('INSERT INTO messages VALUES (?,?)',(tid,tid))
    con.commit();con.close()
    return bag

class TestR04RealBag(unittest.TestCase):
    def test_real_sqlite_required_topics(self):
        with tempfile.TemporaryDirectory() as d:
            b=create_bag(Path(d))
            v=mod.inspect_real_bag(b)
            self.assertTrue(v['required_topics_confirmed'])
            self.assertTrue(v['message_count_positive'])
            self.assertEqual(v['topic_count'],3)
    def test_missing_scan_or_clock_never_counted(self):
        for clock,scan in ((False,True),(True,False)):
            with tempfile.TemporaryDirectory() as d:
                b=create_bag(Path(d),clock=clock,scan=scan)
                with self.assertRaisesRegex(mod.R04Blocked,'ROSBAG_REQUIRED_TOPIC_MISSING'):
                    mod.inspect_real_bag(b)
    def test_corrupt_sqlite_or_wrong_storage_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            b=create_bag(Path(d),storage='mcap')
            with self.assertRaisesRegex(mod.R04Blocked,'ROSBAG_STORAGE_MISMATCH'):
                mod.inspect_real_bag(b)
        with tempfile.TemporaryDirectory() as d:
            b=create_bag(Path(d))
            (b/'rosbag2_0.db3').write_bytes(b'bad data' * 200)
            with self.assertRaisesRegex(mod.R04Blocked,'ROSBAG_SQLITE_INVALID'):
                mod.inspect_real_bag(b)
    def test_no_goal_evidence_blocks_even_when_healthy_status(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name, status in (('startup_verdict.json','SMOKE_READY'),
                                 ('pre_goal_gate.json','PRE_GOAL_READY'),
                                 ('supervisor_prestart.json','SUPERVISOR_PRESTART_READY'),
                                 ('shutdown_verdict.json','SHUTDOWN_CLEAN')):
                (root/name).write_text(json.dumps({'status':status,'gate_accepted':False,'goal_sent':False}))
            (root/'source_commit.txt').write_text(mod.PIN)
            (root/'junit.xml').write_text('<testsuite tests="1" failures="0"/>')
            mod.verify_readonly_source(root,mod.PIN)
            (root/'nav2_goal.log').write_text('fake goal')
            with self.assertRaisesRegex(mod.R04Blocked,'GOAL_OR_FAULT_EVIDENCE_FORBIDDEN'):
                mod.verify_readonly_source(root,mod.PIN)
    def test_no_acceptance_promotion_or_external_custody_claim_in_source(self):
        text=FILE.read_text()
        self.assertIn("'off_runner_storage_verified': False",text)
        self.assertIn("'independent_external_review_verified': False",text)
        self.assertNotIn('actions/upload-artifact',text)
        self.assertNotIn('/axia/safety/start',text)
        self.assertNotIn('ros2 action send_goal',text)
        self.assertIn("'gate_accepted': False",text)
        self.assertIn("'AXIA_T08_PRE_GOAL_NO_GOAL_CI'] = 'YES_READ_ONLY'",text)
        self.assertEqual(mod.PIN,'d86ee9860de8924f6a5b2c5828d493fb7ef7f9eb')
