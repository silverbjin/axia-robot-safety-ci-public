#!/usr/bin/env bash
# Official Jazzy userspace tracing availability check, NOT a cause verdict.
set -eo pipefail
source /opt/ros/jazzy/setup.bash

OUT="results/d08-ros-trace-preflight"
mkdir -p "$OUT"
LOG="$OUT/session.log"
ROS_TRACE_DIR="$PWD/$OUT/trace"
export ROS_TRACE_DIR
mkdir -p "$ROS_TRACE_DIR"
NAME="axia_d08_ci_trace"
started=0
cleanup() {
  if [ "$started" = 1 ]; then
    timeout 20s ros2 trace stop "$NAME" >> "$LOG" 2>&1 || true
  fi
}
trap cleanup EXIT

if ! timeout 20s ros2 run tracetools status > "$OUT/tracetools-status.txt" 2>&1; then
  echo "D08_ROS_TRACE_PREFLIGHT_BLOCKED_STATUS"
  exit 2
fi
if ! grep -q 'Tracing enabled' "$OUT/tracetools-status.txt"; then
  echo "D08_ROS_TRACE_PREFLIGHT_BLOCKED_DISABLED"
  exit 2
fi
if ! timeout 25s ros2 trace start "$NAME" --snapshot-mode > "$LOG" 2>&1; then
  echo "D08_ROS_TRACE_PREFLIGHT_BLOCKED_START"
  tail -c 2400 "$LOG"
  exit 2
fi
started=1
# The small snapshot is a tracing infrastructure canary only. No assertion
# about causal Scan source timestamps or the bridge publisher is made.
if ! timeout 25s ros2 trace record_snapshot "$NAME" >> "$LOG" 2>&1; then
  echo "D08_ROS_TRACE_PREFLIGHT_BLOCKED_SNAPSHOT"
  tail -c 2400 "$LOG"
  exit 2
fi
if ! timeout 25s ros2 trace stop "$NAME" >> "$LOG" 2>&1; then
  echo "D08_ROS_TRACE_PREFLIGHT_BLOCKED_STOP"
  tail -c 2400 "$LOG"
  exit 2
fi
started=0
printf '%s\n' "D08_ROS_TRACE_PREFLIGHT_L2_PASS_NOT_BRIDGE_CAUSALITY" > "$OUT/verdict.txt"
# Record compact, file-backed proof of what the Linux container actually ran.
du -sh "$ROS_TRACE_DIR" > "$OUT/trace-size.txt" 2>&1 || true
echo D08_ROS_TRACE_PREFLIGHT_L2_PASS_NOT_BRIDGE_CAUSALITY
