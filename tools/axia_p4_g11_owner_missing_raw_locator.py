#!/usr/bin/env python3
"""AXIA Owner-only local missing original locator. No ROS, Goal, or upload.

Scopes: reported P0 RUN7 outer tar.gz (hash checked) and 9 Scan fault,
3 SW Stop, 1 Recovery P1 raw bag + JSONL pairs (presence only).
Never extracts, changes, deletes, accepts gates or writes inside source roots.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import uuid

RUN7_NAME = "p0-local-20261101T075725Z-*.tar.gz"
RUN7_SHA256 = "90f786f7aa50f0e9d47ac242e2ce3276264616e498c68f873e5eaf905b78dfde"
SCAN_TIMES = ("031953","054359","033745","035732","043632","055550",
              "050905","052735","053310")
SW_STOP_TIMES=("022220","024401","025936")
RECOVERY_TIMES=("084114",)
SKIP_DIRS = {".git",".cache",".venv","venv","node_modules","build","install",
             ".local","__pycache__",".npm",".rustup",".cargo",".axia_p4_g11_raw_custody"}
SHA_RE = re.compile(r"^[a-f0-9]{64}$")


def hash_regular(path, max_bytes=8*1024**3):
    if path.is_symlink() or not path.is_file():
        return {"status":"SYMLINK_OR_NONFILE_NOT_HASHED"}
    fd=os.open(path,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size>max_bytes:
            return {"status":"NONREGULAR_OR_OVERSIZE_UNHASHED"}
        h=hashlib.sha256()
        with os.fdopen(fd,"rb",closefd=False) as stream:
            for block in iter(lambda:stream.read(1024*1024),b""):
                h.update(block)
        after=os.fstat(fd)
        if ((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=
                (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)):
            return {"status":"CHANGED_DURING_HASH_NOT_ACCEPTED"}
        return {"status":"SHA256_COMPUTED_NOT_BEHAVIOR_ACCEPTED",
                "sha256":h.hexdigest(),"size_bytes":before.st_size}
    finally:
        os.close(fd)


def _known_p1_runs(home, stamps):
    root=home/"axia_p1_owner_restore_checkout"/"results"
    located=[]
    if root.is_symlink() or not root.is_dir():
        return located
    for stamp in stamps:
        for path in sorted(root.glob("p1-t08-20261108T"+stamp+"Z-*/cold_run_01"))[:10]:
            if (path.is_symlink() or not path.is_dir() or
                    not path.resolve().is_relative_to(home)):
                continue
            bag=path/"rosbag2"/"rosbag2_0.db3"
            trace=path/"live_trace.jsonl"
            bag_exists=bag.is_file() and not bag.is_symlink()
            trace_exists=trace.is_file() and not trace.is_symlink()
            bag_check="NOT_TESTED_NO_BAG"
            if bag_exists:
                try:
                    with sqlite3.connect("file:"+str(bag)+"?mode=ro",uri=True) as db:
                        bag_check=db.execute("pragma quick_check").fetchone()[0]
                except (sqlite3.Error,OSError):
                    bag_check="SQLITE_UNREADABLE"
            located.append({"stamp":stamp,"relative_path":path.relative_to(home).as_posix(),
                            "sqlite_present":bool(bag_exists),
                            "live_trace_present":bool(trace_exists),
                            "sqlite_quick_check":bag_check,
                            "raw_behaviour_reviewed":False,
                            "formal_accepted":False})
    return located


def scan_home(home:Path, *, expected_run7_sha=RUN7_SHA256,
              max_walk_dirs=50000) -> dict:
    home=Path(home).resolve(strict=True)
    if not home.is_dir() or type(max_walk_dirs) is not int or max_walk_dirs<1:
        raise ValueError("G11_OWNER_SCAN_BAD_BOUNDS")
    if not isinstance(expected_run7_sha,str) or SHA_RE.fullmatch(expected_run7_sha) is None:
        raise ValueError("G08_EXPECTED_ARCHIVE_SHA_INVALID")
    candidates=[]
    walked=0
    scan_limited=False
    for base,dirs,names in os.walk(home,followlinks=False):
        walked+=1
        if walked>max_walk_dirs:
            scan_limited=True
            break
        folder=Path(base)
        dirs[:]=sorted(x for x in dirs if x not in SKIP_DIRS and
                       not (folder/x).is_symlink())
        for name in sorted(names):
            if not fnmatch.fnmatchcase(name,RUN7_NAME):
                continue
            file=folder/name
            if file.is_symlink() or not file.is_file():
                continue
            if len(candidates)>=50:
                scan_limited=True
                break
            record=hash_regular(file)
            record["relative_path"]=file.relative_to(home).as_posix()
            record["archive_sha_match"]=(record.get("sha256")==expected_run7_sha)
            candidates.append(record)
        if scan_limited:
            break
    matching=sum(x["archive_sha_match"] for x in candidates)
    if scan_limited:
        result="SCAN_LIMIT_REACHED_NOT_ACCEPTED"
    elif matching:
        result="HASH_MATCH_CANDIDATE_NOT_ACCEPTED"
    elif candidates:
        result="HASH_MISMATCH_NOT_ACCEPTED"
    else:
        result="ORIGINAL_NOT_LOCATED"
    scan=_known_p1_runs(home,SCAN_TIMES)
    stop=_known_p1_runs(home,SW_STOP_TIMES)
    recovery=_known_p1_runs(home,RECOVERY_TIMES)
    pairs=lambda xs:sum(bool(x["sqlite_present"] and x["live_trace_present"] and
                               x["sqlite_quick_check"]=="ok") for x in xs)
    return {
        "schema":"axia_p4_owner_missing_original_readonly_locator_v1",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "scope":"OWNER_HOME_KNOWN_RAW_ONLY_NO_ROS_NO_GOAL",
        "g08":{"status":result,"matching_count":matching,
               "archive_candidates":candidates,"directories_walked":walked,
               "scan_limited":scan_limited,"reported_sha256":expected_run7_sha,
               "formal_accepted":False},
        "s03":{"status":"RAW_PAIR_FOUND_BEHAVIOR_NOT_ATTESTED" if pairs(scan) else
                 "NO_COMPLETE_RAW_PAIR_FOUND",
               "scan_fault_run_directories":scan,
               "matching_run_count_with_bag_and_trace":pairs(scan),
               "found_bag_without_trace_count":sum(x["sqlite_present"] and
                    not x["live_trace_present"] for x in scan),
               "formal_accepted":False},
        "s05":{"status":"RAW_CANDIDATES_NOT_BEHAVIOR_REVIEWED",
               "sw_stop_run_directories":stop,
               "recovery_run_directories":recovery,
               "raw_pair_count":pairs(stop)+pairs(recovery),
               "formal_accepted":False},
        "g11_formal_counts":dict.fromkeys(("S01","S02","S03","S04","S05"),0),
        "goal_sent":False,"gazebo_executed":False,"fault_injected":False,
        "certified_estop":False,"formal_accepted":False,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-home",type=Path,default=Path.home())
    parser.add_argument("--out-dir",type=Path,default=Path.home()/".axia_p4_g11_followup")
    parser.add_argument("--max-walk-dirs",type=int,default=50000)
    args=parser.parse_args(argv)
    try:
        if "microsoft" not in Path("/proc/sys/kernel/osrelease").read_text().lower():
            raise ValueError("G11_OWNER_WSL2_ONLY")
        home=args.owner_home.expanduser().resolve(strict=True)
        dest=args.out_dir.expanduser()
        if dest.is_symlink() or not dest.absolute().resolve().is_relative_to(home):
            raise ValueError("G11_PRIVATE_RESULT_ROOT_OUTSIDE_OWNER_HOME")
        report=scan_home(home,max_walk_dirs=args.max_walk_dirs)
        dest.mkdir(mode=0o700,parents=True,exist_ok=True)
        dest.chmod(0o700)
        output=dest/(datetime.now(timezone.utc).strftime(
            "g08-g11-missing-original-%Y%m%dT%H%M%SZ-")+uuid.uuid4().hex[:8]+".json")
        fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        print("AXIA_G08_RUN7_ORIGINAL_FIND_STATUS="+report["g08"]["status"]+
              " matches="+str(report["g08"]["matching_count"]))
        print("AXIA_G11_S03_SCAN_RAW_PAIRS="+str(report["s03"]["matching_run_count_with_bag_and_trace"]))
        print("AXIA_G11_S05_RECOVERY_AND_STOP_RAW_PAIRS="+str(report["s05"]["raw_pair_count"]))
        print("AXIA_G11_PRIVATE_READONLY_REPORT="+str(output))
        print("AXIA_G11_NO_ROS_NO_GOAL_NO_UPLOAD_FORMAL_0_OF_15")
        return 0
    except (ValueError,OSError,TypeError) as exc:
        print("AXIA_G08_G11_OWNER_LOCATOR_BLOCKED "+type(exc).__name__+":"+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
