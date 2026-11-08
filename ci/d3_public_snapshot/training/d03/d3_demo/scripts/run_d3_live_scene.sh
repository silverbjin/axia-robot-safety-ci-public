#!/usr/bin/env bash
# Run AFTER P1 Gazebo is launched. Start monitor+adapter, then guided moving proxy and scan fault.
# No Nav2 Goal, Start, Cancel, /cmd_vel, Reset or Rearm are sent here.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
ENVFILE="$HOME/axia_d3_classroom/d3_session.env"
[[ -f "$ENVFILE" && ! -L "$ENVFILE" ]] || { echo '[BLOCKED] Run d3_session.sh --init first' >&2; exit 2; }
# shellcheck disable=SC1090
source "$ENVFILE"
ROUTE="$HOME/axia_d3_classroom/d3_route.env"
[[ -f "$ROUTE" && ! -L "$ROUTE" ]] && source "$ROUTE"
[[ "${GZ_PARTITION:-}" == axia_d3_* ]] || { echo '[BLOCKED] Wrong Gazebo partition' >&2; exit 2; }
[[ "${AXIA_P0_SIM_ONLY:-}" == 1 ]] || { echo '[BLOCKED] Simulation-only marker absent' >&2; exit 2; }
if [[ "$(git -C "$ROOT" branch --show-current)" != feat/d3-intrusion-scan-stop-demo-20261108 ]]; then
  echo '[BLOCKED] Checkout correct D3 instructor feature branch' >&2; exit 2
fi
set +u
source /opt/ros/jazzy/setup.bash
source "$ROOT/install/setup.bash"
set -u
for cmd in ros2 gz python3; do command -v "$cmd" >/dev/null || { echo "[BLOCKED] Missing $cmd" >&2; exit 2; }; done
for pkg in axia_d3_demo axia_safety_supervisor axia_fault_injector; do
  ros2 pkg prefix "$pkg" >/dev/null || { echo "[BLOCKED] Missing $pkg" >&2; exit 2; }
done
for name in D3_WORLD D3_START_X D3_START_Y D3_END_X D3_END_Y; do
  [[ -n "${!name:-}" ]] || { echo "[BLOCKED] Set $name from verified Gazebo route" >&2; exit 2; }
done
[[ -n "${ROS_DOMAIN_ID:-}" && -n "${D3_EVIDENCE:-}" ]] || { echo '[BLOCKED] D3 session env incomplete' >&2; exit 2; }

echo "[INFO] P1 session: ROS_DOMAIN_ID=$ROS_DOMAIN_ID GZ_PARTITION=$GZ_PARTITION"
echo "[INFO] Gazebo world: $D3_WORLD, proxy path: ($D3_START_X,$D3_START_Y)->($D3_END_X,$D3_END_Y)"
echo '[CHECK] ROS P1 state, odom and Gazebo services must exist before starting the demo.'
timeout 12 ros2 topic type /axia/safety/state | grep -Fxq std_msgs/msg/String || { echo '[BLOCKED] P1 state absent in D3 domain' >&2; exit 2; }
timeout 12 ros2 topic type /odom | grep -Fxq nav_msgs/msg/Odometry || { echo '[BLOCKED] /odom absent' >&2; exit 2; }
gz service -l | grep -Fqx "/world/$D3_WORLD/set_pose" || { echo '[BLOCKED] Gazebo world set_pose service absent' >&2; exit 2; }

# Separate explicit fault authorization. This is a virtual robot and a controlled simulation only.
[[ -r /dev/tty ]] || { echo '[BLOCKED] Controlling terminal is required' >&2; exit 2; }
read -r -p 'SIMULATOR ONLY, P1 goal already approved? Type YES-D3-SIM: ' ANSWER < /dev/tty
[[ "$ANSWER" == YES-D3-SIM ]] || { echo '[BLOCKED] Simulation not approved'; exit 2; }
read -r -p 'Authorize scan_drop in THIS isolated simulation? Type YES-D3-FAULT: ' ANSWER < /dev/tty
[[ "$ANSWER" == YES-D3-FAULT ]] || { echo '[BLOCKED] Fault not authorized'; exit 2; }

OUTDIR="$HOME/axia_d3_classroom/evidence"
mkdir -p "$OUTDIR"
chmod 700 "$OUTDIR"
if [[ -e "$D3_EVIDENCE" ]]; then
  echo '[BLOCKED] Evidence file exists: start a fresh D3 session, never append across runs' >&2; exit 2
fi
TMP="$(mktemp -d "$HOME/axia_d3_classroom/private_bridge.XXXXXXXX")"
chmod 700 "$TMP"
cp "$ROOT/training/d03/student_package/block_A/day03/ros_diagnostics_bridge.py" "$TMP/"
cp "$ROOT/training/d03/instructor/solutions/p1_adapter_todo.py" "$TMP/"
BRIDGE_PID=''
OBS_PID=''
cleanup() {
  local rc=$?
  trap - EXIT
  for pid in "$BRIDGE_PID" "$OBS_PID"; do
    if [[ -n "$pid" ]]; then
      kill -INT "$pid" 2>/dev/null || true
      sleep .2
      kill -TERM "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
  done
  # Do not reset P1 or clear fault! Human operator owns recovery.
  echo "[EVIDENCE] $D3_EVIDENCE"
  echo "[LOG] $OUTDIR/d3_bridge.log $OUTDIR/d3_observer.log"
  echo '[EXIT] P1 remains fail-closed. No automatic recovery.'
  exit "$rc"
}
trap cleanup EXIT INT TERM
PYTHONPATH="$TMP" python3 "$TMP/ros_diagnostics_bridge.py" > "$OUTDIR/d3_bridge.log" 2>&1 &
BRIDGE_PID=$!
ros2 run axia_d3_demo d3_observer --evidence "$D3_EVIDENCE" > "$OUTDIR/d3_observer.log" 2>&1 &
OBS_PID=$!
sleep 2
kill -0 "$BRIDGE_PID" || { echo '[BLOCKED] Diagnostics bridge terminated' >&2; cat "$OUTDIR/d3_bridge.log" >&2; exit 2; }
kill -0 "$OBS_PID" || { echo '[BLOCKED] D3 observer terminated' >&2; cat "$OUTDIR/d3_observer.log" >&2; exit 2; }
# The actual P1 Goal must be started through its previously approved operator workflow.
# This command waits for P1 NORMAL + odom moving; if not, it exits without spawning/fault.
ros2 run axia_d3_demo d3_scene \
  --mode live --world "$D3_WORLD" \
  --start-x "$D3_START_X" --start-y "$D3_START_Y" \
  --end-x "$D3_END_X" --end-y "$D3_END_Y" \
  --evidence "$D3_EVIDENCE" --ack-sim-only --ack-fault \
  --ready-timeout-s 60