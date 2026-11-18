#!/usr/bin/env bash
# Task04: WSL2 public source GUI pre-gate only; NO MOVING GOAL AUTHORITY.
set -Eeuo pipefail
umask 077
STUDENT_REPO='silverbjin/axia-robot-safety-student'
STUDENT_SHA='01752add2e30c90c4d3286ef3a450f97746ecb55'
TASK03_PUBLIC_L2_RUN=44223320904
MODE=--run
if (( $# )); then MODE="$1";fi
case "$MODE" in --self-check|--doctor|--run) ;; *) echo AXIA_G07_TASK04_FIRST_FAILURE=BAD_ARGUMENTS;exit 3;;esac
[[ $# -le 1 && "$STUDENT_SHA" =~ ^[a-f0-9]{40}$ ]] || exit 3
if [[ "$MODE" == --self-check ]];then
  echo "AXIA_G07_TASK04_PUBLIC_OWNER_BOOTSTRAP_L0_PASS student_sha=$STUDENT_SHA public_l2_run=$TASK03_PUBLIC_L2_RUN NO_ROS_NO_GAZEBO_NO_GOAL"
  echo AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
hold() {
  echo "AXIA_G07_TASK04_FIRST_FAILURE=$1" >&2
  echo AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN >&2
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false' >&2
  exit 3
}
[[ "$(printenv GITHUB_ACTIONS || true)" != true ]] || hold NOT_OWNER
[[ -r /proc/sys/kernel/osrelease ]] || hold NOT_WSL2
grep -Eiq 'microsoft|wsl' /proc/sys/kernel/osrelease || hold NOT_WSL2
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || hold UBUNTU_2404_REQUIRED
[[ -r /opt/ros/jazzy/setup.bash ]] || hold JAZZY_MISSING
[[ -n "$(printenv DISPLAY || true)" && -n "$(printenv XDG_RUNTIME_DIR || true)" ]] || hold WSLG_UNAVAILABLE
for cmd in git bash python3 ros2 gz rviz2 colcon timeout tar sha256sum glxinfo xwininfo setsid;do
  command -v "$cmd" >/dev/null 2>&1 || hold "MISSING_COMMAND_$cmd"
done
export AXIA_G07_CI_SIM_GOAL_ALLOWED=0 AXIA_P0_SIM_ONLY=1
unset AXIA_G07_TASK03_FORMAL_CI AXIA_G07_TASK03_ECM_WITNESS AXIA_G07_TASK04_OWNER_WSL2_GOAL || true
export AXIA_D07_H01_TEACHING_LOOP=0
export ROS_DOMAIN_ID=86
requested_domain="$(printenv AXIA_G07_TASK04_DOMAIN_ID || true)"
if [[ -n "$requested_domain" ]];then export ROS_DOMAIN_ID="$requested_domain";fi
[[ "$ROS_DOMAIN_ID" =~ ^[0-9]+$ ]] && ((ROS_DOMAIN_ID<=101)) || hold ROS_DOMAIN_ID_INVALID
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
# Never use the Bash special parameter $_ (last argument to prior export).
# The original WSL2 first failure literally inherited
# 'ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST' inside the Gazebo partition.
export GZ_PARTITION="axia_p2_task04_${ROS_DOMAIN_ID}_${BASHPID}_$(date -u +%s)"
if [[ ! "$GZ_PARTITION" =~ ^[A-Za-z0-9_]+$ || "${#GZ_PARTITION}" -gt 115 ]];then
  echo 'AXIA_G07_TASK04_FIRST_FAILURE=GZ_PARTITION_INVALID' >&2
  hold GZ_PARTITION_INVALID
fi
printf 'AXIA_G07_TASK04_PARTITION_VALID=%s\n' "$GZ_PARTITION"
export QT_QPA_PLATFORM=xcb
unset LIBGL_ALWAYS_SOFTWARE || true
mkdir -p "$HOME/axia_g07_task04_wsl2"
OUT="$(mktemp -d "$HOME/axia_g07_task04_wsl2/owner-gui-pregate-XXXXXXXX")"
chmod 700 "$OUT"
CACHE="$HOME/.cache/axia/g07_task04_public_student/$STUDENT_SHA"
GUI_PID=''
RVIZ_WINDOW=0;GAZEBO_WINDOW=0;XWININFO_AVAILABLE=0;FIRST_FAILURE=NONE
finish() {
  local rc=$?
  trap - EXIT INT TERM
  set +e
  if [[ -n "$GUI_PID" ]] && kill -0 "$GUI_PID" 2>/dev/null;then
    kill -INT -- "-$GUI_PID" 2>/dev/null || true
    for _ in {1..30};do kill -0 "$GUI_PID" 2>/dev/null || break;sleep .3;done
    kill -TERM -- "-$GUI_PID" 2>/dev/null || true
    wait "$GUI_PID" 2>/dev/null || true
  fi
  printf 'run_rc=%s\nrviz_window=%s\ngazebo_window=%s\nxwininfo_available=%s\n' "$rc" "$RVIZ_WINDOW" "$GAZEBO_WINDOW" "$XWININFO_AVAILABLE" > "$OUT/window_status.txt"
  echo "$FIRST_FAILURE" > "$OUT/first_failure.txt"
  # Native H01 outputs are inside OUT/native, not in a disposable git checkout.
  # Preserve the primary GUI process/watcher failure even when the secondary
  # DDS RViz Path subscriber timeout is printed later by geometry_l2.
  for raw in "$OUT/native/launch.log" "$OUT/native/d07_gui_watcher.log" \
    "$OUT/native/d07_gui_watcher_exit.txt" "$OUT/native/d07_gui_watcher_started.txt" \
    "$OUT/native/d07_gui_transport_topics.txt" "$OUT/native/d07_h01_geometry.log";do
    if [[ -f "$raw" ]];then
      printf 'NATIVE_FILE=%s\n' "${raw##*/}" >> "$OUT/native_file_manifest.txt"
    fi
  done
  if [[ -f "$HOME/.gz/rendering/ogre2.log" ]];then
    tail -n 150 "$HOME/.gz/rendering/ogre2.log" > "$OUT/wslg_ogre2_last150.txt" || true
  fi
  (cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 | sort -z |
     xargs -0 -r sha256sum > SHA256SUMS) || true
  tar -czf "$OUT.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")" 2>/dev/null || true
  [[ -s "$OUT.tar.gz" ]] && sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256" || true
  echo "AXIA_G07_TASK04_ARCHIVE=$OUT.tar.gz"
  echo "AXIA_G07_TASK04_SHA256=$OUT.tar.gz.sha256"
  echo "AXIA_G07_TASK04_FIRST_FAILURE=$FIRST_FAILURE"
  echo AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit "$rc"
}
trap finish EXIT
trap 'FIRST_FAILURE=OWNER_INTERRUPTED;exit 130' INT
trap 'FIRST_FAILURE=TERMINATED;exit 143' TERM
printf 'mode=%s\nrepo=%s\nsha=%s\npublic_ci_l2=%s\nROS_DOMAIN_ID=%s\nGZ_PARTITION=%s\n' \
 "$MODE" "$STUDENT_REPO" "$STUDENT_SHA" "$TASK03_PUBLIC_L2_RUN" "$ROS_DOMAIN_ID" "$GZ_PARTITION" > "$OUT/manifest.txt"
uname -sr >> "$OUT/manifest.txt"
command -v free >/dev/null && free -h > "$OUT/ram.txt" 2>&1 || true
command -v nvidia-smi >/dev/null && timeout 6s nvidia-smi -L > "$OUT/gpu.txt" 2>&1 || true
command -v glxinfo >/dev/null && timeout 8s glxinfo -B > "$OUT/wslg_glxinfo.txt" 2>&1 || true
set +u
source /opt/ros/jazzy/setup.bash
overlay="$(printenv AXIA_NAV2_OVERLAY_SETUP || true)"
if [[ -n "$overlay" ]];then
  [[ -r "$overlay" ]] || { FIRST_FAILURE=NAV2_OVERLAY_MISSING;exit 3; }
  source "$overlay"
elif [[ -r "$HOME/axia_p1_abc_verification/results/p1-nav2-official-overlay/install/setup.bash" ]];then
  source "$HOME/axia_p1_abc_verification/results/p1-nav2-official-overlay/install/setup.bash"
fi
set -u
for pkg in nav2_bringup nav2_minimal_tb3_sim ros_gz_sim;do
  ros2 pkg prefix "$pkg" >> "$OUT/official_ros_packages.txt" 2>&1 ||
    { FIRST_FAILURE="OFFICIAL_PACKAGE_$pkg";exit 3; }
done
mkdir -p "$(dirname "$CACHE")"
if [[ ! -d "$CACHE/.git" ]];then
  [[ ! -e "$CACHE" ]] || { FIRST_FAILURE=CACHE_NOT_GIT;exit 3; }
  git init -q "$CACHE" || { FIRST_FAILURE=GIT_INIT_FAILED;exit 3; }
  git -C "$CACHE" remote add origin "https://github.com/$STUDENT_REPO.git"
fi
export GIT_TERMINAL_PROMPT=0
git -C "$CACHE" fetch -q --no-tags --depth 1 origin "$STUDENT_SHA" ||
  { FIRST_FAILURE=PUBLIC_SOURCE_FETCH_FAILED;exit 3; }
git -C "$CACHE" -c advice.detachedHead=false checkout -q --detach FETCH_HEAD ||
  { FIRST_FAILURE=SOURCE_CHECKOUT_FAILED;exit 3; }
[[ "$(git -C "$CACHE" rev-parse HEAD)" == "$STUDENT_SHA" ]] ||
  { FIRST_FAILURE=STUDENT_SHA_MISMATCH;exit 3; }
[[ -z "$(git -C "$CACHE" status --porcelain --untracked-files=no)" ]] ||
  { FIRST_FAILURE=STUDENT_TREE_DIRTY;exit 3; }
echo "AXIA_G07_TASK04_PUBLIC_STUDENT_SHA_VERIFIED=$STUDENT_SHA"
RUNTIME="$CACHE/block_B/day07/h01_runtime"
[[ -r "$RUNTIME/scripts/d07_h01_gui_no_goal_once.sh" && -r "$RUNTIME/tools/p2_g07_owner_env_parity.py" ]] ||
  { FIRST_FAILURE=RUNTIME_MISSING;exit 3; }
bash -n "$RUNTIME/scripts/d07_h01_gui_no_goal_once.sh" ||
  { FIRST_FAILURE=GUI_SYNTAX;exit 3; }
bash "$RUNTIME/scripts/d07_h01_gui_no_goal_once.sh" --self-check > "$OUT/gui_static.txt" 2>&1 ||
  { FIRST_FAILURE=GUI_STATIC_CONTRACT;exit 3; }
python3 "$RUNTIME/tools/p2_g07_owner_env_parity.py" --mode owner --output "$OUT/owner_core_parity.json" \
  > "$OUT/owner_core_parity.log" 2>&1 ||
  { FIRST_FAILURE=OWNER_CORE_PARITY_BLOCKED;exit 3; }
python3 - "$OUT/owner_core_parity.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
assert r["status"]=="CORE_PARITY_PASS" and r["mode"]=="owner"
assert r["checked_packages"]==25 and r["checked_official_files"]==5
assert r["wsl_detected"] is True
print("AXIA_G07_TASK04_WSL2_CORE_PARITY_25_5_PASS")
PY
if [[ "$MODE" == --doctor ]];then
  echo 'AXIA_G07_TASK04_WSL2_DOCTOR_PASS NO_ROS_NODES_NO_GAZEBO_NO_GOAL'
  exit 0
fi
# Existing Student GPU-only watcher has an ACK, native gz topic gate and
# first-child-exit log; the earlier default inline watcher hid that evidence.
# Verify the requested D3D12 adapter with GLX; prefer NVIDIA only if it is
# actually selected, otherwise the already observed integrated Intel adapter.
GPU_SELECTED=''
for adapter in NVIDIA Intel;do
  if env -u LIBGL_ALWAYS_SOFTWARE GALLIUM_DRIVER=d3d12 \
       MESA_D3D12_DEFAULT_ADAPTER_NAME="$adapter" timeout 12s glxinfo -B \
       > "$OUT/wslg_glxinfo_adapter_$adapter.txt" 2>&1 &&
     grep -Eiq "OpenGL renderer string: D3D12.*$adapter" "$OUT/wslg_glxinfo_adapter_$adapter.txt";then
    GPU_SELECTED="$adapter";break
  fi
done
[[ -n "$GPU_SELECTED" ]] || { FIRST_FAILURE=WSLG_D3D12_ADAPTER_UNVERIFIED;exit 3; }
export AXIA_D07_H01_GPU_ADAPTER="$GPU_SELECTED"
export AXIA_D07_H01_GPU_GUI_TRIAL=1
unset AXIA_D07_H01_CI_SOFTWARE_GUI || true
printf 'AXIA_G07_TASK04_WSLG_D3D12_ADAPTER_VERIFIED=%s\n' "$GPU_SELECTED"
export AXIA_D07_GUI_EVIDENCE_DIR="$OUT/gui_evidence" AXIA_D07_GUI_HOLD_S=10
export AXIA_P2_SMOKE_RESULTS="$OUT/native"
export AXIA_G07_CI_OWNER_BAG_PARITY=0
# Own exactly the launched simulator, RViz and GUI watcher process session.
# This invocation is finite and NEVER publishes a moving Goal.
setsid timeout --signal=TERM --kill-after=12s 900s \
  bash -c 'cd "$1"; exec bash scripts/d07_h01_gui_no_goal_once.sh --run' _ "$RUNTIME" \
  > "$OUT/gui_run.log" 2>&1 &
GUI_PID=$!
command -v xwininfo >/dev/null 2>&1 && XWININFO_AVAILABLE=1
while kill -0 "$GUI_PID" 2>/dev/null;do
  if ((XWININFO_AVAILABLE));then
    windows="$(timeout 3s xwininfo -root -tree 2>/dev/null || true)"
    grep -Eiq RViz <<< "$windows" && RVIZ_WINDOW=1
    grep -Eiq Gazebo <<< "$windows" && GAZEBO_WINDOW=1
  fi
  sleep 2
done
set +e;wait "$GUI_PID";RC=$?;set -e
GUI_PID=''
echo "AXIA_G07_TASK04_GUI_PREGATE_RUNTIME_RC=$RC RVIZ_X11=$RVIZ_WINDOW GAZEBO_X11=$GAZEBO_WINDOW XWININFO_AVAILABLE=$XWININFO_AVAILABLE"
if [[ "$RC" -ne 0 ]];then
  FIRST_FAILURE=PUBLIC_NO_GOAL_GUI_RUNTIME_FAILED
  # First GUI watcher stage outranks the later DDS Path subscriber symptom.
  if [[ -r "$OUT/native/d07_gui_watcher.log" ]];then
    if grep -Fq D07_H01_GUI_CHILD_TERMINATED_BEFORE_PHASE_COMPLETE "$OUT/native/d07_gui_watcher.log";then
      FIRST_FAILURE=GUI_CHILD_EARLY_EXIT
    elif grep -Fq D07_H01_GUI_TRANSPORT_WORLD_TOPIC_GATE_FAILED "$OUT/native/d07_gui_watcher.log";then
      FIRST_FAILURE=GUI_WORLD_TRANSPORT_GATE
    elif grep -Fq D07_H01_GUI_GPU_TRIAL_SCOPE_DENIED_NO_GOAL "$OUT/native/d07_gui_watcher.log";then
      FIRST_FAILURE=GPU_WATCHER_SCOPE_DENIED
    elif [[ ! -f "$OUT/native/d07_gui_watcher_started.txt" ]];then
      FIRST_FAILURE=GUI_WATCHER_START_ACK_ABSENT
    fi
  fi
  if [[ "$FIRST_FAILURE" == PUBLIC_NO_GOAL_GUI_RUNTIME_FAILED ]] &&
     grep -Fq D07_H01_GUI_RVIZ_PATH_SUBSCRIPTION_ABSENT "$OUT/gui_run.log";then
    FIRST_FAILURE=D07_H01_GUI_RVIZ_PATH_SUBSCRIPTION_ABSENT
  fi
  grep -Ei 'BLOCKED|FIRST|FAILED|ERROR|FATAL|WATCHER|RVIZ_PATH' "$OUT/gui_run.log" |
    head -n 40 > "$OUT/first_errors.txt" || true
  echo "AXIA_G07_TASK04_FIRST_NATIVE_GUI_FAILURE=$FIRST_FAILURE"
  if [[ -r "$OUT/native/d07_gui_watcher_exit.txt" ]];then
    cat "$OUT/native/d07_gui_watcher_exit.txt" | head -n 4 || true
  fi
  exit 3
fi
if ((XWININFO_AVAILABLE)) && (( !RVIZ_WINDOW || !GAZEBO_WINDOW ));then
  FIRST_FAILURE=WSLG_WINDOW_VISIBILITY_UNVERIFIED
  exit 3
fi
echo 'AXIA_G07_TASK04_WSL2_GUI_NO_GOAL_AUTOMATED_PREGATE_PASS'
echo 'AXIA_G07_TASK04_VISUAL_CONTENT_REVIEW_PENDING=true'
echo AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
