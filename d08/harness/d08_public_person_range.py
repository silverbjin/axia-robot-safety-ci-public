#!/usr/bin/env python3
"""Read-only public D08 D05-compatible actual ROI status (not safety control).

Does not import or expose the private instructor D05 answer. Runtime accepts
ONLY actual ROS Image/Detection headers and pixels supplied by a ROS observer.
L0 fixtures below do NOT prove physical distance, registration or live YOLO.
"""
from __future__ import annotations
import math
import re
import statistics
from d08_live_readonly_probe import decode_real_depth_roi, stamp


def assess_public_person_range(rgb, depth, det_stamp_ns, det_frame, bbox,
                               monotonic_received: dict, monotonic_now: float,
                               registration_sdf_sha256: str) -> dict:
    """Return VALID or reasoned UNKNOWN. No ROS publishers or cmd_vel."""
    base={"status":"UNKNOWN","distance_m":None,
          "rgb_stamp_ns":stamp(rgb),"depth_stamp_ns":stamp(depth),
          "detection_stamp_ns":int(det_stamp_ns),
          "registration_sdf_sha256":registration_sdf_sha256}
    def unknown(reason):
        return {**base,"reason":reason}
    # Only the *real same-run generated SDF* hash is admissible as registration
    # evidence. The caller must independently prove its RGBD sensor is single
    # and registered; a well-formed hash alone is NOT a proof.
    if not isinstance(registration_sdf_sha256,str) or not re.fullmatch(
            r"[0-9a-f]{64}", registration_sdf_sha256):
        return unknown("REGISTRATION_SDF_EVIDENCE_MISSING")
    if not all(math.isfinite(float(x)) for x in
               (monotonic_now,*monotonic_received.values())):
        return unknown("MONOTONIC_CLOCK_INVALID")
    if (set(monotonic_received)!={"rgb","depth","detection"} or
        any(not 0 <= monotonic_now-monotonic_received[k] <= .5
            for k in ("rgb","depth","detection"))):
        return unknown("INPUT_STALE_OR_FUTURE")
    if not (base["rgb_stamp_ns"]>0 and base["depth_stamp_ns"]>0
            and base["detection_stamp_ns"]>0):
        return unknown("STAMP_MISSING")
    if max(base["rgb_stamp_ns"],base["depth_stamp_ns"],
           base["detection_stamp_ns"])-min(
           base["rgb_stamp_ns"],base["depth_stamp_ns"],
           base["detection_stamp_ns"])>50_000_000:
        return unknown("TRIAD_STAMP_SKEW")
    f=depth.header.frame_id
    if not f or rgb.header.frame_id!=f or det_frame!=f:
        return unknown("OPTICAL_FRAME_MISMATCH")
    if (rgb.width!=depth.width or rgb.height!=depth.height
        or rgb.encoding not in ("rgb8","bgr8")
        or depth.encoding!="32FC1"):
        return unknown("RGB_DEPTH_GEOMETRY_OR_ENCODING")
    try:
        samples=decode_real_depth_roi(depth,bbox)
    except (ValueError,TypeError,OverflowError):
        return unknown("INVALID_DEPTH_OR_BBOX")
    valid=[float(x) for row in samples for x in row
           if math.isfinite(x) and .15<=x<=8.0]
    if len(valid)<8:
        return unknown("INSUFFICIENT_VALID_DEPTH_PIXELS")
    return {**base,"status":"VALID","reason":None,
            "distance_m":round(float(statistics.median(valid)),6),
            "valid_count":len(valid),"valid_fraction":round(len(valid)/16,4),
            "sampling":"16_actual_float32_center_roi",
            "received_age_s":{k:round(monotonic_now-v,6)
                              for k,v in monotonic_received.items()},
            "control_published":False}
