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
for cmd in rviz2 gz xwininfo;do
  command -v "$cmd" >/dev/null || {
    echo "G07_UNIFIED_GUI_MISSING_EXACT_CMD=$cmd";exit 3;
  }
done
mkdir -p "$RESULTS/visual-readonly"
EVID="$RESULTS/visual-readonly"
rviz_pid='' monitor_pid='' gz_pid=''
cleanup() {
  trap - EXIT INT TERM
  set +e
  for pid in "$monitor_pid" "$rviz_pid" "$gz_pid";do
    [[ "$pid" =~ ^[0-9]+$ ]] || continue
    kill -TERM -- "-$pid" 2>/dev/null || true
    for i in {1..10};do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.1
    done
    if kill -0 "$pid" 2>/dev/null;then
      kill -KILL -- "-$pid" 2>/dev/null || true
    fi
    wait "$pid" 2>/dev/null || true
  done
  echo 'G07_UNIFIED_GUI_SIDECAR_TERMINATED_DISPLAY_ONLY'
}
trap cleanup EXIT
trap 'exit 0' TERM
trap 'exit 130' INT
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
set +u
source /opt/ros/jazzy/setup.bash
set -u
export DISPLAY="${DISPLAY:-:99}" LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
unset QT_QPA_PLATFORM || true
# Read-only teaching monitor publishes /axia/d06/rviz/bubble MarkerArray only.
# It subscribes to /scan /odom /cmd_vel*; no alternative Goal executor.
setsid nice -n 15 python3 -u "$VISUAL/d06/live/d06_readonly_monitor.py"   --out "$EVID" > "$EVID/monitor.log" 2>&1 &
monitor_pid=$!
setsid nice -n 19 rviz2 -d "$VISUAL/d06/rviz/d06_safety_bubble.rviz"   --ros-args -p use_sim_time:=true > "$EVID/rviz.log" 2>&1 &
rviz_pid=$!
# This connects a DISPLAY-only Gazebo GUI client to the existing Harmonic
# server. The original P4 server/runner is never relaunched.
setsid nice -n 19 gz sim -g > "$EVID/gz_gui.log" 2>&1 &
gz_pid=$!
windows=0
for i in {1..80};do
  if ! kill -0 "$monitor_pid" 2>/dev/null ||
     ! kill -0 "$rviz_pid" 2>/dev/null ||
     ! kill -0 "$gz_pid" 2>/dev/null;then
    echo 'G07_UNIFIED_GUI_CHILD_EARLY_EXIT';exit 3
  fi
  xwininfo -root -tree > "$EVID/windows.txt" 2>&1 || true
  if grep -Eiq 'rviz' "$EVID/windows.txt" &&
      grep -Eiq 'gazebo|gz sim' "$EVID/windows.txt";then
    windows=1;break
  fi
  sleep 0.5
done
[[ "$windows" == 1 ]] || {
  echo 'G07_UNIFIED_GUI_DISPLAY_WINDOW_UNVERIFIED_RVIZ_OR_GAZEBO'
  exit 3
}
python3 - "$EVID/display_attestation.json" <<'PY'
import json,sys,time
with open(sys.argv[1],"x",encoding="utf-8") as f:
    json.dump({"schema":"axia.g07.gui_xvfb_attestation_v1",
               "display_started_monotonic":time.monotonic(),
               "real_rviz_window":True,"real_gazebo_gui_window":True,
               "display":"Xvfb","wslg_verified":False,
               "new_cmd_vel_publisher_authorized":False,
               "owner_l3_accepted":False,"certified_estop":False},f)
print("G07_UNIFIED_GUI_DISPLAY_WINDOW_XVFB_PASS_SAME_SESSION_NO_GOAL_AUTHORITY",flush=True)
PY
while kill -0 "$rviz_pid" 2>/dev/null &&
      kill -0 "$monitor_pid" 2>/dev/null &&
      kill -0 "$gz_pid" 2>/dev/null;do
  sleep 1
done
echo 'G07_UNIFIED_GUI_CHILD_EXITED_EARLY_UNVERIFIED'
exit 3
