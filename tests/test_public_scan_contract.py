import pytest
from axia_public_contracts.scan import summarize_receive_gaps


def test_nominal_gaps_and_threshold_boundary():
    report = summarize_receive_gaps([0.0, 0.1, 0.6, 1.11], threshold_sec=0.5)
    assert report['sample_count'] == 3
    assert report['exceedance_count'] == 1
    assert report['largest_gap_sec'] == pytest.approx(0.51)
    assert report['clock_type'] == 'receiver_wall_time'
    assert report['supervisor_callback_verified'] is False


def test_single_message_is_inconclusive_not_pass():
    report = summarize_receive_gaps([10.0], threshold_sec=0.5)
    assert report['status'] == 'INSUFFICIENT_DATA'
    assert report['sample_count'] == 0


@pytest.mark.parametrize('times', [[0.0, 0.0], [1.0, 0.9], [0.0, float('nan')]])
def test_invalid_timestamp_series_is_rejected(times):
    with pytest.raises(ValueError):
        summarize_receive_gaps(times)


def test_threshold_is_not_silently_changed():
    with pytest.raises(ValueError):
        summarize_receive_gaps([0.0, 1.0], threshold_sec=0.0)
