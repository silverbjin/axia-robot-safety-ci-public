#!/usr/bin/env bash
# Single AXIA G07 DISPLAY-ONLY process implementation for CI/Xvfb and
# Owner/WSLg. Exactly same Gazebo GUI -g, RViz2 and MarkerArray observer
# taskset/nice topology. P4 official headless Gazebo server owns all robot IO.
# No Goal/STOP/Cancel/cmd_vel publisher, no Guard/CM/TTL modifications.
set -Eeuo pipefail
umask 077
[[ $# == 4 ]] || { echo 'G07_SHARED_GUI_ARGUMENTS_INVALID';exit 3; }
MODE="$1";EVID="$2";VISUAL="$3";TOOLS="$4"
case "$MODE" in
  ci)
    [[ "${GITHUB_ACTIONS:-}" == true &&
       "${AXIA_G07_CI_SIM_GOAL_ALLOWED:-0}" == 1 ]] || {
      echo 'G07_SHARED_GUI_CI_AUTH_BLOCKED';exit 3;
    }
    ;;
  owner)
    [[ "${AXIA_G07_UNIFIED_GUI_SIDECAR:-0}" == 1 &&
       -n "${DISPLAY:-}" ]] || {
      echo 'G07_SHARED_GUI_OWNER_PARITY_FLAG_OR_DISPLAY_MISSING_NO_GOAL';exit 3;
    }
    ;;
  *) echo 'G07_SHARED_GUI_MODE_UNSUPPORTED_NO_ROS_NO_GOAL';exit 3 ;;
esac
[[ -d "$EVID" && -f "$VISUAL/d06/live/d06_readonly_monitor.py" &&
   -f "$VISUAL/d06/rviz/d06_safety_bubble.rviz" &&
   -f "$TOOLS/d06/live/d06_gui_cpu_plan.py" ]] || {
  echo 'G07_SHARED_GUI_SOURCES_OR_EVIDENCE_MISSING';exit 3;
}
for exe in python3 taskset setsid rviz2 gz;do
  command -v "$exe" >/dev/null || {
    echo "G07_SHARED_GUI_COMMAND_MISSING=$exe";exit 3;
  }
done
GUI_PLAN="$TOOLS/d06/live/d06_gui_cpu_plan.py"
GUI_CPU="$(python3 "$GUI_PLAN")" || {
  echo 'G07_SHARED_GUI_RENDERER_CPU_UNVERIFIED';exit 3;
}
MONITOR_CPU="$(python3 "$GUI_PLAN" --role monitor)" || {
  echo 'G07_SHARED_GUI_MONITOR_CPU_UNVERIFIED';exit 3;
}
[[ "$GUI_CPU" =~ ^[0-9]+$ && "$MONITOR_CPU" =~ ^[0-9]+$ &&
   "$GUI_CPU" != "$MONITOR_CPU" ]] || {
  echo 'G07_SHARED_GUI_CPU_ROLE_OVERLAP_NO_GOAL';exit 3;
}
# Cycle36: one integrated official Gazebo GUI belongs to the P4 launch.
# Only RViz/Marker are external. CI Xvfb can use llvmpipe, Owner WSLg
# must retain the existing hardware-capable Gazebo renderer.
INTEGRATED_GUI="${AXIA_G07_CYCLE36_INTEGRATED_GUI:-0}"
[[ "$INTEGRATED_GUI" == 0 || "$INTEGRATED_GUI" == 1 ]] || {
  echo G07_CYCLE36_UNKNOWN_DISPLAY_MODE_NO_GOAL >&2;exit 3;
}
if [[ "$MODE" == ci ]];then
  export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
elif [[ "$INTEGRATED_GUI" == 1 ]];then
  unset LIBGL_ALWAYS_SOFTWARE || true
  unset GALLIUM_DRIVER || true
else
  export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
