"""Public receiver-wall-time scan interval analysis, NOT Supervisor callback timing."""
from math import ceil, isfinite


def summarize_receive_gaps(timestamps, threshold_sec=0.5):
    """Receiver wall clock intervals only; never promotes to AXIA acceptance."""
    if isinstance(threshold_sec, bool) or not isinstance(threshold_sec, (int, float)) or not isfinite(threshold_sec) or threshold_sec <= 0:
        raise ValueError('threshold_sec must be a finite positive number')
    samples = list(timestamps)
    if any(isinstance(t, bool) or not isinstance(t, (int, float)) or not isfinite(t) for t in samples):
        raise ValueError('timestamps must be finite numbers')
    gaps = []
    for old, new in zip(samples, samples[1:]):
        gap = new - old
        if gap <= 0:
            raise ValueError('timestamps must be strictly increasing')
        gaps.append(gap)
    return {
        'clock_type': 'receiver_wall_time',
        'supervisor_callback_verified': False,
        'threshold_sec': float(threshold_sec),
        'message_count': len(samples),
        'sample_count': len(gaps),
        'exceedance_count': sum(g > threshold_sec for g in gaps),
        'largest_gap_sec': max(gaps) if gaps else None,
        'p99_gap_sec': sorted(gaps)[ceil(len(gaps) * 0.99) - 1] if gaps else None,
        'status': ('INSUFFICIENT_DATA' if not gaps else
                   'EXCEEDS_THRESHOLD' if any(g > threshold_sec for g in gaps) else
                   'WITHIN_THRESHOLD'),
        'gate_accepted': False,
    }
