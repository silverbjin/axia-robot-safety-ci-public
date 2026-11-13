#!/usr/bin/env python3
"""Read-only Owner TAR custody audit. No ROS/Gazebo/Goal/Fault and no raw upload.

Checks the OUTER archive digest (when anchored), all internal SHA256SUMS,
SQLite quick_check, and rosbag2 message counts. These are integrity checks,
NOT independent safety-state, PID, Goal, stop, contact, or signoff evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

HEX64 = re.compile(r"^[0-9a-f]{64}$")
SUM_LINE = re.compile(r"^([0-9a-fA-F]{64}) ([ *])(.+)$")
MAX_TAR_MEMBERS = 4096
MAX_TOTAL_UNCOMPRESSED_BYTES = 8 * 1024**3
MAX_COMPRESSED_BYTES = 8 * 1024**3
MAX_MANIFEST_BYTES = 2 * 1024**2
READ_SIZE = 1024 * 1024


class AuditBlocked(Exception):
    """One fail-closed, stable, non-sensitive reason."""


def _safe_tar_name(name: str) -> bool:
    if not isinstance(name, str) or not name or name.startswith("/") or "\\" in name or "\x00" in name:
        return False
    parts = name.rstrip("/").split("/")
    return bool(parts) and all(p not in ("", ".", "..") for p in parts)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(READ_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_tar_and_check(archive: Path) -> tuple[int, int, list[dict]]:
    """Stream only regular members; temporary DB files are cleaned automatically."""
    actual: dict[str, str] = {}
    sqlite_reports: list[dict] = []
    manifest_paths: list[str] = []
    manifest_bytes = None
    with tempfile.TemporaryDirectory(prefix="axia-p2-archive-readonly-") as tmp:
        with tarfile.open(archive, mode="r:gz") as tf:
            members = tf.getmembers()
            if len(members) > MAX_TAR_MEMBERS:
                raise AuditBlocked("ARCHIVE_MEMBER_LIMIT")
            seen: set[str] = set()
            file_members = []
            total = 0
            for member in members:
                if not _safe_tar_name(member.name):
                    raise AuditBlocked("UNSAFE_TAR_MEMBER")
                if member.name in seen:
                    raise AuditBlocked("DUPLICATE_TAR_MEMBER")
                seen.add(member.name)
                if member.isdir():
                    continue
                if not member.isfile() or member.size < 0:
                    raise AuditBlocked("UNSAFE_TAR_MEMBER")
                total += member.size
                if total > MAX_TOTAL_UNCOMPRESSED_BYTES:
                    raise AuditBlocked("UNCOMPRESSED_SIZE_LIMIT")
                file_members.append(member)
                if PurePosixPath(member.name).name == "SHA256SUMS":
                    manifest_paths.append(member.name)
            if len(manifest_paths) != 1:
                raise AuditBlocked("SHA256SUMS_MISSING" if not manifest_paths else "MULTIPLE_SHA256SUMS")
            manifest_path = manifest_paths[0]
            for member in file_members:
                stream = tf.extractfile(member)
                if stream is None:
                    raise AuditBlocked("TAR_MEMBER_READ_FAILED")
                digest = hashlib.sha256()
                is_db = member.name.lower().endswith((".db3", ".sqlite", ".sqlite3"))
                is_manifest = member.name == manifest_path
                db_path = Path(tmp) / ("db-" + str(len(sqlite_reports)) + ".db3")
                if is_manifest and member.size > MAX_MANIFEST_BYTES:
                    raise AuditBlocked("MANIFEST_SIZE_LIMIT")
                chunks = [] if is_manifest else None
                with (db_path.open("wb") if is_db else open(os.devnull, "wb")) as destination:
                    while chunk := stream.read(READ_SIZE):
                        digest.update(chunk)
                        if chunks is not None:
                            chunks.append(chunk)
                        if is_db:
                            destination.write(chunk)
                actual[member.name] = digest.hexdigest()
                if chunks is not None:
                    manifest_bytes = b"".join(chunks)
                if is_db:
                    try:
                        with sqlite3.connect("file:" + str(db_path) + "?mode=ro", uri=True) as con:
                            check = con.execute("PRAGMA quick_check").fetchone()
                            if check is None or check[0] != "ok":
                                raise AuditBlocked("SQLITE_QUICK_CHECK_FAILED")
                            count = con.execute("SELECT count(*) FROM messages").fetchone()[0]
                            topics = con.execute("SELECT count(*) FROM topics").fetchone()[0]
                            if count < 1 or topics < 1:
                                raise AuditBlocked("SQLITE_EMPTY_OR_MISSING_MESSAGES")
                            sqlite_reports.append({"file": PurePosixPath(member.name).name,
                                                   "quick_check": "ok", "message_count": count,
                                                   "topic_count": topics})
                    except (sqlite3.Error, UnicodeError) as exc:
                        raise AuditBlocked("SQLITE_QUICK_CHECK_FAILED") from exc
                    finally:
                        db_path.unlink(missing_ok=True)
    if manifest_bytes is None:
        raise AuditBlocked("SHA256SUMS_MISSING")
    try:
        lines = manifest_bytes.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise AuditBlocked("INVALID_SHA256SUMS") from exc
    listed: dict[str, str] = {}
    manifest_parent = str(PurePosixPath(manifest_path).parent)
    for line in lines:
        if not line:
            continue
        matched = SUM_LINE.fullmatch(line)
        if matched is None:
            raise AuditBlocked("INVALID_SHA256SUMS")
        filename = matched.group(3)
        while filename.startswith("./"):
            filename = filename[2:]
        if not _safe_tar_name(filename):
            raise AuditBlocked("INVALID_SHA256SUMS_PATH")
        full_name = manifest_parent + "/" + filename if manifest_parent != "." else filename
        if full_name in listed:
            raise AuditBlocked("DUPLICATE_SHA256SUMS_ENTRY")
        listed[full_name] = matched.group(1).lower()
    files = set(actual) - {manifest_path}
    if not listed or set(listed) != files:
        raise AuditBlocked("SHA256SUMS_COVERAGE_MISMATCH")
    if any(actual[name] != hexdigest for name, hexdigest in listed.items()):
        raise AuditBlocked("INTERNAL_SHA256_MISMATCH")
    if not sqlite_reports:
        raise AuditBlocked("SQLITE_MISSING")
    return len(listed), len(files), sqlite_reports


def audit_archive(path: Path, *, expected_sha256: str | None = None) -> dict:
    """Never report formal PASS, even when every archive byte is sound."""
    archive = Path(path)
    result = {
        "archive_name": archive.name,
        "status": "BLOCKED",
        "reason": "UNREVIEWED",
        "outer_sha256": None,
        "outer_sha256_match": None,
        "hash_verified_entries": 0,
        "manifest_entries": 0,
        "sqlite": [],
        "gate_accepted": False,
        "raw_behavior_reviewed": False,
        "goal_sent": False,
        "fault_injected": False,
        "certified_estop": False,
        "owner_l3_new_run": False,
        "review_level": "OFFLINE_CUSTODY_ONLY",
    }
    try:
        if expected_sha256 is not None and not HEX64.fullmatch(expected_sha256):
            raise AuditBlocked("INVALID_EXPECTED_SHA256")
        if archive.is_symlink() or not archive.is_file() or not archive.name.endswith(".tar.gz"):
            raise AuditBlocked("ARCHIVE_NOT_FOUND_OR_UNSAFE")
        if archive.stat().st_size > MAX_COMPRESSED_BYTES:
            raise AuditBlocked("COMPRESSED_SIZE_LIMIT")
        outer = _sha256_file(archive)
        result["outer_sha256"] = outer
        if expected_sha256 is not None:
            result["outer_sha256_match"] = outer == expected_sha256
            if outer != expected_sha256:
                raise AuditBlocked("OUTER_SHA256_MISMATCH")
        entries, matched, sqlite_reports = _read_tar_and_check(archive)
        result.update(manifest_entries=entries, hash_verified_entries=matched, sqlite=sqlite_reports)
        result["status"] = ("INTEGRITY_VERIFIED_NOT_ACCEPTED" if expected_sha256 is not None
                            else "INTEGRITY_UNANCHORED_NOT_ACCEPTED")
        result["reason"] = "RAW_SAFETY_BEHAVIOR_REVIEW_REQUIRED"
    except AuditBlocked as exc:
        result["reason"] = str(exc)
    except (tarfile.TarError, OSError, ValueError, OverflowError) as exc:
        result["reason"] = "ARCHIVE_UNREADABLE_" + type(exc).__name__
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, action="append", required=True)
    parser.add_argument("--expect", action="append", default=[],
                        metavar="BASENAME=SHA256", help="Prior independently recorded outer digest")
    parser.add_argument("--out-dir", type=Path,
                        default=Path.home() / ".axia_p2_private_archive_audit")
    args = parser.parse_args(argv)
    expected = {}
    for item in args.expect:
        name, sep, digest = item.partition("=")
        if (not sep or not name.endswith(".tar.gz") or "/" in name
                or name in expected or not HEX64.fullmatch(digest)):
            parser.error("invalid --expect entry")
        expected[name] = digest
    home = Path.home().resolve()
    out = args.out_dir.expanduser()
    if out.is_symlink() or not out.resolve().is_relative_to(home):
        parser.error("results must be within Owner home and not symlinked")
    os.makedirs(out, mode=0o700, exist_ok=True)
    os.chmod(out, 0o700)
    archives = list(args.archive)
    if len(archives) > 8 or len(set(str(x) for x in archives)) != len(archives):
        parser.error("duplicate or excessive archive paths")
    records = [audit_archive(p, expected_sha256=expected.get(p.name)) for p in archives]
    report = {"schema": "axia_p2_g05_g06_archive_custody_v1",
              "created_utc": datetime.now(timezone.utc).isoformat(),
              "status": "OFFLINE_CUSTODY_ONLY",
              "gate_accepted": False, "owner_l3_new_run": False,
              "raw_behavior_reviewed": False, "certified_estop": False,
              "records": records}
    destination = out / ("p2-archive-audit-" + uuid4().hex[:12] + ".json")
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    for record in records:
        print("AXIA_P2_ARCHIVE " + record["archive_name"] + " " + record["status"]
              + " reason=" + record["reason"]
              + " entries=" + str(record["hash_verified_entries"]))
    print("AXIA_P2_OFFLINE_CUSTODY_COMPLETE RAW_SAFETY_REVIEW_REQUIRED NO_GOAL NO_FAULT")
    print("PRIVATE_LOCAL_REPORT=" + str(destination))
    return 2 if any(r["status"] == "BLOCKED" for r in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
