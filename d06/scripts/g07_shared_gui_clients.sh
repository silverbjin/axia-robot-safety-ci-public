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
# The 2026-11-16 Owner WSLg evidence recorded:
# MESA-EGL: Not allowed to force software rendering when API explicitly
# selects a hardware device. D04 previously fixed the same WSLg-vs-CI
# environment mismatch: keep software EGL only for CI Xvfb, never WSLg.
if [[ "$MODE" == ci ]];then
  export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
  echo G07_GUI_CI_XVFB_LLVMPIPE_SELECTED_NO_OWNER_CLAIM
else
  unset LIBGL_ALWAYS_SOFTWARE GALLIUM_DRIVER MESA_LOADER_DRIVER_OVERRIDE
  [[ -f "$TOOLS/d06/live/g07_cycle38_gui_window_evidence.py" ]] || {
    echo AXIA_G07_C38_OWNER_REAL_WINDOW_EVIDENCE_HELPER_ABSENT_NO_GOAL;exit 3;
  }
  for tool in glxinfo xwd xwininfo;do
    command -v "$tool" >/dev/null || {
      echo "AXIA_G07_C38_OWNER_XCB_XWD_DEPENDENCY_MISSING=$tool";exit 3;
    }
  done
  # D07 Cycle19 *actual* Owner WSLg success selected NVIDIA D3D12,
  # not the Intel Iris Xe auto-picked in this G07 Owner ZIP.
  # Probe GPU before any display client, and apply only to GUI children.
  if ! timeout 12s env -u LIBGL_ALWAYS_SOFTWARE -u MESA_LOADER_DRIVER_OVERRIDE \
      QT_QPA_PLATFORM=xcb QT_X11_NO_MITSHM=1 \
      GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA \
      glxinfo -B > "$EVID/d07_nvidia_d3d12_glxinfo.txt" 2>&1;then
    echo AXIA_G07_C38_D07_GUI_NVIDIA_PREFLIGHT_FAILED_NO_GOAL;exit 3
  fi
  if ! python3 "$TOOLS/d06/live/g07_cycle38_gui_window_evidence.py" \
       --gpu "$EVID/d07_nvidia_d3d12_glxinfo.txt" --adapter NVIDIA;then
    echo AXIA_G07_C38_GUI_WRONG_GPU_NOT_NVIDIA_HOLD_NO_GOAL;exit 3
  fi
  echo AXIA_G07_C38_OWNER_D07_PROVEN_NVIDIA_XCB_GUI_CHILDREN_ONLY
fi
if [[ "$MODE" == ci ]];then unset QT_QPA_PLATFORM || true;fi
# Original read-only monitor remains CPU/safety independent. GUI child
# environment is scoped to its own process, not the ROS/Nav2/Gazebo server.
if [[ "$MODE" == owner ]];then
  GUI_RENDER_ENV=(env -u LIBGL_ALWAYS_SOFTWARE -u MESA_LOADER_DRIVER_OVERRIDE
    QT_QPA_PLATFORM=xcb QT_X11_NO_MITSHM=1
    GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA)
else
  GUI_RENDER_ENV=(env)
fi
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
setsid taskset -c "$GUI_CPU" nice -n 19 "${GUI_RENDER_ENV[@]}" rviz2 -d "$VISUAL/d06/rviz/d06_safety_bubble.rviz" --ros-args -p use_sim_time:=true > "$EVID/rviz.log" 2>&1 &
rviz_pid=$!
setsid taskset -c "$GUI_CPU" nice -n 19 "${GUI_RENDER_ENV[@]}" gz sim -g -v 4 > "$EVID/gz_gui.log" 2>&1 &
gz_pid=$!
windows=0
gazebo_id=''
rviz_id=''
for _ in {1..80};do
  if ! kill -0 "$monitor_pid" 2>/dev/null ||
     ! kill -0 "$rviz_pid" 2>/dev/null ||
     ! kill -0 "$gz_pid" 2>/dev/null;then
    echo 'G07_SHARED_GUI_CHILD_EARLY_EXIT';exit 3
  fi
  if command -v xwininfo >/dev/null;then
    xwininfo -root -tree > "$EVID/windows.txt" 2>&1 || true
    if [[ "$MODE" == owner ]];then
      gazebo_id="$(python3 "$TOOLS/d06/live/g07_cycle38_gui_window_evidence.py" \
        --tree "$EVID/windows.txt" --role gazebo 2>/dev/null)" || gazebo_id=''
      rviz_id="$(python3 "$TOOLS/d06/live/g07_cycle38_gui_window_evidence.py" \
        --tree "$EVID/windows.txt" --role rviz 2>/dev/null)" || rviz_id=''
      if [[ "$gazebo_id" == 0x* && "$rviz_id" == 0x* ]];then
        windows=1;break
      fi
    elif grep -Eiq 'rviz' "$EVID/windows.txt" &&
         grep -Eiq 'gazebo|gz sim' "$EVID/windows.txt";then
      windows=1;break
    fi
  fi
  sleep .5
