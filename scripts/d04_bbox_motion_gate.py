"""Strict frame-to-frame motion gate for real YOLO person detections.

Requires distinct ROS sim timestamps, multiple detections, and pixel displacement.
A single annotated PNG or stationary detection is NOT dynamic evidence.
"""
from __future__ import annotations

def motion_evidence(samples: list[dict], *, min_samples: int = 4,
                    min_sim_span_s: float = 1.5,
                    min_bbox_x_range_px: float = 12.0) -> dict:
    import math
    good = []
    for v in samples:
        try:
            if (v.get("class_name") != "person" or v.get("class_id") != 0
                    or not (0 < float(v["score"]) <= 1)
                    or int(v["stamp_ns"]) <= 0
                    or not math.isfinite(float(v["center_x"]))):
                continue
            good.append({"stamp_ns":int(v["stamp_ns"]),
                         "center_x":float(v["center_x"]),
                         "score":float(v["score"])})
        except (TypeError,KeyError,ValueError):
            continue
    # Reject duplicated timestamps (e.g. the same detection echoed repeatedly).
    unique = {x["stamp_ns"]:x for x in good}
    ordered = sorted(unique.values(),key=lambda x:x["stamp_ns"])
    span = ((ordered[-1]["stamp_ns"]-ordered[0]["stamp_ns"])/1e9
            if len(ordered)>1 else 0.0)
    motion = (max(x["center_x"] for x in ordered)-min(x["center_x"] for x in ordered)
              if ordered else 0.0)
    return {
        "passed": len(ordered)>=min_samples and
                  span>=min_sim_span_s and
                  motion>=min_bbox_x_range_px,
        "person_detection_samples":len(ordered),
        "sim_time_span_s":round(span,3),
        "bbox_center_x_range_px":round(motion,3),
        "min_samples":min_samples,
        "min_sim_span_s":min_sim_span_s,
        "min_bbox_x_range_px":min_bbox_x_range_px,
        "values":ordered[:250],
    }
