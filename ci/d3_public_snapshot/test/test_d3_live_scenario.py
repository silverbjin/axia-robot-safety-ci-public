"""RED first: dynamic proxy and one-command classroom scenario orchestrator."""
import json
from unittest.mock import Mock

import pytest

from axia_d3_demo.scenario import (
    validate_path, build_pose_command, pose_ok, fault_ok, latest_live_state,
    dynamic_verified, ScenarioDriver,
)


def test_valid_short_instructor_path():
    assert validate_path('tb3_sandbox', (1.0, 0.0), (1.0, 1.0)) == ('tb3_sandbox', (1.0, 0.0), (1.0, 1.0))


@pytest.mark.parametrize('start,end', [((0, 0), (0, 0)), ((0, 0), (5, 0)), ((float('nan'), 0), (1, 0)), ((0, 0), (99, 0))])
def test_bad_path_blocks(start, end):
    with pytest.raises(ValueError):
        validate_path('tb3_sandbox', start, end)


def test_pose_service_command_is_subprocess_array_without_shell():
    cmd = build_pose_command('tb3_sandbox', 'd3_pedestrian_proxy', 1.25, -0.2)
    assert cmd[:3] == ['gz', 'service', '-s']
    assert cmd[3] == '/world/tb3_sandbox/set_pose'
    assert 'gz.msgs.Pose' in cmd
    assert 'gz.msgs.Boolean' in cmd
    assert 'd3_pedestrian_proxy' in cmd[-1]
    assert '1.25' in cmd[-1]


def test_pose_service_requires_positive_response():
    assert pose_ok('data: true\n')
    assert not pose_ok('data: false\n')
    assert not pose_ok('')


def test_fault_service_response_requires_success():
    assert fault_ok('response:\nstd_srvs.srv.Trigger_Response(success=True, message="DROP_SCAN")')
    assert not fault_ok('response:\nstd_srvs.srv.Trigger_Response(success=False, message="FAULT_INJECTION_DISABLED")')
    assert fault_ok('success: true\nmessage: DROP_SCAN')


def stream(now=12.):
    return [
        {'ts_mono': 10.5, 'kind': 'p1_state', 'state': 'NORMAL'},
        {'ts_mono': 11.1, 'kind': 'odom', 'v': 0.12, 'w': 0.0},
    ]


def test_require_live_normal_and_recent_motion():
    assert latest_live_state(stream(), 12.0)
    assert not latest_live_state(stream(), 20.0)
    assert not latest_live_state([{'ts_mono': 11.0, 'kind': 'p1_state', 'state': 'PROTECTIVE_STOP'}, *stream()[-1:]], 11.5)
    assert not latest_live_state([stream()[0], {'ts_mono': 11.1, 'kind': 'odom', 'v': 0., 'w': 0.}], 11.5)


def observed():
    return [
        {'ts_mono': 10., 'kind': 'p1_state', 'state': 'NORMAL'},
        {'ts_mono': 10.1, 'kind': 'odom', 'v': 0.15, 'w': 0.},
        {'ts_mono': 10.2, 'kind': 'stage_spawned', 'name': 'd3_pedestrian_proxy', 'world': 'tb3_sandbox'},
        {'ts_mono': 10.3, 'kind': 'obstacle_visible', 'name': 'd3_pedestrian_proxy'},
        {'ts_mono': 10.4, 'kind': 'obstacle_moved', 'name': 'd3_pedestrian_proxy', 'step': 1},
        {'ts_mono': 10.5, 'kind': 'fault_status', 'mode': 'DROP_SCAN', 'enabled': True},
        {'ts_mono': 10.6, 'kind': 'p1_state', 'state': 'PROTECTIVE_STOP'},
        {'ts_mono': 10.7, 'kind': 'diagnostic', 'name': 'AXIA/P1/SafetySupervisor', 'level': 2},
        {'ts_mono': 10.8, 'kind': 'odom', 'v': 0., 'w': 0.},
        {'ts_mono': 11.9, 'kind': 'odom', 'v': 0., 'w': 0.},
        {'ts_mono': 12.0, 'kind': 'operator_decision', 'choice': 'HOLD'},
    ]


def test_dynamic_verifier_requires_real_movement_event():
    assert dynamic_verified(observed()) == 'DEMO_OBSERVED'
    assert dynamic_verified([e for e in observed() if e['kind'] != 'obstacle_moved']) == 'INCONCLUSIVE'


