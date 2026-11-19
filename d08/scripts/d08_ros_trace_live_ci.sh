#!/usr/bin/env bash
# Scoped CI-only trace around ACTUAL D08 public no-Goal Gazebo L2.
# 500ms/CM/Guard criterion UNCHANGED; trace availability never a safety PASS.
set -Eeuo pipefail
source /opt/ros/jazzy/setup.bash
MODE="$1"
OUT="$PWD/results/d08-ros-trace-live"
export ROS_TRACE_DIR="$OUT/trace"
SESSION='axia_d08_real_rcl'
LOG="$OUT/session.log"
mkdir -p "$OUT" "$ROS_TRACE_DIR"
case "$MODE" in
start)
  if ! timeout 20s ros2 run tracetools status > "$OUT/tracetools-status.txt" 2>&1; then
    echo D08_BRIDGE_RCL_TRACE_STATUS_BLOCKED; exit 2
  fi
  if ! grep -Fq 'Tracing enabled' "$OUT/tracetools-status.txt"; then
    echo D08_BRIDGE_RCL_TRACE_DISABLED; exit 2
  fi
  # Start before the existing Gazebo L2 process creates ros_gz_bridge.
  if ! timeout 30s ros2 trace start "$SESSION" > "$LOG" 2>&1; then
    echo D08_BRIDGE_RCL_TRACE_START_BLOCKED
    tail -c 1800 "$LOG"; exit 2
  fi
  python3 - <<'PY' > "$OUT/clock_anchor.json"
import json,time
print(json.dumps({'wall_ns':time.time_ns(), 'monotonic_ns':time.monotonic_ns(),
                  'note':'host clock anchor only; not exact LaserScan message correlation'}))
PY
  echo D08_BRIDGE_RCL_TRACE_REAL_SESSION_STARTED
  ;;
stop)
  if ! timeout 35s ros2 trace stop "$SESSION" >> "$LOG" 2>&1; then
    echo D08_BRIDGE_RCL_TRACE_STOP_BLOCKED; exit 2
  fi
  SESSION_PATH="$ROS_TRACE_DIR/$SESSION"
  if [ ! -d "$SESSION_PATH" ]; then
    echo D08_BRIDGE_RCL_TRACE_OUTPUT_MISSING; exit 2
  fi
  du -sb "$SESSION_PATH" > "$OUT/trace-size-bytes.txt"
  find "$SESSION_PATH" -type f -print0 | sort -z | xargs -0 -r sha256sum > "$OUT/raw-trace-sha256.txt"
  # Stream CTF directly into a tiny JSON summary, not a giant textual log.
  # The resulting rcl_publish / rcl_take inter-event gaps are only
  # candidates: per-Scan message identity and RMW internals are UNDETERMINED.
  if ! timeout 150s babeltrace "$SESSION_PATH" |
      python3 d08/scripts/d08_rcl_trace_summary.py --out "$OUT/summary.json"; then
    echo D08_BRIDGE_RCL_TRACE_PARSE_BLOCKED; exit 2
  fi
  test -s "$OUT/summary.json"
  # Preserve a bounded raw CTF attachment only if modest-sized; otherwise
  # keep source SHA256 inventory and compact summary, do not upload build logs.
  BYTES="$(du -sb "$SESSION_PATH" | cut -f1)"
  if [ "$BYTES" -le 16000000 ]; then
    tar -C "$ROS_TRACE_DIR" -czf "$OUT/ctf-small.tar.gz" "$SESSION"
    if [ "$(stat -c %s "$OUT/ctf-small.tar.gz")" -gt 10000000 ]; then
      rm -f "$OUT/ctf-small.tar.gz"
      echo D08_BRIDGE_RCL_TRACE_RAW_ARCHIVE_SIZE_CAPPED > "$OUT/raw-archive-verdict.txt"
    fi
  else
    echo D08_BRIDGE_RCL_TRACE_RAW_TOO_LARGE_SUMMARY_ONLY > "$OUT/raw-archive-verdict.txt"
  fi
  echo D08_BRIDGE_RCL_TRACE_CAPTURED_CAUSE_UNDETERMINED
  ;;
*) echo 'Usage: bash d08/scripts/d08_ros_trace_live_ci.sh start|stop' >&2; exit 2 ;;
esac
