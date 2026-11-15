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
GUI_CPU_SELECTOR="$PUBLIC_ROOT/d06/live/d06_gui_cpu_plan.py"
session=''
for attempt in $(seq 1 600);do
  mapfile -d '' -t matches < <(find "$BASE" -maxdepth 3 -type f \
    -path "$BASE/p2-l3-owner-*/G07/session.env" -newer "$MARKER" \
    -print0 2>/dev/null)
  if (( ${#matches[@]} > 1 ));then
    echo 'D06_RVIZ_BLOCKED_MULTIPLE_NEW_OWNER_SESSIONS';exit 2
  fi
  if (( ${#matches[@]} == 1 ));then session="${matches[0]}";break;fi
  sleep 1
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
# Display-only work starts AFTER actual Nav2 Lifecycle startup acknowledgement.
# This avoids overloading localization/navigation initialization on WSLg.
# A JSON file alone is not proof of a Goal; status must be SMOKE_READY and
# the same session must still have goal_sent=false at this boundary.
NAV2_READY="$owner_dir/G07/startup_verdict.json"
nav2_ready=false
for attempt in $(seq 1 960);do
  if [[ -s "$NAV2_READY" ]] && /usr/bin/python3 - "$NAV2_READY" <<'PY'
import json,sys
try:
    d=json.load(open(sys.argv[1],encoding="utf-8"))
    assert d.get("status")=="SMOKE_READY"
    assert d.get("goal_sent") is False
except (OSError,ValueError,AssertionError):
    raise SystemExit(3)
PY
  then
    nav2_ready=true
    break
  fi
  sleep .25
done
if [[ "$nav2_ready" != true ]];then
  echo 'D06_GUI_NAV2_STARTUP_MISSING_OR_UNVERIFIED';exit 3;
fi
echo 'D06_GUI_NAV2_STARTUP_READY_NO_GOAL'
# The exact same three display clients + CPU/nice topology as public CI.
# The private shared P4 launcher is source-pinned and headless only when
# AXIA_G07_UNIFIED_GUI_SIDECAR=1. The Goal remains strictly manual.
exec bash "$PUBLIC_ROOT/d06/scripts/g07_shared_gui_clients.sh" owner "$OUT" "$PUBLIC_ROOT" "$PUBLIC_ROOT"
