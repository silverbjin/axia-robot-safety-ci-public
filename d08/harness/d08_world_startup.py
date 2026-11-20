"""Fail-closed actual D08 Gazebo world readiness BEFORE official Nav2.
Owner 2026-11-18 gz exit255 /tmp/nav2_*.sdf: never mislabel as Contact fault.
"""
from __future__ import annotations
import hashlib,json,subprocess,time
from pathlib import Path
import xml.etree.ElementTree as ET

WORLD_SVC='/world/default/scene/info'

def inspect_generated_world(world_sdf:Path)->dict:
    p=Path(world_sdf)
    try:
        if not p.is_file() or p.is_symlink() or p.stat().st_size==0:
            raise ValueError('not a regular nonempty SDF')
        raw=p.read_bytes()
        root=ET.fromstring(raw)
        worlds=root.findall('./world')
        if root.tag!='sdf' or len(worlds)!=1 or worlds[0].get('name')!='default':
            raise ValueError('wrong world name or document root')
        if worlds[0].find("./model[@name='axia_p2_g07_obstacle']") is None:
            raise ValueError('physical proxy fixture missing')
        return {'world_name':'default','bytes':len(raw),
                'sha256':hashlib.sha256(raw).hexdigest(),
                'path':str(p.resolve()),'temp_nav2_sdf_used_by_server':False}
    except (OSError,ValueError,ET.ParseError) as exc:
        raise RuntimeError('D08_GAZEBO_WORLD_SDF_NOT_READY:'+type(exc).__name__) from exc

def wait_for_native_world(server,world_sdf:Path,env:dict,*,probe=None,
                          evidence_path=None,timeout_s=45.0):
    """Actual native Scene response verifies Gazebo is alive before Nav2.

    A stopped server reports its earliest exit code immediately. The native
    World model is a real SDF fixture; fake data is never published.
    """
    world=inspect_generated_world(world_sdf)
    started=time.monotonic()
    state=dict(world,status='BLOCKED',server_pid=getattr(server,'pid',None),
               native_world_service_verified=False,first_boundary=None,
               native_scene_probe_count=0,nav2_launched_at_probe=False)
    def save():
        if evidence_path is not None:
            Path(evidence_path).write_text(json.dumps(state,indent=2,sort_keys=True)+'\n')
    until=started+timeout_s
    while time.monotonic()<until:
        rc=server.poll()
        if rc is not None:
            state['first_boundary']='D08_GAZEBO_SERVER_EXIT_BEFORE_WORLD_READY'
            state['server_exit_code']=rc
            save()
            raise RuntimeError(state['first_boundary']+':exit_code='+str(rc))
        try:
            cp=(probe() if probe is not None else subprocess.run(
                ['gz','service','-s',WORLD_SVC,'--reqtype','gz.msgs.Empty',
                 '--reptype','gz.msgs.Scene','--timeout','1600','--req',' '],
                env=env,capture_output=True,text=True,check=False,timeout=4))
            state['native_scene_probe_count']+=1
            if (cp.returncode==0 and 'model {' in cp.stdout and
                'name: "axia_p2_g07_obstacle"' in cp.stdout):
                state.update(status='READY',native_world_service_verified=True,
                             elapsed_sec=round(time.monotonic()-started,3),
                             first_boundary=None)
                save()
                return state
            state['last_native_probe']=(cp.stderr or cp.stdout)[-350:]
        except subprocess.TimeoutExpired:
            state['last_native_probe']='D08_GZ_SERVICE_CALL_TIMED_OUT'
        rc=server.poll()
        if rc is not None:
            state['first_boundary']='D08_GAZEBO_SERVER_EXIT_BEFORE_WORLD_READY'
            state['server_exit_code']=rc
            save()
            raise RuntimeError(state['first_boundary']+':exit_code='+str(rc))
        time.sleep(.2)
    state['first_boundary']='D08_GAZEBO_NATIVE_WORLD_NOT_READY'
    save()
    raise RuntimeError(state['first_boundary']+':service='+WORLD_SVC)
