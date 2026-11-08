#!/usr/bin/env bash
# Show Gazebo proxy and its trajectory WITHOUT requiring robot navigation.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
ENVFILE="$HOME/axia_d3_classroom/d3_session.env"
[[ -f "$ENVFILE" && ! -L "$ENVFILE" ]] || { echo '[BLOCKED] d3_session.sh --init required'; exit 2; }
source "$ENVFILE"
ROUTE="$HOME/axia_d3_classroom/d3_route.env"
[[ -f "$ROUTE" && ! -L "$ROUTE" ]] && source "$ROUTE"
[[ "${GZ_PARTITION:-}" == axia_d3_* ]] || exit 2
set +u
source /opt/ros/jazzy/setup.bash
source "$ROOT/install/setup.bash"
set -u
for k in D3_WORLD D3_START_X D3_START_Y D3_END_X D3_END_Y; do
 [[ -n "${!k:-}" ]] || { echo "[BLOCKED] Set $k"; exit 2; }
done
[[ -r /dev/tty ]] || exit 2
read -r -p 'Preview human-shaped proxy in simulator ONLY? Type YES-D3-PREVIEW: ' ACK < /dev/tty
[[ "$ACK" == YES-D3-PREVIEW ]] || exit 2
ros2 run axia_d3_demo d3_scene --mode preview --world "$D3_WORLD" \
  --start-x "$D3_START_X" --start-y "$D3_START_Y" \
  --end-x "$D3_END_X" --end-y "$D3_END_Y" --ack-sim-only
printf '%s\n' '[INFO] Preview is NOT P1 safety verification.' '[INFO] Model remains. Remove it before live run:' \
  "ros2 run ros_gz_sim remove --ros-args -p world:=$D3_WORLD -p entity_name:=d3_pedestrian_proxy"