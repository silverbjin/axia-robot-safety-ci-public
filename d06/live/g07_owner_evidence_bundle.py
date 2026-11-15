#!/usr/bin/env python3
"""PRIVATE local Owner G07 support-bundle collector. NO ROS, Goal or upload.

Collect owner archive/raw, GUI sidecar and G11 custody read-only. All originals
remain in place. Results live under ~/.axia_g07_owner_support/<unique>/.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tarfile
import tempfile
from datetime import datetime,timezone

OWNER_FILES=(
    "source.sha","summary.json","g07_machine_preflight.json",
    "G07/live.log","G07/launch.log","G07/rosbag.log",
    "G07/startup_verdict.json","G07/g07_userspace_parity.json",
    "G07/clock_diagnostics.json","G07/p2_graph_diagnostics.json",
    "G07/rosbag2/metadata.yaml",
    "G07/live/ci_moving_goal_result.json",
    "G07/live/actual_ros_events.jsonl",
    "G07/live/owner_parity_fatal_trace.log",
)
GUI_FILES=(
    "sidecar.log","monitor.log","readonly_monitor.log","rviz.log",
    "gz_gui.log","windows.txt","display_attestation.json",
    "readonly_samples.jsonl","joined_first_cm_guard.json",
    "joined_first_cm_guard.log","first_failure_triage.json",
    "first_failure_triage.log","session_attachment.txt","SHA256SUMS",
)

def _hash(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def _regular(path,home):
    try:
        if path.is_symlink() or not path.is_file():return False
        path.relative_to(home)
        mode=path.stat().st_mode
        return stat.S_ISREG(mode) and 0 <= path.stat().st_size < 512*1024*1024
    except (OSError,ValueError):
        return False

def collect(home,owner_root,gui_root,status_code):
    home=home.resolve(strict=True)
    owner=owner_root.resolve() if owner_root is not None else None
    gui=gui_root.resolve() if gui_root is not None else None
    if owner is not None:
        try:owner.relative_to(home/"axia_p2_private_evidence")
        except ValueError:raise ValueError("OWNER_ROOT_OUTSIDE_LOCAL_PRIVATE_HOME")
    if gui is not None:
        try:gui.relative_to(home)
        except ValueError:raise ValueError("GUI_ROOT_OUTSIDE_LOCAL_HOME")
    parent=home/".axia_g07_owner_support"
    parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    os.chmod(parent,0o700)
    dest=Path(tempfile.mkdtemp(prefix="g07-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-",dir=parent))
    os.chmod(dest,0o700)
    pairs=[]
    owner_archive=False
    if owner is not None and owner.is_dir():
        # Preserve original owner archive verbatim plus its independent hash.
        for suffix in (".tar.gz",".tar.gz.sha256"):
            f=Path(str(owner)+suffix)
            if _regular(f,home):
                pairs.append((f,"owner_original/"+f.name))
                if suffix==".tar.gz":owner_archive=True
        for rel in OWNER_FILES:
            f=owner/rel
            if _regular(f,home):pairs.append((f,"owner_selected/"+rel))
        if not owner_archive:
            bag=owner/"G07"/"rosbag2"
            if bag.is_dir():
                for f in sorted(bag.glob("*.db3")):
                    if _regular(f,home):
                        pairs.append((f,"owner_selected/G07/rosbag2/"+f.name))
    if gui is not None and gui.is_dir():
        for rel in GUI_FILES:
            f=gui/rel
            if _regular(f,home):pairs.append((f,"gui_readonly/"+rel))
    custody=home/".axia_p4_g11_session_custody"
    for folder in ("manifests","reviews"):
        q=custody/folder
        if q.is_dir():
            for f in sorted(q.glob("*.json")):
                if _regular(f,home):
                    pairs.append((f,"g11_custody/"+folder+"/"+f.name))
    # Deduplicate paths, avoid symlink injection and preserve exact original
    # evidence file bytes. No shell, network, ROS API or public upload.
    uniq={}
    for path,name in pairs:uniq[name]=path
    entries=[]
    bundle=dest/"support_evidence.tar.gz"
    tmp=dest/"support_evidence.tar.gz.partial"
    with tarfile.open(tmp,"w:gz") as archive:
        for name,path in sorted(uniq.items()):
            try:
                if not _regular(path,home):continue
                info=tarfile.TarInfo(name)
                info.size=path.stat().st_size
                info.mode=0o600
                info.mtime=int(path.stat().st_mtime)
                with path.open("rb") as file:
                    archive.addfile(info,file)
                entries.append({"name":name,"bytes":info.size,"sha256":_hash(path)})
            except OSError:
                continue
    os.chmod(tmp,0o600)
    os.replace(tmp,bundle)
    status=("EVIDENCE_BUNDLED_OWNER_NOT_ACCEPTED" if
            owner is not None and owner.is_dir() and owner_archive and
            any(e["name"].endswith("ci_moving_goal_result.json") for e in entries)
            else "INCOMPLETE_OWNER_ORIGINAL_UNAVAILABLE")
    result={
        "schema":"axia.g07.owner_private_support_bundle_v1",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "status":status,"owner_wrapper_rc":status_code,
        "owner_l3_accepted":False,"formal_mvp_accepted":False,
        "certified_estop":False,"uploaded":False,"no_ros_no_goal":True,
        "owner_original_archive_present":owner_archive,
        "file_count":len(entries),"files":entries,
        "bundle_sha256":_hash(bundle),
    }
    manifest=dest/"manifest.json"
    with manifest.open("x",encoding="utf-8") as f:
        json.dump(result,f,sort_keys=True,indent=2);f.write("\n")
    checksum=dest/"SHA256SUMS"
    with checksum.open("x",encoding="ascii") as f:
        f.write(_hash(bundle)+"  support_evidence.tar.gz\n")
        f.write(_hash(manifest)+"  manifest.json\n")
    for f in (manifest,checksum):os.chmod(f,0o600)
    print("AXIA_G07_OWNER_SUPPORT_BUNDLE="+str(dest))
    print("AXIA_G07_OWNER_SUPPORT_ARCHIVE="+str(bundle))
    print("AXIA_G07_OWNER_SUPPORT_STATUS="+status+
          " PRIVATE_RAW_LOCAL_ONLY OWNER_NOT_ACCEPTED")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--home",type=Path,required=True)
    p.add_argument("--owner-root",type=Path)
    p.add_argument("--gui-root",type=Path)
    p.add_argument("--status-code",type=int,required=True)
    a=p.parse_args()
    try:collect(a.home,a.owner_root,a.gui_root,a.status_code)
    except (ValueError,OSError) as e:
        print("AXIA_G07_OWNER_BUNDLE_FAILED_NO_ACCEPTANCE "+type(e).__name__)
        return 3
    return 0

if __name__=="__main__":
    raise SystemExit(main())
