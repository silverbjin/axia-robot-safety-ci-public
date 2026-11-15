#!/usr/bin/env bash
# AXIA Unified G07: GitHub-hosted CI DISPLAY ONLY. The P4 runner owns the
# sole actual Goal/STOP/Cancel/Shutdown. No robot command publisher here.
set -Eeuo pipefail
umask 077
if [[ "${GITHUB_ACTIONS:-}" != true || "${AXIA_P0_SIM_ONLY:-0}" != 1 ||
      "${AXIA_G07_CI_SIM_GOAL_ALLOWED:-0}" != 1 ||
      "${AXIA_P2_G07_PHYSICAL_PREFLIGHT:-0}" != 1 ]];then
  echo 'G07_UNIFIED_GUI_CI_ONLY_NO_ROS_NO_GOAL' >&2
  exit 3
fi
[[ $# == 2 ]] || { echo 'G07_UNIFIED_GUI_BAD_ARGUMENTS';exit 3; }
RESULTS="$1"
VISUAL="$2"
[[ -d "$RESULTS" && -f "$VISUAL/d06/live/d06_readonly_monitor.py" &&
   -f "$VISUAL/d06/rviz/d06_safety_bubble.rviz" ]] || {
  echo 'G07_UNIFIED_GUI_PUBLIC_SOURCE_MISSING';exit 3;
}
set +u
source /opt/ros/jazzy/setup.bash
set -u
for cmd in rviz2 gz xwininfo;do
  command -v "$cmd" >/dev/null || {
    echo "G07_UNIFIED_GUI_MISSING_EXACT_CMD=$cmd";exit 3;
  }
done
# P4 stage is authoritative. Never infer startup from a file that is
# stale or reports a Goal. This process does not gate/control the Goal.
ready=0
for i in {1..960};do
  if [[ -s "$RESULTS/startup_verdict.json" ]] &&
      python3 - "$RESULTS/startup_verdict.json" <<'PY'
import json,sys
try:
    d=json.load(open(sys.argv[1],encoding="utf-8"))
    assert d.get("status")=="SMOKE_READY" and d.get("goal_sent") is False
    assert d.get("gate_accepted") is False
except (OSError,ValueError,AssertionError,TypeError):
    raise SystemExit(1)
PY
  then ready=1;break;fi
  sleep 0.5
done
[[ "$ready" == 1 ]] || {
  echo 'G07_UNIFIED_GUI_NOT_READY_REAL_NAV2_STARTUP_UNVERIFIED'
  exit 3
}
export DISPLAY="${DISPLAY:-:99}"
unset QT_QPA_PLATFORM || true
# The same GUI process launcher is used in Owner WSLg and CI Xvfb.
# DISPLAY_WINDOW and real marker attestations belong to the shared helper.
UNIFIED="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
mkdir -p "$RESULTS/visual-readonly"
EVID="$RESULTS/visual-readonly"
exec bash "$UNIFIED/d06/scripts/g07_shared_gui_clients.sh" ci "$EVID" "$VISUAL" "$UNIFIED"
