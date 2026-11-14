#!/usr/bin/env bash
# G07 Owner keeps ALL safety/Goal ownership. Sidecar is display-only.
set -Eeuo pipefail
umask 077
[[ $# == 3 ]] || { echo "D06_SIDECAR_USAGE marker evidence owner_sha";exit 2; }
MARKER="$1"; OUT="$2"; OWNER_SHA="$3"
[[ -f "$MARKER" && -d "$OUT" && "$OWNER_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
BASE="$HOME/axia_p2_private_evidence"
PUBLIC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
RVIZ_CONFIG="$PUBLIC_ROOT/d06/rviz/d06_safety_bubble.rviz"
MONITOR="$PUBLIC_ROOT/d06/live/d06_readonly_monitor.py"
rviz_pid=''; monitor_pid=''
cleanup() {
  trap - EXIT INT TERM
  set +e
  for pid in "$monitor_pid" "$rviz_pid";do
    [[ "$pid" =~ ^[0-9]+$ ]] || continue
    kill -INT -- "-$pid" 2>/dev/null || true
    sleep 0.5
    kill -TERM -- "-$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  done
  echo 'D06_RVIZ_SIDECAR_CLEANED D06_GUI_NOT_ACCEPTANCE'
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
session=''
for attempt in $(seq 1 240);do
  mapfile -d '' -t matches < <(find "$BASE" -maxdepth 3 -type f \
    -path "$BASE/p2-l3-owner-*/G07/session.env" -newer "$MARKER" \
    -print0 2>/dev/null)
  if (( ${#matches[@]} > 1 ));then
    echo 'D06_RVIZ_BLOCKED_MULTIPLE_NEW_OWNER_SESSIONS';exit 2
  fi
  if (( ${#matches[@]} == 1 ));then session="${matches[0]}";break;fi
  sleep 0.5
done
[[ -n "$session" ]] || { echo 'D06_RVIZ_BLOCKED_OWNER_SESSION_NOT_FOUND';exit 2; }
owner_dir="$(dirname "$(dirname "$session")")"
[[ -f "$owner_dir/source.sha" && "$(cat "$owner_dir/source.sha")" == "$OWNER_SHA" ]] || {
  echo 'D06_RVIZ_BLOCKED_OWNER_SOURCE_MISMATCH';exit 2;
}
# Treat session.env as data, not shell script.
ros_domain="$(sed -n 's/^ROS_DOMAIN_ID=//p' "$session")"
partition="$(sed -n 's/^GZ_PARTITION=//p' "$session")"
[[ "$ros_domain" =~ ^[0-9]{1,3}$ && "$partition" =~ ^axia_p2_g07_[a-zA-Z0-9_]+$ ]] || {
  echo 'D06_RVIZ_BLOCKED_OWNER_DOMAIN_PARTITION';exit 2;
}
export ROS_DOMAIN_ID="$ros_domain" GZ_PARTITION="$partition"
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
unset QT_QPA_PLATFORM || true
set +u
source /opt/ros/jazzy/setup.bash
set -u
printf 'D06_OWNER_SESSION=%s\nROS_DOMAIN_ID=%s\nGZ_PARTITION=%s\n' \
  "$owner_dir" "$ros_domain" "$partition" > "$OUT/session_attachment.txt"
setsid rviz2 -d "$RVIZ_CONFIG" --ros-args -p use_sim_time:=true \
  > "$OUT/rviz.log" 2>&1 & rviz_pid=$!
setsid /usr/bin/python3 -u "$MONITOR" --out "$OUT" \
  > "$OUT/readonly_monitor.log" 2>&1 & monitor_pid=$!
sleep 3
if ! kill -0 "$rviz_pid" 2>/dev/null || ! kill -0 "$monitor_pid" 2>/dev/null;then
  echo 'D06_RVIZ_BLOCKED_EARLY_CHILD_EXIT'
  tail -n 12 "$OUT/rviz.log" || true
  tail -n 12 "$OUT/readonly_monitor.log" || true
  exit 2
fi
echo "D06_RVIZ_STARTED domain=$ros_domain rviz_pid=$rviz_pid monitor_pid=$monitor_pid"
echo 'D06_GUI_NOT_ACCEPTANCE: visual WSL2 check still required'
while kill -0 "$rviz_pid" 2>/dev/null && kill -0 "$monitor_pid" 2>/dev/null;do
  sleep 1
done
echo 'D06_RVIZ_SIDECAR_EXITED_BEFORE_OWNER_COMPLETION'
exit 2
