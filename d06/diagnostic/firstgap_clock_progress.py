"""Same-run /clock *subscriber* receive-time vs CM first observer window.

Only numeric, relative timestamps leave CI. A ROS /clock sidecar cannot
prove the exact private tf2 Buffer::clock_->now() or the RMW publisher clock.
This is diagnostic ONLY; no Goal authorization / safety release.
"""
from __future__ import annotations

import math


MAX_RAW=50_000
MAX_PUBLIC=96


def _hold(status):
    return dict(
        status=status, clock_causality_proven=False,
        tf_buffer_clock_progress_proven=False,
        source_publication_to_monotonic_alignment_proven=False,
        cm120_release_pass=False, root_cause_proven=False,
        slow_sim_progress_candidate=False, samples=[],
        observer_pair_clock_sample_count=0,
    )


def summarize(rows, first_observer_mono_ns, second_observer_mono_ns):
    """Two MONOTONIC observer timestamps with same-run /clock callback rows.

    Each row is an in-memory dict {mono_ns, sim_ns}. Other raw fields such as
    frame, private source, name, ROS message, callback IDs are NEVER copied.
    """
    if (type(first_observer_mono_ns) is not int or
            type(second_observer_mono_ns) is not int or
            first_observer_mono_ns <= 0 or
            not 0 < second_observer_mono_ns-first_observer_mono_ns <= 1_000_000_000 or
            not isinstance(rows,list) or not 1<=len(rows)<=MAX_RAW):
        return _hold("CLOCK_INVALID_INPUT_HOLD")

    validated=[]
    for row in rows:
        if not isinstance(row,dict):
            return _hold("CLOCK_INVALID_INPUT_HOLD")
        mono,sim=row.get("mono_ns"),row.get("sim_ns")
        if (type(mono) is not int or type(sim) is not int or
                not 0<mono<10**20 or not 0<=sim<10**20):
            return _hold("CLOCK_INVALID_INPUT_HOLD")
        validated.append((mono,sim))
    if any(b[0]<=a[0] or b[1]<a[1]
            for a,b in zip(validated,validated[1:])):
        return _hold("CLOCK_REWIND_OR_BAD_ORDER_HOLD")

    lo=max((i for i,(mono,sim) in enumerate(validated)
            if mono<=first_observer_mono_ns),default=None)
    hi=next((i for i,(mono,sim) in enumerate(validated)
             if mono>=second_observer_mono_ns),None)
    if (lo is None or hi is None or hi<=lo or
            first_observer_mono_ns-validated[lo][0] > 200_000_000 or
            validated[hi][0]-second_observer_mono_ns > 200_000_000):
        return _hold("CLOCK_WINDOW_UNBRACKETED_HOLD")
    inside=[x for x in validated if
            first_observer_mono_ns<=x[0]<=second_observer_mono_ns]
    if len(inside)<2:
        return _hold("CLOCK_WINDOW_INSUFFICIENT_SAMPLES_HOLD")

    sample=validated[lo:hi+1]
    duration=inside[-1][0]-inside[0][0]
    if duration<=0:
        return _hold("CLOCK_WINDOW_INVALID_DURATION_HOLD")
    sim_advance=inside[-1][1]-inside[0][1]
    ratio=round(sim_advance/duration,6)
    max_gap=max(b[0]-a[0] for a,b in zip(sample,sample[1:]))
    if len(sample)>MAX_PUBLIC:
        # Preserve first+last bracket. Evenly select in between; no causal
        # claim is permitted because the probe may be downsampled.
        import math
        idx=[round(i*(len(sample)-1)/(MAX_PUBLIC-1))
             for i in range(MAX_PUBLIC)]
        output=[sample[i] for i in idx]
        sampled=True
    else:
        output=sample
        sampled=False

    return dict(_hold("CLOCK_OBSERVER_WINDOW_BRACKETED_HYPOTHESIS_ONLY"),
        observer_pair_clock_sample_count=len(inside),
        sample_count_raw=len(sample),
        sampled=sampled,
        observed_host_window_ns=duration,
        observed_sim_advance_ns=sim_advance,
        sim_to_wall_progress_ratio=ratio,
        max_observed_clock_subscriber_gap_ns=max_gap,
        slow_sim_progress_candidate=(ratio<0.25 and len(inside)>=4),
        samples=[dict(mono_rel_first_observer_ns=m-first_observer_mono_ns,
                      sim_rel_first_probe_ns=sim-sample[0][1])
                 for m,sim in output])