done
if [[ "$windows" != 1 ]];then
  echo "AXIA_G07_C38_REAL_XCB_GUI_WINDOW_MISSING_NO_GOAL mode=$MODE"
  echo 'G07_UNIFIED_GUI_DISPLAY_WINDOW_UNVERIFIED_RVIZ_OR_GAZEBO'
  exit 3
fi
if [[ "$MODE" == owner ]];then
  # D07 Cycle19 had genuine 1000x845/1450x900 Owner XWD frames.
  # Capturing pixels proves a window buffer exists, NOT meaningful scene
  # contents. Do not promote to formal L3 without human visual review.
  timeout 12s xwd -silent -id "$gazebo_id" -out "$EVID/gazebo_scene_owner.xwd" ||
    { echo AXIA_G07_C38_GAZEBO_XWD_FAILED_NO_GOAL;exit 3; }
  timeout 12s xwd -silent -id "$rviz_id" -out "$EVID/rviz_scene_owner.xwd" ||
    { echo AXIA_G07_C38_RVIZ_XWD_FAILED_NO_GOAL;exit 3; }
  [[ "$(stat -c %s "$EVID/gazebo_scene_owner.xwd")" -gt 65536
     && "$(stat -c %s "$EVID/rviz_scene_owner.xwd")" -gt 65536 ]] ||
    { echo AXIA_G07_C38_GUI_XWD_TOO_SMALL_TO_REVIEW_NO_GOAL;exit 3; }
  sha256sum "$EVID/gazebo_scene_owner.xwd" "$EVID/rviz_scene_owner.xwd" > "$EVID/owner_gui_xwd.sha256"
  echo G07_CYCLE38_OWNER_XWD_PIXELS_CAPTURED_CONTENT_NEEDS_REVIEW
  echo G07_CYCLE38_OWNER_XWD_REAL_XCB_WINDOWS_ATTESTED_NOT_L3
fi
export GUI_CPU MONITOR_CPU windows MODE
python3 - "$EVID/display_attestation.json" <<'PY'
import json,os,sys,time
mode=os.environ["MODE"]
windows=os.environ["windows"]=="1"
with open(sys.argv[1],"x",encoding="utf-8") as f:
    json.dump({"schema":"axia.g07.shared_gui_display_client_v2",
               "display_started_monotonic":time.monotonic(),
               "real_rviz_window":windows,
               "real_gazebo_gui_window":windows,
               "display":"Xvfb" if mode=="ci" else "WSLg_candidate",
               "wslg_verified":False,"xvfb_window_verified":mode=="ci" and windows,
               "renderer_cpu":int(os.environ["GUI_CPU"]),
               "monitor_cpu":int(os.environ["MONITOR_CPU"]),
               "shared_gui_launcher":True,"headless_server_required":True,
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
      kill -0 "$gz_pid" 2>/dev/null;do
  sleep 1
done
if [[ "$MODE" == owner ]];then
  echo 'D06_RVIZ_SIDECAR_EXITED_BEFORE_OWNER_COMPLETION'
else
  echo 'G07_UNIFIED_GUI_CHILD_EXITED_EARLY_UNVERIFIED'
fi
exit 3
