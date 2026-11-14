#!/usr/bin/env python3
"""AXIA P4 G12: live Student D03 + main file inventory, NO student release.

Checks only real file trees and pinned upstream SHAs. Existence of attribution
documents is not proof of license correctness. This tool cannot inspect full
Git history or private Instructor solutions, never attests legal compliance,
and never upgrades G11/G12/G13 formal acceptance.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

SHA40=re.compile(r"[a-f0-9]{40}\Z")
DIGEST=re.compile(r"sha256:[a-f0-9]{64}\Z")
REQUIRED_D03=frozenset({
    "block_A/day03/todo_safety.py",
    "block_A/day03/p1_adapter_todo.py",
    "block_A/day03/README_D03_KO.md",
    "block_A/tests/test_safety_public.py",
})
BANNED=frozenset({"instructor","instructor_solution","solutions","solution",
                  "hidden_tests","private_keys",".ssh","secrets"})
ROOT_LICENSE="LICENSES.md"
VERSION="VERSION_LOCK.md"
ATTRIBUTION="THIRD_PARTY_ATTRIBUTION.md"


def validate_paths(paths)->set[str]:
    if not isinstance(paths,(list,tuple,set,frozenset)):
        raise ValueError("STUDENT_TREE_NOT_SEQUENCE")
    result=set()
    for name in paths:
        if not isinstance(name,str) or not name or "\x00" in name:
            raise ValueError("STUDENT_TREE_UNSAFE_PATH")
        p=Path(name)
        if p.is_absolute() or len(p.parts)>25 or any(x in ("..",".") for x in p.parts):
            raise ValueError("STUDENT_TREE_UNSAFE_PATH")
        result.add(p.as_posix())
    return result


def audit_release_inventory(*,student_main_paths,student_d03_paths,
                            main_sha:str,d03_sha:str,
                            baseline_runtime_digest:str,
                            student_release_approved:bool=False)->dict:
    if (not isinstance(main_sha,str) or SHA40.fullmatch(main_sha) is None
            or not isinstance(d03_sha,str) or SHA40.fullmatch(d03_sha) is None):
        raise ValueError("G12_SOURCE_PIN_INVALID")
    if (not isinstance(baseline_runtime_digest,str) or
            DIGEST.fullmatch(baseline_runtime_digest) is None):
        raise ValueError("G12_RUNTIME_DIGEST_INVALID")
    if not isinstance(student_release_approved,bool):
        raise ValueError("G12_APPROVAL_TYPE_INVALID")
    main=validate_paths(student_main_paths)
    d03=validate_paths(student_d03_paths)
    private_hits=sorted(
        n for n in main|d03
        if any(part.lower() in BANNED for part in Path(n).parts)
        or Path(n).suffix.lower() in (".key",".pem",".p12",".pfx")
    )
    blockers=[]
    d03_ready=REQUIRED_D03.issubset(d03)
    if not d03_ready:
        blockers.append("D03_TODO_OR_PUBLIC_TEST_MISSING")
    if not REQUIRED_D03.issubset(main):
        blockers.append("D03_NOT_IN_STUDENT_MAIN")
    if ROOT_LICENSE not in main:
        blockers.append("ROOT_LICENSES_MD_MISSING")
    if VERSION not in main:
        blockers.append("ROOT_VERSION_LOCK_MD_MISSING")
    if ATTRIBUTION not in main:
        blockers.append("THIRD_PARTY_ATTRIBUTION_NOT_LOCKED")
    if private_hits:
        blockers.append("PRIVATE_ANSWER_OR_HIDDEN_PATH_DETECTED")
    # Even a complete inventory does not license third-party redistributions.
    # Review of contents/permissions and explicit manual release are separate.
    return {
        "schema":"axia_p4_g12_actual_student_release_inventory_l0_v1",
        "status":"HOLD_INCOMPLETE_STUDENT_RELEASE_INVENTORY" if blockers
                 else "STRUCTURE_ONLY_REQUIRES_LICENSE_CONTENT_AND_OWNER_APPROVAL",
        "student_repo":"silverbjin/axia-robot-safety-student",
        "student_main_sha":main_sha,
        "student_d03_sha":d03_sha,
        "student_main_tracked_path_count":len(main),
        "student_d03_tracked_path_count":len(d03),
        "student_d03_skeleton_present":d03_ready,
        "blockers":sorted(blockers),
        "private_path_finding_count":len(private_hits),
        "instructor_answers_copied":False,
        "source_history_reaudited_here":False,
        "previous_history_heuristic_reference":"PUBLIC_CI_43408993054",
        "runtime_digest_reference":baseline_runtime_digest,
        "runtime_image_pulled_this_job":False,
        "license_contents_verified":False,
        "student_release_approval_flag_supplied":student_release_approved,
        "new_student_release":False,
        "formal_g12_accepted":False,
        "g11_formal_count":0,
        "g13_distinct_external_pcs_verified":0,
        "ros_gazebo_executed":False,
        "certified_estop":False,
    }


def _tracked_paths(root:Path)->set[str]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("G12_STUDENT_ROOT_MISSING")
    data=subprocess.check_output(["git","-C",str(root),"ls-files","-z"],
                                 timeout=10)
    names=[v.decode("utf-8") for v in data.split(b"\0") if v]
    if any((root/n).is_symlink() for n in names):
        raise ValueError("G12_STUDENT_SYMLINK_PATH")
    return validate_paths(names)


def _head(root:Path)->str:
    return subprocess.check_output(
        ["git","-C",str(root),"rev-parse","HEAD"],text=True,timeout=5).strip()


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-main",type=Path,required=True)
    parser.add_argument("--student-d03",type=Path,required=True)
    parser.add_argument("--main-sha",required=True)
    parser.add_argument("--d03-sha",required=True)
    parser.add_argument("--runtime-digest",required=True)
    parser.add_argument("--report",type=Path,required=True)
    a=parser.parse_args(argv)
    try:
        if _head(a.student_main)!=a.main_sha or _head(a.student_d03)!=a.d03_sha:
            raise ValueError("G12_GIT_SOURCE_SHA_MISMATCH")
        result=audit_release_inventory(
            student_main_paths=_tracked_paths(a.student_main),
            student_d03_paths=_tracked_paths(a.student_d03),
            main_sha=a.main_sha,d03_sha=a.d03_sha,
            baseline_runtime_digest=a.runtime_digest)
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        print("AXIA_G12_STUDENT_MAIN_D03_RELEASE_INVENTORY_SCOPED_AUDIT_COMPLETE")
        print("AXIA_G12_RELEASE_STATUS="+result["status"])
        print("AXIA_G12_RELEASE_BLOCKERS="+",".join(result["blockers"]))
        print("AXIA_G12_NO_STUDENT_RELEASE_NO_INSTRUCTOR_SECRETS_G11_0_OF_15")
        # This command succeeded in detecting current release blockers.
        # Exit success is NOT a G12 release success.
        return 0
    except (ValueError,OSError,subprocess.SubprocessError,UnicodeError) as exc:
        print("AXIA_G12_INVENTORY_AUDIT_BLOCKED "+type(exc).__name__+
              ":"+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    sys.exit(main())
