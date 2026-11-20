#!/usr/bin/env python3
"""D08 diagnostic ONLY: precise original rclpy /scan take-complete→callback.

ROS-free helpers. In the *opt-in* observer, the small executor override mirrors
ROS 2 Jazzy rclpy Executor._take_subscription for the ONE /scan subscription.
Other subscriptions use the original rclpy executor method unchanged.
Never claims DDS send time or changes a timeout/Goal/CM/Guard.
"""
from collections import deque
import threading
import time


class TakeTimeline:
    def __init__(self, limit=1024):
        self._events = deque(maxlen=limit)
        self._lock = threading.Lock()
        self.limit = limit
        self.total = 0

    def record(self, stage, source_stamp_ns, *, at=None, take_start=None):
        row = {"stage": stage, "source_stamp_ns": source_stamp_ns,
               "at": time.monotonic() if at is None else at}
        if take_start is not None:
            row["take_call_start_sec"] = take_start
        with self._lock:
            self._events.append(row)
            self.total += 1

    def snapshot(self):
        with self._lock:
            return list(self._events)

    def complete(self):
        with self._lock:
            return self.total < self.limit


def _stamp_ns(msg):
    try:
        stamp = msg.header.stamp
        ns = int(stamp.sec)*1_000_000_000 + int(stamp.nanosec)
        return ns if ns > 0 else None
    except (AttributeError, TypeError, ValueError):
        return None


def build_scan_take_executor(base_executor, invalid_handle, await_or_execute,
                             message_only_callback_type):
    """Build an opt-in /scan-only subclass; no global rclpy monkeypatch."""
    class ScanTakeExecutor(base_executor):
        def __init__(self, timeline, **kwargs):
            super().__init__(**kwargs)
            self._timeline = timeline
            self._observed_scan_sub = None

        def arm_scan(self, sub):
            self._observed_scan_sub = sub

        def _take_subscription(self, sub):
            if sub is not self._observed_scan_sub:
                return super()._take_subscription(sub)
            # ROS 2 Jazzy rclpy.executor.Executor._take_subscription contract.
            # Do not call take_message twice and do not change the callback.
            try:
                with sub.handle:
                    before = time.monotonic()
                    msg_info = sub.handle.take_message(sub.msg_type, sub.raw)
                    taken = time.monotonic()
                    if msg_info is None:
                        return None
                    msg = msg_info[0]
                    stamp = _stamp_ns(msg)
                    self._timeline.record("take_complete", stamp,
                                          at=taken, take_start=before)
                    if sub._callback_type == message_only_callback_type:
                        msg_tuple = (msg,)
                    else:
                        msg_tuple = msg_info

                    async def _execute():
                        self._timeline.record("callback_dispatch", stamp)
                        await await_or_execute(sub.callback, *msg_tuple)
                    return _execute
            except invalid_handle:
                return None

    return ScanTakeExecutor


def classify_source_pair(pair, events, independent_ros_gap_sec):
    """Exact two-header-stamp join; missing/duplicate => HOLD, never PASS."""
    missing = {
        "candidate": "TAKE_DISPATCH_EVIDENCE_INCOMPLETE",
        "exact_source_pair_proven": False,
        "root_cause": "UNDETERMINED",
        "rcl_take_native_timestamp_proven": False,
        "middleware_publish_latency_proven": False,
    }
    if not isinstance(pair, dict):
        return missing
    try:
        before = int(pair["previous_ros_stamp_ns"])
        after = int(pair["current_ros_stamp_ns"])
        p_at = float(pair["previous_host_monotonic_sec"])
        c_at = float(pair["current_host_monotonic_sec"])
        independent = float(independent_ros_gap_sec)
    except (KeyError, ValueError, TypeError):
        return missing
    if before <= 0 or after <= before or c_at <= p_at or independent <= 0:
        return missing
    hits = {}
    for stamp in (before, after):
        for stage in ("take_complete", "callback_dispatch"):
            found = [r for r in events if
                     r.get("source_stamp_ns") == stamp and
                     r.get("stage") == stage]
            if len(found) != 1:
                return missing
            hits[(stamp, stage)] = float(found[0]["at"])
    b_take = hits[(before, "take_complete")]
    c_take = hits[(after, "take_complete")]
    b_dis = hits[(before, "callback_dispatch")]
    c_dis = hits[(after, "callback_dispatch")]
    if not (b_take <= b_dis <= c_dis and
            b_take < c_take <= c_dis and
            b_dis <= p_at + .1 and c_dis <= c_at + .1):
        return missing
    take_gap = c_take-b_take
    callback_gap = c_dis-b_dis
    after_take = c_dis-c_take
    candidate = "TAKE_DISPATCH_UNDETERMINED"
    # Diagnostic classification only: independent process must show a healthy
    # source-matched period, and original callback must actually violate 500ms.
    if independent < .5 and c_at-p_at > .5:
        if take_gap > .5 and after_take < .1:
            candidate = "ORIGINAL_RCL_TAKE_LATE_CANDIDATE"
        elif take_gap <= .5 and after_take > .1:
            candidate = "ORIGINAL_POST_TAKE_DISPATCH_DELAY_CANDIDATE"
    return {
        "candidate": candidate,
        "exact_source_pair_proven": True,
        "root_cause": "UNDETERMINED",
        "take_gap_sec": round(take_gap, 6),
        "callback_dispatch_gap_sec": round(callback_gap, 6),
        "current_take_to_dispatch_sec": round(after_take, 6),
        "previous_take_complete_sec": round(b_take, 6),
        "current_take_complete_sec": round(c_take, 6),
        "previous_callback_dispatch_sec": round(b_dis, 6),
        "current_callback_dispatch_sec": round(c_dis, 6),
        "first_original_observer_gap_sec": round(c_at-p_at, 6),
        "independent_ros_source_gap_sec": round(independent, 6),
        "rcl_take_native_timestamp_proven": False,
        "middleware_publish_latency_proven": False,
        "interpretation": ("take_complete is measured immediately AFTER rclpy "
                           "Subscription.handle.take_message returns; it is "
                           "NOT a separate native rcl_take tracepoint"),
    }
