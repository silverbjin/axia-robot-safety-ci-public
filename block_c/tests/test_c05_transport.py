"""Public ROS educational transport is NOT the private teacher anomaly classifier."""
from pathlib import Path
import sys,json,subprocess
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'transport'))
from event_contract import sample_events,EventGate,validate_event,to_diagnostic_payload


def test_education_levels_and_transport_sample():
    samples=sample_events()
    assert len(samples)==12 and {e['level'] for e in samples}=={'NORMAL','CAUTION','WARNING','INSUFFICIENT_DATA'}
    assert all(validate_event(e) for e in samples)
    assert [to_diagnostic_payload(e)['level'] for e in samples[:4]]==[0,1,2,3]


def test_invalid_trace_not_trusted_as_robot_control():
    e=sample_events()[0]
    with pytest.raises(ValueError,match='no control authority'):
        validate_event({**e,'control_authority':True})
    with pytest.raises(ValueError):validate_event({**e,'certified_estop':True})


def test_clock_separation_and_first_stale():
    gate=EventGate(stale_after_ns=250000000)
    a,b=sample_events()[:2]
    gate.accept(a,arrival_mono_ns=1000000000,arrival_wall_ns=999999999999999999)
    assert gate.stale(1250000001)
    gate.accept(b,arrival_mono_ns=1260000000,arrival_wall_ns=999999999999999999)
    assert not gate.stale(1261000000)
    with pytest.raises(ValueError,match='duplicate'):gate.accept(b,arrival_mono_ns=1270000000,arrival_wall_ns=1)
    with pytest.raises(ValueError,match='out_of_order'):
        gate.accept({**b,'event_id':'older','source_timestamp_ns':0},arrival_mono_ns=1280000000,arrival_wall_ns=1)


def test_only_education_topic_and_readonly_subscriptions():
    bridge=(ROOT/'transport'/'ros_diagnostic_bridge.py').read_text()
    assert "TOPIC='/axia/education/diagnostics'" in (ROOT/'transport'/'event_contract.py').read_text()
    assert "create_publisher(DiagnosticArray,TOPIC,10)" in bridge
    for prohibited in ('send_goal_async','create_publisher(Twist','/cmd_vel','/navigate_to_pose','/axia/fault/inject','create_client('):
        assert prohibited not in bridge
    assert "create_subscription(String,'/axia/safety/state'" in bridge
    assert "create_subscription(String,'/axia/fault/status'" in bridge


def test_sample_jsonl_and_source_provenance():
    data=[json.loads(x) for x in (ROOT/'transport'/'sample_events.jsonl').read_text().splitlines()]
    assert data==sample_events()
    assert all(e['source']=='SYNTHETIC_COURSE_FIXTURE' for e in data)
