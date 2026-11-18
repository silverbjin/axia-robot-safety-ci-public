"""Owner blank Gazebo 3D viewport: real exported world lacked SceneBroadcaster.
Original Owner run_20261118T113915Z_FXDexn; RED L0 only.
"""
import json,sys,zipfile
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
sys.path.insert(0,str(ROOT/'d08/scripts'))
from d08_scene_broadcaster import validate_d08_scene_world,validate_native_scene_reply
from d08_compact_evidence import create_compact_evidence

def make_world(plugin_count=1):
    plugin='<plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>'
    return '<sdf version="1.6"><world name="default">'+plugin*plugin_count+'<model name="axia_p2_g07_obstacle"/></world></sdf>'

def test_owner_actual_world_missing_broadcaster_fails_closed(tmp_path):
    p=tmp_path/'actual_world.sdf'
    p.write_text(make_world(0))
    with pytest.raises(ValueError,match='D08_GAZEBO_SCENE_BROADCASTER_MISSING'):
        validate_d08_scene_world(p)
    p.write_text(make_world(1))
    assert validate_d08_scene_world(p)['scene_broadcaster_count']==1
    p.write_text(make_world(2))
    with pytest.raises(ValueError,match='D08_GAZEBO_SCENE_BROADCASTER_DUPLICATE'):
        validate_d08_scene_world(p)

def test_real_native_scene_requires_robot_and_obstacle_not_empty_window():
    with pytest.raises(ValueError,match='D08_GAZEBO_NATIVE_SCENE_MODELS_MISSING'):
        validate_native_scene_reply('name: "default"\nmodel { name: "ground_plane" }')
    s='name: "default"\nmodel { name: "axia_d08_ci_waffle" }\nmodel { name: "axia_p2_g07_obstacle" }'
    x=validate_native_scene_reply(s)
    assert x['native_scene_service_verified'] is True
    assert x['robot_model_in_native_scene'] and x['physical_person_model_in_native_scene']
    assert x['gui_pixels_verified'] is False

def test_same_generated_world_scene_contract_and_real_ci_witness():
    source=(ROOT/'d08/scripts/d08_public_gazebo_l2.py').read_text()
    assert "'headless:=false'" in source
    assert 'validate_d08_scene_world(' in source
    assert 'validate_native_scene_reply(' in source
    w=(ROOT/'.github/workflows/d08-main-no-goal-real-gazebo-l2.yml').read_text()
    assert 'D08_REAL_GAZEBO_SCENE_BROADCASTER_L2_PASS' in w
    assert "v['native_scene']['native_scene_service_verified'] is True" in w

def test_compact_original_failure_keep_and_no_large_dependency(tmp_path):
    run=tmp_path/'run';ev=run/'live_evidence';ev.mkdir(parents=True)
    for directory,name in [('assets','onnx.nupkg'),('src','source.py'),('yolo_ws/build','huge.o')]:
        p=run/directory/name;p.parent.mkdir(parents=True);p.write_bytes(b'X'*20000)
    (ev/'verdict.json').write_text(json.dumps({'status':'BLOCKED','first_boundary':'D08_FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS','gap_sec':.546644}))
    (ev/'amcl_receive_timing.json').write_text('{}')
    (ev/'d08_official_nav2_one_world.log').write_text('start\n'+'noise\n'*3000+'D08_FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS\n'+'noise\n'*3000)
    for i in ('0000','0001','0007'):
        p=ev/'owner_replan_cycles'/f'cycle_{i}'/'verdict.json';p.parent.mkdir(parents=True)
        p.write_text(json.dumps({'status':'HOLD' if i=='0007' else 'D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL','first_boundary':'0.546644' if i=='0007' else None}))
    target=tmp_path/'compact.zip'
    verdict=create_compact_evidence(run,target)
    assert verdict['status']=='D08_COMPACT_EVIDENCE_READY'
    with zipfile.ZipFile(target) as z:
        paths=z.namelist()
        assert 'SHA256SUMS' in paths
        assert 'live_evidence/owner_replan_cycles/cycle_0007/verdict.json' in paths
        assert 'live_evidence/owner_replan_cycles/cycle_0000/verdict.json' in paths
        assert any('error_context' in x for x in paths)
        assert not any(x.startswith(('assets/','src/','yolo_ws/')) for x in paths)
        assert all(len(z.read(x))<256*1024 for x in paths)
    assert target.stat().st_size<10000


def test_owner_eight_cycle_real_gui_regression_and_first_scan_source_gap():
    """Owner's 8th cycle failed at a true 546.644ms receive gap."""
    source=(ROOT/'d08/scripts/d08_public_gazebo_l2.py').read_text()
    workflow=(ROOT/'.github/workflows/d08-main-no-goal-real-gazebo-l2.yml').read_text()
    observer=(ROOT/'d08/harness/d08_same_world_replan.py').read_text()
    assert '--ci-owner-repro' in source
    assert 'D08_CI_REAL_GUI_EIGHT_REPEAT_PATHS_L2_PASS' in source
    assert 'D08_CI_REAL_GUI_EIGHT_REPEAT_PATHS_L2_PASS' in workflow
    assert 'ci_owner_replan_cycles' in workflow
    assert 'first_scan_receive_gap(' in observer
    assert 'first_scan_timing_boundary' in observer
    from d08_scan_gap_trace import first_scan_receive_gap
    v=first_scan_receive_gap([(5.0,100_000_000),
                              (5.546644,200_000_000)])
    assert v['receive_gap_sec']==.546644
    assert v['header_sim_gap_sec']==.1
    assert v['publisher_rmw_gap_measured'] is False