fi
unset QT_QPA_PLATFORM || true
echo "G07_UNIFIED_GUI_CPU_PARTITION renderer=$GUI_CPU observer=$MONITOR_CPU same_process_launcher=true safety_processes_unmodified=true cm_core_isolation_proven=false"
monitor_pid='';rviz_pid='';gz_pid=''
cleanup(){
  trap - EXIT INT TERM
  set +e
  for pid in "$monitor_pid" "$rviz_pid" "$gz_pid";do
    [[ "$pid" =~ ^[0-9]+$ ]] || continue
    kill -TERM -- "-$pid" 2>/dev/null || true
    for _ in {1..10};do
      kill -0 "$pid" 2>/dev/null || break
      sleep .1
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
# Exactly these THREE commands and affinity/nice settings for BOTH environments.
setsid taskset -c "$MONITOR_CPU" nice -n 15 python3 -u "$VISUAL/d06/live/d06_readonly_monitor.py" --out "$EVID" > "$EVID/monitor.log" 2>&1 &
monitor_pid=$!
setsid taskset -c "$GUI_CPU" nice -n 19 rviz2 -d "$VISUAL/d06/rviz/d06_safety_bubble.rviz" --ros-args -p use_sim_time:=true > "$EVID/rviz.log" 2>&1 &
rviz_pid=$!
if [[ "$INTEGRATED_GUI" == 1 ]];then
  # Do not launch a second Gazebo GUI; the official P4 launch has one.
  echo G07_CYCLE36_INTEGRATED_GUI_NO_EXTERNAL_GZ
  printf '%s\n' 'Cycle36 official Gazebo integrated GUI: no secondary gz -g' > "$EVID/gz_gui.log"
else
  setsid taskset -c "$GUI_CPU" nice -n 19 gz sim -g > "$EVID/gz_gui.log" 2>&1 &
  gz_pid=$!
fi
windows=0
for _ in {1..80};do
  if ! kill -0 "$monitor_pid" 2>/dev/null ||
     ! kill -0 "$rviz_pid" 2>/dev/null ||
     { [[ "$INTEGRATED_GUI" != 1 ]] && ! kill -0 "$gz_pid" 2>/dev/null; };then
    echo 'G07_SHARED_GUI_CHILD_EARLY_EXIT';exit 3
  fi
  if command -v xwininfo >/dev/null;then
    xwininfo -root -tree > "$EVID/windows.txt" 2>&1 || true
    if grep -Eiq 'rviz' "$EVID/windows.txt" &&
       grep -Eiq 'gazebo|gz sim' "$EVID/windows.txt";then
      windows=1;break
    fi
  fi
  # WSLg may expose Wayland windows without xwininfo. Never mark visual
  # attested from process existence in this mode; Owner must confirm WSLg.
  [[ "$MODE" == ci ]] || { sleep 0.5; break; }
  sleep .5
done
# Verify real Gazebo transport world and official Waffle entity, not a
# GUI PID or an empty window. These checks are read-only: no Goal/STOP.
world_entity_verified=0
if [[ "$INTEGRATED_GUI" == 1 ]];then
  for _ in {1..24};do
    services="$(timeout 4s gz service -l 2>/dev/null || true)"
    models="$(timeout 4s gz model --list 2>/dev/null || true)"
    if grep -Eq '/world/[^/]+/control' <<< "$services" &&
       grep -Eiq '(waffle|turtlebot3)' <<< "$models";then
      world_entity_verified=1
      printf '%s\n' "$services" > "$EVID/gz_services.txt"
      printf '%s\n' "$models" > "$EVID/gz_models.txt"
      echo G07_CYCLE36_WORLD_ENTITY_REAL_GAZEBO_PASS
      break
    fi
    sleep 0.5
  done
  if [[ "$world_entity_verified" != 1 ]];then
    echo G07_CYCLE36_WORLD_ENTITY_MISSING_NO_GOAL >&2;exit 3
  fi
fi
if [[ "$MODE" == ci && "$windows" != 1 ]];then
  echo 'G07_UNIFIED_GUI_DISPLAY_WINDOW_UNVERIFIED_RVIZ_OR_GAZEBO'
  exit 3
fi
export GUI_CPU MONITOR_CPU windows MODE INTEGRATED_GUI world_entity_verified
python3 - "$EVID/display_attestation.json" <<'PY'
import json,os,sys,time
mode=os.environ["MODE"]
windows=os.environ["windows"]=="1"
with open(sys.argv[1],"x",encoding="utf-8") as f:
    json.dump({"schema":"axia.g07.shared_gui_display_client_v2",
               "display_started_monotonic":time.monotonic(),
               "real_rviz_window":windows if mode=="ci" else None,
               "real_gazebo_gui_window":windows if mode=="ci" else None,
               "display":"Xvfb" if mode=="ci" else "WSLg_candidate",
               "wslg_verified":False,"xvfb_window_verified":mode=="ci" and windows,
               "renderer_cpu":int(os.environ["GUI_CPU"]),
               "monitor_cpu":int(os.environ["MONITOR_CPU"]),
               "shared_gui_launcher":True,
               "headless_server_required":os.environ["INTEGRATED_GUI"]!="1",
               "world_entity_verified":os.environ["world_entity_verified"]=="1",
               "external_gazebo_gui_spawned":os.environ["INTEGRATED_GUI"]!="1",
               "new_cmd_vel_publisher_authorized":False,
               "owner_l3_accepted":False,"certified_estop":False},f)
PY
if [[ "$MODE" == ci ]];then
  echo "G07_UNIFIED_GUI_DISPLAY_WINDOW_XVFB_PASS_SAME_SESSION_NO_GOAL_AUTHORITY"
else
  echo "D06_RVIZ_STARTED domain=${ROS_DOMAIN_ID:-unknown} rviz_pid=$rviz_pid monitor_pid=$monitor_pid gz_pid=$gz_pid"
  echo "G07_OWNER_SHARED_GAZEBO_GUI_PROCESS_STARTED_RENDER_NOT_YET_WSLG_VERIFIED"
  echo 'D06_GUI_NOT_ACCEPTANCE: actual WSLg visual confirmation still required'
fi
while kill -0 "$rviz_pid" 2>/dev/null &&
      kill -0 "$monitor_pid" 2>/dev/null &&
      { [[ "$INTEGRATED_GUI" == 1 ]] || kill -0 "$gz_pid" 2>/dev/null; };do
  sleep 1
done
if [[ "$MODE" == owner ]];then
  echo 'D06_RVIZ_SIDECAR_EXITED_BEFORE_OWNER_COMPLETION'
else
  echo 'G07_UNIFIED_GUI_CHILD_EXITED_EARLY_UNVERIFIED'
fi
exit 3
