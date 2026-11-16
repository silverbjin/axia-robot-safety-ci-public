#!/usr/bin/env python3
"""Pure, read-only cylinder-vs-LaserScan geometry check for G07 teaching.

Consumes a *same-stamp* LaserScan snapshot and a world->base_scan
pose at that stamp. This is an aid for identifying an initial mismatch,
NOT proof that all 3D scene meshes and lidar points coincide.
No ROS import, Gazebo launch, Goal, cmd_vel or safety verdict.
"""
from __future__ import annotations
import math


def _unverified(reason: str) -> dict:
    return {"status": "UNVERIFIED", "reason": reason,
            "formal_safety_accepted": False}


def _wrapped(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def compare_cylinder_hit(scan: dict, pose: dict | None, obstacle: dict | None,
                         tolerance_m: float = 0.12,
                         max_stamp_delta_s: float = 0.05) -> dict:
    """Compare one ray to a known vertical collision cylinder in the scan plane.

    Coordinates of pose and obstacle MUST be from the same world reference,
    with pose giving world->scan origin/yaw sampled at the scan timestamp.
    The scan frame ID must agree. Other nearer world obstacles can occlude
    the cylinder; unmatched does not automatically imply a sensor bug.
    """
    if not isinstance(scan, dict) or not isinstance(pose, dict) or not isinstance(obstacle, dict):
        return _unverified("MISSING_OR_UNTRUSTED_SNAPSHOT")
    try:
        if scan["frame_id"] != pose["frame_id"]:
            return _unverified("SCAN_FRAME_AND_TF_CHILD_MISMATCH")
        scan_t, pose_t = float(scan["stamp_s"]), float(pose["stamp_s"])
        if not math.isfinite(scan_t) or not math.isfinite(pose_t) or abs(scan_t - pose_t) > max_stamp_delta_s:
            return _unverified("SCAN_TF_TIMESTAMP_NOT_ALIGNED")
        sx, sy, sz = float(pose["x"]), float(pose["y"]), float(pose["z"])
        yaw = float(pose["yaw"])
        cx, cy, radius = float(obstacle["x"]), float(obstacle["y"]), float(obstacle["radius"])
        z_min, z_max = float(obstacle["z_min"]), float(obstacle["z_max"])
        angle_min, increment = float(scan["angle_min"]), float(scan["angle_increment"])
        ranges = scan["ranges"]
        if not ranges or increment <= 0 or radius <= 0 or tolerance_m <= 0:
            return _unverified("INVALID_RAY_OR_CYLINDER_SCHEMA")
        if not z_min <= sz <= z_max:
            return _unverified("CYLINDER_OUTSIDE_LIDAR_HEIGHT")
        if not all(math.isfinite(x) for x in (sx, sy, sz, yaw, cx, cy, radius, increment)):
            return _unverified("NONFINITE_GEOMETRY")
        bearing = _wrapped(math.atan2(cy - sy, cx - sx) - yaw)
        beam = min(range(len(ranges)),
                   key=lambda i: abs(_wrapped(angle_min + i * increment - bearing)))
        beam_bearing = _wrapped(angle_min + beam * increment)
        if abs(_wrapped(beam_bearing - bearing)) > increment:
            return _unverified("TARGET_NOT_WITHIN_SCAN_FOV")
        dx, dy = math.cos(yaw + angle_min + beam * increment), math.sin(yaw + angle_min + beam * increment)
        ox, oy = sx - cx, sy - cy
        b, c = 2 * (dx * ox + dy * oy), ox * ox + oy * oy - radius * radius
        discriminant = b * b - 4 * c
        if discriminant < 0:
            return _unverified("CLOSEST_RAY_MISSES_CYLINDER")
        predicted = (-b - math.sqrt(discriminant)) / 2
        if predicted < 0:
            return _unverified("RAY_STARTS_INSIDE_OR_BEYOND_CYLINDER")
        observed = float(ranges[beam])
        result = {"beam_index": beam, "expected_range_m": round(predicted, 5),
                  "observed_range_m": observed, "delta_m": None,
                  "formal_safety_accepted": False}
        if not math.isfinite(observed):
            result.update(status="NOT_MATCHED_NEEDS_SCENE_REVIEW", reason="NONFINITE_OBSERVED_RANGE")
        else:
            delta = abs(observed - predicted)
            result["delta_m"] = round(delta, 5)
            result["status"] = ("CONSISTENT_CYLINDER_HIT" if delta <= tolerance_m
                                else "NOT_MATCHED_NEEDS_SCENE_REVIEW")
            if delta > tolerance_m:
                result["reason"] = "VERIFY_OCCLUSION_COLLISION_OR_TF_BEFORE_ADJUSTING_MODEL"
        return result
    except (KeyError, TypeError, ValueError, IndexError, OverflowError, ZeroDivisionError):
        return _unverified("INCOMPLETE_INVALID_OR_UNALIGNED_SOURCE")


if __name__ == "__main__":
    raise SystemExit("Import compare_cylinder_hit into an offline validator; live ROS/Gazebo not run.")
