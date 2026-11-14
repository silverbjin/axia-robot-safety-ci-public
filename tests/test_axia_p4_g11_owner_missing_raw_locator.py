"""P4 G08/G11 missing Owner RAW locator RED: local temp HOME only, no ROS."""
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from tools.axia_p4_g11_owner_missing_raw_locator import scan_home

NAME="p0-local-20261101T075725Z-$.tar.gz"
class MissingRawLocatorTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.home=Path(self.t.name)
        self.origin=self.home/"axia_p1_acceptance"/"results"
        self.origin.mkdir(parents=True)
        self.src=self.origin/NAME
        self.src.write_bytes(b"AXIA_G08_TEST_BYTES_NOT_REAL_RAW")
        self.sha=hashlib.sha256(self.src.read_bytes()).hexdigest()
    def tearDown(self):self.t.cleanup()
    def scan(self,**kw):
        return scan_home(self.home,expected_run7_sha=kw.pop("expected",self.sha),**kw)
    def test_exact_archive_hash_match_does_not_accept_formal(self):
        r=self.scan()
        self.assertEqual(r["g08"]["status"],"HASH_MATCH_CANDIDATE_NOT_ACCEPTED")
        self.assertEqual(r["g08"]["matching_count"],1)
        self.assertEqual(r["g11_formal_counts"],dict.fromkeys(("S01","S02","S03","S04","S05"),0))
        self.assertFalse(r["goal_sent"])
        self.assertFalse(r["gazebo_executed"])
        self.assertFalse(r["formal_accepted"])
    def test_mismatching_archive_hash_never_gets_acceptance(self):
        r=self.scan(expected="e"*64)
        self.assertEqual(r["g08"]["status"],"HASH_MISMATCH_NOT_ACCEPTED")
        self.assertEqual(r["g08"]["matching_count"],0)
    def test_missing_archive_reports_not_found_without_new_goal(self):
        self.src.unlink()
        r=self.scan()
        self.assertEqual(r["g08"]["status"],"ORIGINAL_NOT_LOCATED")
        self.assertFalse(r["formal_accepted"])
    def test_symlink_archive_not_followed(self):
        self.src.unlink()
        outside=self.home/"outside.tar.gz";outside.write_bytes(b"data")
        self.src.symlink_to(outside)
        r=self.scan(expected=hashlib.sha256(b"data").hexdigest())
        self.assertEqual(r["g08"]["status"],"ORIGINAL_NOT_LOCATED")
        self.assertEqual(r["g08"]["matching_count"],0)
    def test_g04_bag_without_trace_not_a_complete_raw_pair(self):
        root=self.home/"axia_p1_owner_restore_checkout"/"results"/"p1-t08-20261108T031953Z-example"/"cold_run_01"
        bag=root/"rosbag2"/"rosbag2_0.db3"
        bag.parent.mkdir(parents=True)
        c=sqlite3.connect(str(bag));c.execute("create table topics(id int primary key, name text)");c.commit();c.close()
        r=self.scan()
        self.assertEqual(r["s03"]["matching_run_count_with_bag_and_trace"],0)
        self.assertEqual(r["s03"]["found_bag_without_trace_count"],1)
    def test_g04_trace_plus_sqlite_is_locator_only_not_safety_pass(self):
        root=self.home/"axia_p1_owner_restore_checkout"/"results"/"p1-t08-20261108T031953Z-example"/"cold_run_01"
        bag=root/"rosbag2"/"rosbag2_0.db3";bag.parent.mkdir(parents=True)
        c=sqlite3.connect(str(bag));c.execute("create table topics(id int primary key, name text)");c.commit();c.close()
        (root/"live_trace.jsonl").write_text('{"kind":"start"}\n')
        r=self.scan()
        self.assertEqual(r["s03"]["matching_run_count_with_bag_and_trace"],1)
        self.assertEqual(r["s03"]["status"],"RAW_PAIR_FOUND_BEHAVIOR_NOT_ATTESTED")
        self.assertFalse(r["formal_accepted"])
    def test_scan_bound_must_be_inconclusive_not_missing(self):
        r=self.scan(max_walk_dirs=1)
        self.assertEqual(r["g08"]["status"],"SCAN_LIMIT_REACHED_NOT_ACCEPTED")
    def test_report_never_claims_certified_estop(self):
        self.assertFalse(self.scan()["certified_estop"])
if __name__=="__main__":unittest.main()
