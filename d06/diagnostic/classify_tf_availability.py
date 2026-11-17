"""Strict Task01 original Advanced TF nonblocking readiness evidence.

Zero-timeout canTransform immediately BEFORE and AFTER original official TF
invocation is a diagnostic observation, not proof of the first RMW source
gap or that the transform appeared at a particular instant in the loop.
"""
from __future__ import annotations


def _hold(reason, **extra):
    return dict(
        status=reason,
        root_cause_proven=False,
        scheduler_wait_proven=False,
        tf_wait_root_cause_proven=False,
        source_publication_to_monotonic_alignment_proven=False,
        gate_c_authorized=False,
        cm120_release_pass=False,
        certified_estop=False,
        **extra,
    )


def classify(artifact):
    if not isinstance(artifact, dict):
        return _hold("TF_AVAILABILITY_EVIDENCE_INVALID_HOLD")
    if artifact.get("cm120_release_pass") is not False or             artifact.get("root_cause_proven") is not False:
        return _hold("TF_AVAILABILITY_RELEASE_FLAG_INVALID_HOLD")
    # A pre/post nonblocking TF observation without the actual first
    # publisher-source breach must NEVER be presented as same-gap evidence.
    # In the real #44073078458 Moving Goal, max source=117.998ms and
    # TF readiness exists, but the selected >120ms first pair is ABSENT.
    # Keep the comparison strictly in the RMW source interval domain.
    first = artifact.get("first_gap")
    if (not isinstance(first, dict) or
            type(first.get("rmw_source_gap_ns")) is not int or
            first["rmw_source_gap_ns"] <= 120_000_000):
        return _hold("FIRST_SOURCE_GAP_NOT_REPRODUCED_HOLD")
    raw = artifact.get("tf_availability")
    if raw is None:
        return _hold("TF_AVAILABILITY_PROBE_NOT_PRESENT_HOLD")
    if not isinstance(raw, dict):
        return _hold("TF_AVAILABILITY_EVIDENCE_INVALID_HOLD")
    if raw.get("status") != "TF_AVAILABILITY_READ_ONLY_RECORDED_HOLD":
        return _hold(raw.get("status", "TF_AVAILABILITY_EVIDENCE_INVALID_HOLD"))
    spans = raw.get("spans")
    if not isinstance(spans, list) or not 1 <= len(spans) <= 40:
        return _hold("TF_AVAILABILITY_PROBE_NOT_PRESENT_HOLD")
    transition = 0
    for s in spans:
        if not isinstance(s, dict) or set(s) != {
            "pre_available", "post_available", "pre_probe_wall_ns",
            "post_probe_wall_ns", "original_tf_call_wall_ns",
            "pre_start_rel_observer_ns", "post_end_rel_observer_ns",
        }:
            return _hold("TF_AVAILABILITY_EVIDENCE_INVALID_HOLD")
        if type(s["pre_available"]) is not bool or                 type(s["post_available"]) is not bool:
            return _hold("TF_AVAILABILITY_EVIDENCE_INVALID_HOLD")
        values = [s[k] for k in (
            "pre_probe_wall_ns", "post_probe_wall_ns",
            "original_tf_call_wall_ns", "pre_start_rel_observer_ns",
            "post_end_rel_observer_ns",
        )]
        if any(type(n) is not int for n in values):
            return _hold("TF_AVAILABILITY_EVIDENCE_INVALID_HOLD")
        pre, post, call, _a, _b = values
        if min(pre, post, call) < 0 or call <= 0:
            return _hold("TF_AVAILABILITY_EVIDENCE_INVALID_HOLD")
        if pre > 10_000_000 or post > 10_000_000:
            return _hold("TF_AVAILABILITY_PROBE_TOO_SLOW_HOLD")
        if s["pre_available"]:
            return _hold("TF_AVAILABLE_AT_ENTRY_CAUSE_UNPROVEN_HOLD")
        if s["post_available"]:
            transition += 1
    if transition:
        return _hold("TF_INITIAL_UNAVAILABLE_LATER_AVAILABLE_CANDIDATE_HOLD",
                     same_call_transition_count=transition)
    return _hold("TF_UNAVAILABLE_BOTH_ENDPOINTS_CAUSE_UNPROVEN_HOLD",
                 same_call_transition_count=0)
