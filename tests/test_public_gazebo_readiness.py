"""Prevent false-negative cold starts before ROS topic type discovery."""
from types import SimpleNamespace
from scripts import gazebo_readonly_baseline as probe


def test_transient_unpublished_topic_retries_until_message(monkeypatch):
    attempts = []
    def fake_run(cmd, **kwargs):
        attempts.append(cmd)
        if len(attempts) <= 2:
            return SimpleNamespace(returncode=1, stdout='WARNING: topic [/clock] does not appear to be published yet',
                                   stderr='Could not determine the type for the passed topic')
        return SimpleNamespace(returncode=0, stdout='clock: 1\n', stderr='')
    monkeypatch.setattr(probe.subprocess, 'run', fake_run)
    monkeypatch.setattr(probe.time, 'sleep', lambda _: None)
    outcome = probe.inspect_topic('/clock', {}, 3.0)
    assert outcome['received'] is True
    assert outcome['attempts'] == 3
    assert len(attempts) == 3


def test_unpublished_topic_until_deadline_is_not_pass(monkeypatch):
    state = {'now': 0.0, 'attempts': 0}
    monkeypatch.setattr(probe.time, 'monotonic', lambda: state['now'])
    monkeypatch.setattr(probe.time, 'sleep', lambda dt: state.__setitem__('now', state['now']+dt))
    def fake_run(cmd, **kwargs):
        state['attempts'] += 1
        return SimpleNamespace(returncode=1, stdout='WARNING: topic [/clock] does not appear to be published yet',
                               stderr='Could not determine the type for the passed topic')
    monkeypatch.setattr(probe.subprocess, 'run', fake_run)
    result = probe.inspect_topic('/clock', {}, 0.9)
    assert result['received'] is False
    assert result['error'] == 'READINESS_TIMEOUT'
    assert state['attempts'] >= 2
    assert state['now'] >= 0.9


def test_non_transient_ros_cli_error_fails_closed(monkeypatch):
    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=2, stdout='', stderr='unrecognized arguments: --once')
    monkeypatch.setattr(probe.subprocess, 'run', fake_run)
    result = probe.inspect_topic('/clock', {}, 3.0)
    assert result['received'] is False
    assert result['error'] == 'ROS_CLI_ERROR'
    assert len(calls) == 1