def test_dynamic_verifier_fault_after_motion():
    es = observed()
    es[4]['ts_mono'], es[5]['ts_mono'] = es[5]['ts_mono'], es[4]['ts_mono']
    es.sort(key=lambda e: e['ts_mono'])
    assert dynamic_verified(es) == 'INCONCLUSIVE'


def test_scenario_dry_run_does_not_call_external_system(tmp_path):
    runner = Mock()
    driver = ScenarioDriver(runner=runner, input_fn=lambda _: 'YES-VISIBLE')
    outcome = driver.run(world='tb3_sandbox', start=(1., 0.), end=(1., 1.), evidence=tmp_path/'events.jsonl',
                         dry_run=True, acknowledge_sim=False, acknowledge_fault=False)
    assert outcome == 'PLAN_ONLY'
    runner.assert_not_called()


def test_no_live_motion_prevents_spawn_and_fault(tmp_path, monkeypatch):
    monkeypatch.setenv('GZ_PARTITION', 'axia_d3_test')
    monkeypatch.setenv('ROS_DOMAIN_ID', '174')
    runner = Mock()
    driver = ScenarioDriver(runner=runner, input_fn=lambda _: 'YES-VISIBLE',
                            evidence_reader=lambda _: [])
    result = driver.run(world='tb3_sandbox', start=(1., 0.), end=(1., 1.), evidence=tmp_path/'events.jsonl',
                        acknowledge_sim=True, acknowledge_fault=True, ready_timeout_s=0.1)
    assert result == 'BLOCKED_NO_LIVE_MOTION'
    runner.assert_not_called()


def test_fault_declined_even_when_sim_approved(tmp_path):
    runner = Mock()
    driver = ScenarioDriver(runner=runner)
    result = driver.run(world='tb3_sandbox', start=(1., 0.), end=(1., 1.), evidence=tmp_path/'events.jsonl',
                        acknowledge_sim=True, acknowledge_fault=False)
    assert result == 'BLOCKED_FAULT_APPROVAL'
    runner.assert_not_called()


def test_preview_only_no_ros_goal_fault(monkeypatch):
    monkeypatch.setenv('GZ_PARTITION','axia_d3_test')
    monkeypatch.setenv('ROS_DOMAIN_ID','174')
    executed = []
    def fake_run(cmd, **kwargs):
        executed.append(cmd)
        if cmd[:3] == ['gz', 'service', '-l']:
            out = '/world/tb3_sandbox/create\n/world/tb3_sandbox/set_pose\n'
        elif cmd[:3] == ['gz', 'service', '-s']:
            out = 'data: true'
        else:
            out = 'Entity creation successful'
        return type('Return', (), {'returncode':0, 'stdout':out, 'stderr':''})()
    driver = ScenarioDriver(runner=fake_run, sleep=lambda _:None)
    assert driver.preview('tb3_sandbox', (1., 0.), (1., 1.), steps=4, duration_s=2., acknowledge_sim=True) == 'PREVIEW_MOVED'
    assert sum(x[:3] == ['gz', 'service', '-s'] for x in executed) == 4
    assert not any('/axia/fault/' in ' '.join(x) or '/cmd_vel' in ' '.join(x) for x in executed)


def test_preview_requires_approval_no_external_calls():
    mock = Mock()
    driver = ScenarioDriver(runner=mock)
    assert driver.preview('tb3_sandbox', (1.,0.), (1.,1.), acknowledge_sim=False) == 'BLOCKED_SIM_APPROVAL'
    mock.assert_not_called()


def test_existing_scan_fault_prevents_second_injection(tmp_path, monkeypatch):
    monkeypatch.setenv('GZ_PARTITION','axia_d3_test')
    monkeypatch.setenv('ROS_DOMAIN_ID','174')
    from time import monotonic
    now=monotonic()
    evidence=[{'ts_mono':now-.2,'kind':'p1_state','state':'NORMAL'},
              {'ts_mono':now-.1,'kind':'odom','v':.16,'w':0.},
              {'ts_mono':now-.1,'kind':'fault_status','enabled':True,'mode':'DROP_SCAN'}]
    runner=Mock()
    d=ScenarioDriver(runner=runner, evidence_reader=lambda _:evidence)
    result=d.run(world='tb3_sandbox',start=(1.,0.),end=(1.,1.),evidence=tmp_path/'a.jsonl',
                 acknowledge_sim=True, acknowledge_fault=True, ready_timeout_s=.1)
    assert result=='BLOCKED_FAULT_ALREADY_ACTIVE'
    runner.assert_not_called()