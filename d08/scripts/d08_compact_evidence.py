#!/usr/bin/env python3
"""Bounded PRIVATE Owner evidence ZIP: first error, recent cycles, SHA256.

Do not include source checkout, git history, ONNX, .deb/.nupkg, build/install,
raw rosbag or other large assets. Never delete the original raw run directory.
"""
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path

MAX_FILE=256*1024
ROOT_LOGS=['yolo_native.log','yolo_ldd.log','yolo_build.log','owner_gpu_probe.txt','asset_sha256.txt']
LIVE_FILES=[
 'verdict.json','runtime_provenance.json','amcl_receive_timing.json',
 'gazebo_startup.json',
 'official_nav2_before_path.json','overlay/manifest.json',
 'actual_world.sdf','actual_waffle.sdf','gazebo_topics.txt',
 'scene_info_verdict.json','scene_info_response.txt','native_create_ack.txt',
 'official_path_phases/verdict.json','official_path_phases/path_phases.jsonl',
 'live_person_range/verdict.json']
ERROR_PATTERN=re.compile(
 r'(ERROR|FATAL|Exception|Traceback|BLOCKED|TIMEOUT|GAP|first_boundary|process has died|not found|Unable to find or download file|SceneBroadcaster)',re.I)

def _bounded_log(raw:bytes)->tuple[bytes,bytes]:
    lines=raw.decode('utf-8','replace').splitlines(keepends=True)
    selected=[]
    for i,line in enumerate(lines):
        if ERROR_PATTERN.search(line):
            selected.append(''.join(lines[max(0,i-2):min(len(lines),i+3)]))
            if len(selected)>=80:break
    errors=''.join(selected).encode('utf-8')[:MAX_FILE]
    edges=(''.join(lines[:55])+'\n--- omitted middle ---\n'+''.join(lines[-80:])).encode('utf-8')[:MAX_FILE]
    return errors,edges

def create_compact_evidence(run_dir:Path,archive:Path)->dict:
    run_dir=Path(run_dir).resolve();archive=Path(archive).resolve()
    if not run_dir.is_dir() or archive.exists() or archive.is_symlink():
        raise ValueError('D08_COMPACT_RUN_OR_OUTPUT_INVALID')
    out={}
    def add_from(path:Path,relative:str,*,bounded=False):
        if not path.is_file() or path.is_symlink():return
        data=path.read_bytes()
        if bounded:
            err,edges=_bounded_log(data)
            if err:out[relative.replace('.log','_error_context.txt')]=err
            if len(data)>MAX_FILE:
                out[relative.replace('.log','_startup_shutdown.txt')]=edges
            else:
                out[relative]=data
        else:
            if len(data)>MAX_FILE:raise ValueError('D08_COMPACT_UNEXPECTED_LARGE_EVIDENCE:'+relative)
            out[relative]=data
    for f in LIVE_FILES:add_from(run_dir/'live_evidence'/f,'live_evidence/'+f)
    # RMW summary and the FIRST Owner boundary only; never ship raw CTF or
    # unbounded per-message RMW JSONL to students or public CI.
    for f in ('summary.json','owner_first_gap_verdict.json',
              'trace-size-bytes.txt','tracetools-status.txt',
              'raw-archive-verdict.txt','stop.success'):
        add_from(run_dir/'rmw_trace'/f,'rmw_trace/'+f)
    for f in ROOT_LOGS:add_from(run_dir/f,'logs/'+f,bounded=True)
    add_from(run_dir/'live_evidence'/'d08_official_nav2_one_world.log',
             'logs/d08_official_nav2_one_world.log',bounded=True)
    add_from(run_dir/'live_evidence'/'gazebo_server.log',
             'logs/gazebo_server.log',bounded=True)
    cycles=run_dir/'live_evidence'/'owner_replan_cycles'
    ids=sorted((p for p in cycles.glob('cycle_[0-9][0-9][0-9][0-9]') if p.is_dir()),
               key=lambda p:p.name)
    chosen=set(ids[:1]+ids[-2:])
    # Include the FIRST failed cycle even if many repeat successes follow.
    for p in ids:
        v=p/'verdict.json'
        if v.is_file():
            try:
                row=json.loads(v.read_text())
                if row.get('first_boundary') or row.get('status') not in (
                    'D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL','PASS'):
                    chosen.add(p);break
            except Exception:chosen.add(p);break
    for p in sorted(chosen):
        for name in ('verdict.json','path_phases.jsonl'):
            add_from(p/name,'live_evidence/owner_replan_cycles/'+p.name+'/'+name)
    manifest={'status':'D08_COMPACT_EVIDENCE_READY',
              'archive_scope':'PRIVATE_LOCAL_FIRST_BOUNDARY_ONLY',
              'source_and_build_included':False,
              'files':{k:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}
                       for k,v in sorted(out.items())}}
    out['manifest.json']=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    out['SHA256SUMS']=(''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n'
                            for name,data in sorted(out.items()))).encode()
    archive.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(out.items()):z.writestr(name,data)
    return {'status':'D08_COMPACT_EVIDENCE_READY','path':str(archive),
            'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'bytes':archive.stat().st_size,'file_count':len(out)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    print('D08_OWNER_COMPACT_BUNDLE '+json.dumps(create_compact_evidence(a.run,a.out)),flush=True)

if __name__=='__main__':main()
