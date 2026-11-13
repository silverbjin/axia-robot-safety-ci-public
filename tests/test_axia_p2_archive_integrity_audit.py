"""Synthetic archive-only regression; NEVER download or launch Owner ROS artifacts."""
import hashlib
import io
import importlib.util
from pathlib import Path
import sqlite3
import tarfile
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools/axia_p2_archive_integrity_audit.py"
spec = importlib.util.spec_from_file_location("axia_p2_archive_integrity_audit", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fixture_archive(root: Path, *, bad_hash=False, missing_manifest=False, symlink=False, corrupt_db=False):
    db = root / "synthetic.db3"
    if corrupt_db:
        db.write_bytes(b"not a sqlite database")
    else:
        with sqlite3.connect(db) as con:
            con.execute("CREATE TABLE topics (id INTEGER PRIMARY KEY, name TEXT)")
            con.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, topic_id INTEGER)")
            con.execute("INSERT INTO topics VALUES (1, '/odom')")
            con.execute("INSERT INTO messages VALUES (1, 1)")
    members = {"G06/rosbag2_0.db3": db.read_bytes(),
               "G06/live/case_result.json": b'{"case":"G06","status":"NUMERICAL_CANDIDATE"}'}
    checksum = "".join(
        f"{'0'*64 if bad_hash and i==0 else hashlib.sha256(data).hexdigest()}  ./{name}\n"
        for i, (name, data) in enumerate(members.items()))
    if not missing_manifest:
        members["SHA256SUMS"] = checksum.encode()
    archive = root / "synthetic-owner.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        for name, data in members.items():
            info = tarfile.TarInfo("owner-evidence/" + name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        if symlink:
            info = tarfile.TarInfo("owner-evidence/escape")
            info.type = tarfile.SYMTYPE
            info.linkname = "../../etc/passwd"
            tf.addfile(info)
    return archive


class ArchiveAuditTests(unittest.TestCase):
    def test_valid_integrity_is_never_gate_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = fixture_archive(Path(tmp))
            got = audit.audit_archive(a, expected_sha256=hashlib.sha256(a.read_bytes()).hexdigest())
            self.assertEqual(got["status"], "INTEGRITY_VERIFIED_NOT_ACCEPTED")
            self.assertEqual(got["hash_verified_entries"], 2)
            self.assertEqual(got["sqlite"][0]["quick_check"], "ok")
            self.assertEqual(got["sqlite"][0]["message_count"], 1)
            self.assertFalse(got["gate_accepted"])
            self.assertFalse(got["raw_behavior_reviewed"])
            self.assertFalse(got["goal_sent"])

    def test_bad_outer_checksum_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = audit.audit_archive(fixture_archive(Path(tmp)), expected_sha256="0"*64)
            self.assertEqual(got["status"], "BLOCKED")
            self.assertEqual(got["reason"], "OUTER_SHA256_MISMATCH")

    def test_missing_outer_anchor_is_not_full_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = audit.audit_archive(fixture_archive(Path(tmp)))
            self.assertEqual(got["status"], "INTEGRITY_UNANCHORED_NOT_ACCEPTED")
            self.assertFalse(got["gate_accepted"])

    def test_internal_corruption_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = audit.audit_archive(fixture_archive(Path(tmp), bad_hash=True))
            self.assertEqual(got["status"], "BLOCKED")
            self.assertEqual(got["reason"], "INTERNAL_SHA256_MISMATCH")

    def test_missing_manifest_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = audit.audit_archive(fixture_archive(Path(tmp), missing_manifest=True))
            self.assertEqual(got["status"], "BLOCKED")
            self.assertEqual(got["reason"], "SHA256SUMS_MISSING")

    def test_symlink_member_blocks_without_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = audit.audit_archive(fixture_archive(Path(tmp), symlink=True))
            self.assertEqual(got["status"], "BLOCKED")
            self.assertEqual(got["reason"], "UNSAFE_TAR_MEMBER")

    def test_corrupt_sqlite_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = audit.audit_archive(fixture_archive(Path(tmp), corrupt_db=True))
            self.assertEqual(got["status"], "BLOCKED")
            self.assertEqual(got["reason"], "SQLITE_QUICK_CHECK_FAILED")


if __name__ == "__main__":
    unittest.main()
