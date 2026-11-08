import json
from pathlib import Path
from unittest.mock import patch

import pytest

from axia_d3_demo.cli import build_spawn_command, cli_main, validate_stage


def test_stage_requires_explicit_world():
    with pytest.raises(ValueError):
        validate_stage('','1.0','2.0')


@pytest.mark.parametrize('world', ['../other','/world/default','world;rm','', 'foo space'])
def test_world_is_safe_identifier(world):
    with pytest.raises(ValueError):
        validate_stage(world, '1.0', '2.0')


@pytest.mark.parametrize('x,y', [('nan','2'), ('inf','2'), ('1e999','2'), ('0','-100'), ('x','1')])
def test_invalid_stage_coordinates_blocked(x,y):
    with pytest.raises(ValueError):
        validate_stage('tb3_sandbox', x, y)


def test_spawn_command_is_argument_array_without_shell():
    cmd=build_spawn_command('tb3_sandbox',1.5,-0.2,'/tmp/proxy.sdf')
    assert cmd == ['ros2','run','ros_gz_sim','create','-world','tb3_sandbox','-file','/tmp/proxy.sdf','-name','d3_pedestrian_proxy','-x','1.5','-y','-0.2','-z','0.0']


def test_plan_does_not_execute_external_command(capsys):
    with patch('subprocess.run') as run:
        rc=cli_main(['plan'])
    assert rc == 0
    run.assert_not_called()
    assert 'SCAN_DROP' in capsys.readouterr().out


def test_stage_without_sim_ack_is_blocked(tmp_path):
    with patch('subprocess.run') as run:
        rc=cli_main(['stage','--world','tb3_sandbox','--x','1','--y','0','--evidence',str(tmp_path/'a.jsonl')])
    assert rc != 0
    run.assert_not_called()
    assert not (tmp_path/'a.jsonl').exists()


def test_confirm_requires_prior_spawn_and_explicit_ack(tmp_path):
    e=tmp_path/'a.jsonl'
    assert cli_main(['confirm','--evidence',str(e),'--ack-visible'])!=0
    e.write_text(json.dumps({'ts_mono': 10.0,'kind':'stage_spawned','world':'tb3_sandbox','name':'d3_pedestrian_proxy'})+'\n')
    assert cli_main(['confirm','--evidence',str(e)])!=0


def test_decision_rejects_unverified_stop(tmp_path):
    e=tmp_path/'a.jsonl'
    with patch('subprocess.run') as run:
        assert cli_main(['decision','--evidence',str(e),'--choice','HOLD','--ack-operator'])!=0
        run.assert_not_called()
    assert not e.exists()


def test_verify_inconclusive_returns_code_three(tmp_path):
    assert cli_main(['verify','--evidence',str(tmp_path/'notfound.jsonl')]) == 3


def test_stage_uses_exact_ros_gz_command_and_records_success(tmp_path, monkeypatch):
    monkeypatch.setenv('GZ_PARTITION', 'axia_d3_test')
    monkeypatch.setenv('ROS_DOMAIN_ID', '174')
    evidence = tmp_path/'evidence.jsonl'
    with patch('subprocess.run') as run:
        run.return_value.returncode = 0
        run.return_value.stdout = 'OK'
        run.return_value.stderr = ''
        rc = cli_main(['stage','--world','tb3_sandbox','--x','1','--y','0',
                       '--ack-sim-only','--evidence',str(evidence)])
    assert rc == 0
    cmd=run.call_args.args[0]
    assert cmd[:4] == ['ros2','run','ros_gz_sim','create']
    assert cmd[cmd.index('-world')+1] == 'tb3_sandbox'
    assert Path(cmd[cmd.index('-file')+1]).is_file()
    assert 'stage_spawned' in evidence.read_text()


def test_stage_nonzero_exit_never_records_confirmation(tmp_path, monkeypatch):
    monkeypatch.setenv('GZ_PARTITION','axia_d3_test')
    monkeypatch.setenv('ROS_DOMAIN_ID','174')
    evidence=tmp_path/'evidence.jsonl'
    with patch('subprocess.run') as run:
        run.return_value.returncode=1
        run.return_value.stdout=''
        run.return_value.stderr='failed'
        rc=cli_main(['stage','--world','tb3_sandbox','--x','1','--y','0',
                     '--ack-sim-only','--evidence',str(evidence)])
    assert rc==2
    assert not evidence.exists()
