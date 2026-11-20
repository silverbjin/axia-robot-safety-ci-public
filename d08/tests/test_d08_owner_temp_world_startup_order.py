"""Actual Owner 2026-11-18 first startup failure: gz exit 255 before Xacro finished.
Deterministic old race reproduction is L0 ONLY. CI real Gazebo L2 is separate.
"""
from __future__ import annotations
import subprocess,sys,threading,time
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_one_world_official_nav2_launch import make_official_nav2_command

def fixture(tmp_path):
    w=tmp_path/'actual_world.sdf'
    w.write_text('<sdf version="1.9"><world name="default"><plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/><model name="axia_p2_g07_obstacle"><link name="obstacle_link"><collision name="obstacle_collision"/></link></model></world></sdf>')
    r=tmp_path/'actual_waffle.sdf'
    r.write_text('<sdf version="1.9"><model name="waffle"><link name="camera_link"><sensor name="axia_d08_registered_rgbd" type="rgbd_camera"><gz_frame_id>axia_d08_rgbd_optical</gz_frame_id></sensor><sensor name="hls_lfcd_lds" type="gpu_lidar"/></link></model></sdf>')
    return w,r

def test_red_legacy_temp_sdf_open_before_xacro_complete(tmp_path):
    p=tmp_path/'nav2_delayed.sdf'
    finished=threading.Event()
    def producer():
        time.sleep(.15)
        p.write_text('<sdf version="1.9"><world name="default"/></sdf>')
        finished.set()
    t=threading.Thread(target=producer,daemon=True);t.start()
    cp=subprocess.run([sys.executable,'-c',
        'import pathlib,sys; p=pathlib.Path(sys.argv[1]); sys.exit(0 if p.is_file() and p.stat().st_size else 255)',
        str(p)],capture_output=True,timeout=3)
    assert cp.returncode==255 and not finished.is_set()
    t.join(2)
    assert finished.is_set() and p.stat().st_size>0

def test_official_nav2_does_not_start_legacy_racing_server(tmp_path):
    w,r=fixture(tmp_path)
    cmd=make_official_nav2_command(w,r)
    assert 'use_simulator:=False' in cmd,'D08_RED_LEGACY_NAV2_SPAWNS_RACING_TEMP_SDF_SERVER'
    assert 'use_composition:=False' in cmd
    assert sum(a.startswith('world:=') for a in cmd)==1

def test_generated_sdf_must_be_valid_before_real_server_start(tmp_path):
    from d08_world_startup import inspect_generated_world
    w,_=fixture(tmp_path)
    check=inspect_generated_world(w)
    assert check['world_name']=='default' and check['bytes']>0 and len(check['sha256'])==64
    w.unlink()
    with pytest.raises(RuntimeError,match='D08_GAZEBO_WORLD_SDF_NOT_READY'):
        inspect_generated_world(w)
    w.write_text('<sdf><world')
    with pytest.raises(RuntimeError,match='D08_GAZEBO_WORLD_SDF_NOT_READY'):
        inspect_generated_world(w)

def test_dead_server_must_block_before_contact_or_rgbd_timeout(tmp_path):
    from d08_world_startup import wait_for_native_world
    w,_=fixture(tmp_path)
    class Exited:
        pid=1234
        def poll(self):return 255
    called=[]
    with pytest.raises(RuntimeError,match='D08_GAZEBO_SERVER_EXIT_BEFORE_WORLD_READY'):
        wait_for_native_world(Exited(),w,env={},probe=lambda: called.append(1))
    assert not called

def test_owner_and_ci_use_same_ordered_launch():
    runner=(ROOT/'d08/scripts/d08_public_gazebo_l2.py').read_text()
    assert "wait_for_native_world(" in runner
    assert "'gz','sim','-r','-s'" in runner
    assert 'D08_GAZEBO_SERVER_EXIT_BEFORE_WORLD_READY' in runner
    assert runner.index('wait_for_native_world(')<runner.index('make_official_nav2_command(')
    launch=(ROOT/'d08/harness/d08_one_world_official_nav2_launch.py').read_text()
    assert "'use_simulator:=False'" in launch
    workflow=(ROOT/'.github/workflows/d08-main-no-goal-real-gazebo-l2.yml').read_text()
    assert 'D08_REAL_GAZEBO_TEMPFILE_RED_REPRODUCED' in workflow
    assert 'D08_GAZEBO_WORLD_READY_BEFORE_NAV2_L2_PASS' in workflow
    assert "v['startup_world']['native_world_service_verified'] is True" in workflow

def test_compact_owner_saves_first_gazebo_exit_without_build_assets(tmp_path):
    import json,zipfile
    sys.path.insert(0,str(ROOT/'d08/scripts'))
    from d08_compact_evidence import create_compact_evidence
    run=tmp_path/'owner_run';e=run/'live_evidence';e.mkdir(parents=True)
    (e/'gazebo_startup.json').write_text(json.dumps({
        'status':'BLOCKED','first_boundary':'D08_GAZEBO_SERVER_EXIT_BEFORE_WORLD_READY',
        'server_exit_code':255}))
    (e/'gazebo_server.log').write_text(
        'Unable to find or download file\n'+'startup detail\n'*1000)
    big=run/'assets'/'onnxruntime.nupkg';big.parent.mkdir()
    big.write_bytes(b'X'*100000)
    archive=tmp_path/'diagnostics.zip'
    create_compact_evidence(run,archive)
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        assert 'live_evidence/gazebo_startup.json' in names
        assert 'logs/gazebo_server_error_context.txt' in names
        assert all(not x.startswith('assets/') for x in names)
        assert b'D08_GAZEBO_SERVER_EXIT_BEFORE_WORLD_READY' in z.read(
            'live_evidence/gazebo_startup.json')
    assert archive.stat().st_size<10000
