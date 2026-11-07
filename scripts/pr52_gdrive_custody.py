#!/usr/bin/env python3
"""AXIA P1 evidence custody. No ROS actuation; only encrypted files leave CI.

Three real G00 original directories are assessed before archiving. Google Drive
receives only age ciphertext and its SHA256. A second independent Actions job
downloads and hashes ciphertext. The owner's age private key is NEVER in CI;
plaintext restoration and original SQLite review remain a separate gate.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

PRIVATE_REPO = "silverbjin/axia-robot-safety-instructor"
PUBLIC_REPO = "silverbjin/axia-robot-safety-ci-public"
BRANCH = "refs/heads/feat/secure-instructor-cloud-bridge"
REMOTE = "axia_drive:AXIA-P1-T08-private-evidence"
PIN = "5a458a0ca8533b77e548dbb500b00fbe70d61942"
SHA = re.compile(r"[a-f0-9]{40}\Z")
AGE = re.compile(r"age1[023456789acdefghjklmnpqrstuvwxyz]{20,120}\Z")
HEADER = b"age-encryption.org/v1\n"
MARGIN = 256 * 1024 * 1024


class CustodyBlocked(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def check_ci_context(env):
    if not (env.get("CI") == "true"
            and env.get("GITHUB_ACTIONS") == "true"
            and env.get("GITHUB_REPOSITORY") == PUBLIC_REPO
            and env.get("GITHUB_REF") == BRANCH
            and env.get("GITHUB_ACTOR") == "silverbjin"
            and re.fullmatch(r"[0-9]{1,15}", env.get("GITHUB_RUN_ID", ""))
            and re.fullmatch(r"[0-9]{1,5}", env.get("GITHUB_RUN_ATTEMPT", ""))):
        raise CustodyBlocked("PROTECTED_CONTEXT_INVALID")


def remote_object(env, source_sha):
    if not isinstance(source_sha, str) or not SHA.fullmatch(source_sha):
        raise CustodyBlocked("SOURCE_SHA_INVALID")
    check_ci_context(env)
    return (f"{REMOTE}/{source_sha}/"
            f"run-{env['GITHUB_RUN_ID']}-attempt-{env['GITHUB_RUN_ATTEMPT']}"
            "/g00-evidence.tar.gz.age")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as fd:
        for block in iter(lambda: fd.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def invoke(args, *, timeout=900, data=None):
    try:
        p = subprocess.run(args, input=data, capture_output=True,
                           timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise CustodyBlocked("TOOL_EXECUTION_FAILED")
    if p.returncode:
        # Do not expose OAuth token, file metadata, or raw error text in logs.
        raise CustodyBlocked("REMOTE_OPERATION_FAILED")
    return p.stdout


def configure(temp, env):
    secret=env.get("AXIA_GDRIVE_RCLONE_CONFIG_B64", "")
    recipient=env.get("AXIA_GDRIVE_AGE_RECIPIENT", "")
    if not secret or not recipient or not AGE.fullmatch(recipient):
        raise CustodyBlocked("PROTECTED_CREDENTIALS_OR_RECIPIENT_MISSING")
    try:
        decoded=base64.b64decode(secret, validate=True)
        if b"[axia_drive]" not in decoded or len(decoded)>32768:
            raise ValueError("Invalid section or excessive config")
    except (ValueError, base64.binascii.Error):
        raise CustodyBlocked("PROTECTED_CONFIG_INVALID")
    config=temp/"rclone.conf"
    config.write_bytes(decoded)
    config.chmod(0o600)
    return config, recipient


def rclone(config, *args, timeout=900):
    return invoke(["rclone", "--config", str(config), *args],timeout=timeout)


def ensure_quota(config, encrypted_size):
    try:
        quota=json.loads(rclone(config, "about", "axia_drive:", "--json", timeout=90))
        free=quota.get("free")
        if type(free) is not int or free < encrypted_size + MARGIN:
            raise CustodyBlocked("DRIVE_QUOTA_INSUFFICIENT_OR_UNKNOWN")
    except (ValueError, TypeError):
        raise CustodyBlocked("DRIVE_QUOTA_UNAVAILABLE")


def _safe_entries(runs):
    if len(runs)!=3 or len({p.resolve() for p in runs})!=3:
        raise CustodyBlocked("THREE_DISTINCT_G00_RUNS_REQUIRED")
    entries=[]
    for i,run in enumerate(runs,1):
        run=Path(run)
        if not run.is_dir() or run.is_symlink():
            raise CustodyBlocked("ORIGINAL_RUN_INVALID")
        # Include source commit and every original receipt, rosbag, and ledger;
        # refuse links/nonregular files, rather than dereferencing out of root.
        count=0
        for src in sorted(run.rglob("*")):
            if src.is_symlink():
                raise CustodyBlocked("ORIGINAL_SYMLINK_DENIED")
            if src.is_file():
                if not src.resolve().is_relative_to(run.resolve()):
                    raise CustodyBlocked("ORIGINAL_ESCAPE_DENIED")
                entries.append((src,f"g00_run_{i:02d}/{src.relative_to(run).as_posix()}"))
                count+=1
            elif not src.is_dir():
                raise CustodyBlocked("ORIGINAL_SPECIAL_FILE_DENIED")
        if count == 0:
            raise CustodyBlocked("EMPTY_ORIGINAL_RUN_DENIED")
    return entries


def build_archive(runs, archive, metadata):
    entries=_safe_entries(runs)
    with tarfile.open(archive, "w:gz") as tf:
        for src,arc in entries:
            tf.add(src, arcname=arc, recursive=False)
        data=(json.dumps(metadata,sort_keys=True)+"\n").encode("utf-8")
        info=tarfile.TarInfo("custody-record.json")
        info.size=len(data)
        info.mode=0o600
        tf.addfile(info,io.BytesIO(data))
    return len(entries)


def assess_original_runs(private_root, runs, source_sha):
    from tools.p1_t08_local_batch import classify_g00_evidence
    from tools.p1_t08_raw_custody import assess_raw_g00
    goals=set()
    for run in runs:
        gate=classify_g00_evidence(run,expected_sha=source_sha)
        raw=assess_raw_g00(run,source_sha=source_sha)
        goal=gate.get("goal_uuid")
        if (gate.get("status")!="R06_G00_EVIDENCE_CANDIDATE"
                or raw.get("status")!="R06_RAW_CUSTODY_REVIEW_PENDING"
                or not isinstance(goal,str) or goal in goals):
            raise CustodyBlocked("RAW_G00_SOURCE_CUSTODY_BLOCKED")
        goals.add(goal)
    if len(goals)!=3:
        raise CustodyBlocked("GOAL_UUID_UNIQUENESS_BLOCKED")
    return len(goals)


def _precheck(private_root, runs, env):
    check_ci_context(env)
    root=Path(private_root)
    if root.is_symlink() or not root.is_dir():
        raise CustodyBlocked("PRIVATE_SOURCE_DIR_INVALID")
    got=invoke(["git","-C",str(root),"rev-parse","HEAD"],timeout=15).decode().strip()
    if got!=PIN:
        raise CustodyBlocked("SOURCE_SHA_MISMATCH")
    if len(runs)!=3 or not all(Path(r).resolve().is_relative_to((root/"results").resolve()) for r in runs):
        raise CustodyBlocked("ORIGINAL_SOURCE_SCOPE_INVALID")
    return root


def seal(private_root, runs, env=None):
    env=os.environ if env is None else env
    root=_precheck(private_root,runs,env)
    assess_original_runs(root,runs,PIN)
    object_name=remote_object(env,PIN)
    with tempfile.TemporaryDirectory(prefix="axia_custody_",dir=env.get("RUNNER_TEMP") or None) as tmp:
        temp=Path(tmp)
        config,recipient=configure(temp,env)
        original=temp/"g00-evidence.tar.gz"
        count=build_archive(runs,original,{"source_sha":PIN,
            "run_id":env["GITHUB_RUN_ID"],"attempt":env["GITHUB_RUN_ATTEMPT"],
            "runs_collected":3,"original_gate":"R06_RAW_CUSTODY_REVIEW_PENDING",
            "gate_accepted":False,"certified_estop_verified":False})
        if count < 15:
            raise CustodyBlocked("ORIGINAL_ARCHIVE_CONTENT_TOO_SMALL")
        ciphertext=temp/"g00-evidence.tar.gz.age"
        invoke(["age","-r",recipient,"-o",str(ciphertext),str(original)],timeout=1200)
        if not ciphertext.is_file() or ciphertext.open("rb").read(len(HEADER))!=HEADER:
            raise CustodyBlocked("AGE_ENCRYPTION_INVALID")
        digest=sha256(ciphertext)
        sidecar=temp/"g00-evidence.tar.gz.age.sha256"
        sidecar.write_text(digest+"  g00-evidence.tar.gz.age\n")
        ensure_quota(config,ciphertext.stat().st_size)
        # Destination is deterministically unique for this GitHub run attempt;
        # no overwrite and no original files ever sent to Drive.
        rclone(config,"copyto",str(ciphertext),object_name,"--immutable",timeout=1800)
        rclone(config,"copyto",str(sidecar),object_name+".sha256","--immutable",timeout=120)
        status={"status":"CUSTODY_AGE_CIPHER_UPLOADED",
            "original_g00_rechecked":True,"goal_ids_distinct":3,
            "source_sha_verified":True,
            "raw_restored":False,"gate_accepted":False}
    return status


def restore_cipher(source_sha, env=None):
    env=os.environ if env is None else env
    check_ci_context(env)
    obj=remote_object(env,source_sha)
    with tempfile.TemporaryDirectory(prefix="axia_custody_restore_",dir=env.get("RUNNER_TEMP") or None) as tmp:
        temp=Path(tmp)
        config,_=configure(temp,env)
        cipher=temp/"g00-evidence.tar.gz.age"
        sidecar=temp/"g00-evidence.tar.gz.age.sha256"
        rclone(config,"copyto",obj,str(cipher),timeout=1800)
        rclone(config,"copyto",obj+".sha256",str(sidecar),timeout=120)
        record=sidecar.read_text(encoding="utf-8").strip()
        match=re.fullmatch(r"([0-9a-f]{64})  g00-evidence\.tar\.gz\.age",record)
        if (not match or cipher.stat().st_size<64 or
                cipher.open("rb").read(len(HEADER))!=HEADER or
                sha256(cipher)!=match.group(1)):
            raise CustodyBlocked("RESTORED_CIPHER_SHA256_INVALID")
    return {"status":"CUSTODY_CIPHERTEXT_ROUNDTRIP_PASS",
        "remote_cipher_sha256_verified":True,"age_envelope_present":True,
        "raw_restored":False,"owner_private_key_in_ci":False,
        "gate_accepted":False,"certified_estop_verified":False}


def probe(env=None):
    env=os.environ if env is None else env
    check_ci_context(env)
    with tempfile.TemporaryDirectory(prefix="axia_drive_probe_",dir=env.get("RUNNER_TEMP") or None) as tmp:
        temp=Path(tmp)
        config,recipient=configure(temp,env)
        # No original source or Evidence required. No token is written to logs.
        data=temp/"probe.txt"
        data.write_text(f"AXIA P1 drive protected canary {env['GITHUB_RUN_ID']}\n")
        encrypted=temp/"probe.txt.age"
        invoke(["age","-r",recipient,"-o",str(encrypted),str(data)],timeout=30)
        if encrypted.open("rb").read(len(HEADER))!=HEADER:
            raise CustodyBlocked("PROTECTED_AGE_ENCRYPTION_INVALID")
        key=f"{REMOTE}/_probe/probe-{env['GITHUB_RUN_ID']}-{env['GITHUB_RUN_ATTEMPT']}.txt.age"
        ensure_quota(config,encrypted.stat().st_size)
        rclone(config,"copyto",str(encrypted),key,"--immutable",timeout=120)
        try:
            received=temp/"received.txt.age"
            rclone(config,"copyto",key,str(received),timeout=120)
            if sha256(encrypted)!=sha256(received):
                raise CustodyBlocked("PROTECTED_DRIVE_PROBE_SHA256_MISMATCH")
        finally:
            rclone(config,"deletefile",key,timeout=120)
        return {"status":"PROTECTED_DRIVE_CANARY_PASS",
                "age_recipient_configured":bool(recipient),
                "age_encrypted_canary_roundtrip":True,
                "original_bag_uploaded":False,"gate_accepted":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("probe","restore"),required=True)
    parser.add_argument("--source-sha",default=PIN)
    args=parser.parse_args()
    try:
        result=probe() if args.mode=="probe" else restore_cipher(args.source_sha)
        print("AXIA_P1_DRIVE "+json.dumps(result,sort_keys=True),flush=True)
        return 0
    except CustodyBlocked as exc:
        print("AXIA_P1_DRIVE "+json.dumps({"status":"PRIVATE_CUSTODY_BLOCKED",
            "reason":exc.code,"gate_accepted":False,"raw_restored":False},
            sort_keys=True),flush=True)
        return 3
    except Exception:
        print('AXIA_P1_DRIVE {"status":"PRIVATE_CUSTODY_BLOCKED","reason":"UNEXPECTED_PRIVATE_ERROR","gate_accepted":false}',flush=True)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
