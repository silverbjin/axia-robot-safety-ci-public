import json
import math
from pathlib import Path

import pytest

from axia_d3_demo.contract import append_event, evaluate_events, read_events


def sample():
    return [
        {'ts_mono': 10.0, 'kind': 'p1_state', 'state': 'NORMAL'},
        {'ts_mono': 10.2, 'kind': 'odom', 'v': 0.14, 'w': 0.0},
        {'ts_mono': 10.4, 'kind': 'stage_spawned', 'world': 'tb3_sandbox', 'name': 'd3_pedestrian_proxy'},
        {'ts_mono': 10.5, 'kind': 'obstacle_visible', 'name': 'd3_pedestrian_proxy'},
        {'ts_mono': 10.7, 'kind': 'fault_status', 'mode': 'DROP_SCAN', 'enabled': True},
        {'ts_mono': 10.9, 'kind': 'p1_state', 'state': 'PROTECTIVE_STOP'},
        {'ts_mono': 11.1, 'kind': 'diagnostic', 'name': 'AXIA/P1/SafetySupervisor', 'level': 2},
        {'ts_mono': 11.2, 'kind': 'odom', 'v': 0.0, 'w': 0.0},
        {'ts_mono': 12.3, 'kind': 'odom', 'v': 0.0, 'w': 0.0},
        {'ts_mono': 12.5, 'kind': 'operator_decision', 'choice': 'HOLD'},
    ]


def test_happy_path_is_observed_not_certified():
    verdict = evaluate_events(sample())
    assert verdict.status == 'DEMO_OBSERVED'
    assert verdict.certified_estop is False
    assert verdict.contact_free_proven is False
    assert verdict.missing == ()


def test_no_obstacle_visual_confirmation_is_inconclusive():
    events = [e for e in sample() if e['kind'] != 'obstacle_visible']
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_no_motion_before_intrusion_is_inconclusive():
    events = [e for e in sample() if not (e['kind'] == 'odom' and e['ts_mono'] == 10.2)]
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_old_normal_not_accepted_as_active_movement():
    events = sample()
    events[0] = dict(events[0], ts_mono=3.0)
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_fault_must_follow_intrusion():
    events = sample()
    events[4] = dict(events[4], ts_mono=10.45)
    events.sort(key=lambda e: e['ts_mono'])
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_diagnostic_warn_not_sufficient():
    events = sample()
    events[6] = dict(events[6], level=1)
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_diagnostic_other_name_not_sufficient():
    events = sample()
    events[6] = dict(events[6], name='other/diagnostic')
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_boot_safe_to_protective_stop_does_not_count():
    events = sample()
    events[0] = dict(events[0], state='BOOT_SAFE')
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_no_stable_odom_stop_does_not_count():
    events = sample()
    events[8] = dict(events[8], v=0.09)
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_stop_held_less_than_one_second_not_enough():
    events = sample()
    events[8] = dict(events[8], ts_mono=12.0)
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_decision_must_follow_observed_stop():
    events = sample()
    events[9] = dict(events[9], ts_mono=11.5)
    events.sort(key=lambda e: e['ts_mono'])
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_invalid_operator_decision_not_accepted():
    events = sample()
    events[9] = dict(events[9], choice='REARM')
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_fault_disabled_does_not_count():
    events = sample()
    events[4] = dict(events[4], enabled=False)
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_out_of_order_timestamp_rejected():
    events = sample()
    events[5] = dict(events[5], ts_mono=10.0)
    assert evaluate_events(events).status == 'INVALID_EVIDENCE'


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -1, '10', None, True])
def test_bad_monotonic_timestamp_rejected(value):
    events = sample()
    events[0] = dict(events[0], ts_mono=value)
    assert evaluate_events(events).status == 'INVALID_EVIDENCE'


def test_append_and_read_event_preserve_only_allowlisted_fields(tmp_path):
    path = tmp_path / 'evidence.jsonl'
    e = append_event(path, 'p1_state', state='NORMAL', goal_id='sensitive-id', stop_reason='private')
    assert 'goal_id' not in e and 'stop_reason' not in e
    assert 'sensitive-id' not in path.read_text()
    assert read_events(path) == [e]


def test_broken_jsonl_rejected(tmp_path):
    path = tmp_path / 'evidence.jsonl'
    path.write_text('{not json}\n')
    assert evaluate_events(read_events(path)).status == 'INVALID_EVIDENCE'


def test_rejects_forged_unknown_kind():
    events = sample() + [{'ts_mono': 13.1, 'kind': '/cmd_vel', 'v': 0.5}]
    assert evaluate_events(events).status == 'INVALID_EVIDENCE'


def test_visual_confirmation_can_happen_after_manual_gui_inspection():
    events = sample()
    # Actor was created while moving; operator may need a few seconds to inspect GUI.
    events[3] = dict(events[3], ts_mono=14.2)
    for idx in range(4,len(events)):
        events[idx] = dict(events[idx], ts_mono=events[idx]['ts_mono']+4.0)
    assert evaluate_events(events).status == 'DEMO_OBSERVED'


def test_confirmation_without_successful_stage_is_not_evidence():
    events=[e for e in sample() if e['kind'] != 'stage_spawned']
    assert evaluate_events(events).status == 'INCONCLUSIVE'


def test_stop_already_active_before_scan_fault_does_not_prove_fault_response():
    events = sample()
    events.insert(4, {'ts_mono': 10.6, 'kind':'p1_state','state':'PROTECTIVE_STOP'})
    assert evaluate_events(events).status == 'INCONCLUSIVE'
