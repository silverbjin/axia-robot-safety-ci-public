#!/usr/bin/env bash
# AXIA D07-H01 Owner WSL2: ONE read-only, NO-MOVING-GOAL GUI run.
# Exact private source and actual public ROS/Gazebo/RViz L2 are pinned.
# This is a simulation-only classroom demonstration, NOT P4 G07 motion,
# a certified E-Stop, or AXIA_MVP_DEMO_ACCEPTED.
set -Eeuo pipefail
umask 077

readonly PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'
readonly PRIVATE_SHA='a9f0d2b6ae1f0dcf2e8f92b263d9b66480924c4e'
readonly PUBLIC_REAL_GAZEBO_XVFB_L2_RUN='43817527534'
readonly PUBLIC_NO_ROS_L0_RUN='43793526290'
readonly CI_CONTAINER_DIGEST='sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e'

# Bounded read-only WSLg GUI screenshot and resource capture. Never auto PASS.
axia_d07_capture_render_evidence() {
  local run_dir="${1:-}" tag="${2:-initial}"
  [[ -n "$run_dir" && -d "$run_dir" && ! -L "$run_dir" ]] || return 3
  [[ "$tag" == initial || "$tag" == late || "$tag" == selfcheck ]] || return 3
  local dir="$run_dir/gui_diagnostics" tree id title output
  mkdir -p -- "$dir" || return 3
  printf '{"tag":"%s","utc":"%s"}\n' "$tag" "$(date -u +%FT%TZ)" >> "$dir/resource_samples.jsonl"
  {
    echo "sample=$tag"
    date -u +%FT%TZ
    echo "LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-unset}"
    echo "DISPLAY_PRESENT=$([[ -n "${DISPLAY:-}" ]] && echo yes || echo no)"
    cat /proc/loadavg /proc/pressure/cpu /proc/pressure/memory 2>/dev/null || true
    free -m 2>/dev/null || true
    ps -eo pid,ppid,stat,comm,%cpu,%mem,rss --sort=-%cpu 2>/dev/null | head -n 24 || true
  } >> "$dir/resources_processes.txt" 2>&1
  if [[ "$tag" == initial || "$tag" == selfcheck ]]; then
    if command -v glxinfo >/dev/null; then
      timeout 8s glxinfo -B > "$dir/glxinfo_B.txt" 2>&1 || \
        echo GLXINFO_PROBE_FAILED_OR_TIMEOUT >> "$dir/glxinfo_B.txt"
    else
      echo 'GLXINFO_NOT_INSTALLED' > "$dir/glxinfo_B.txt"
    fi
    if command -v nvidia-smi >/dev/null; then
      timeout 8s nvidia-smi -L > "$dir/nvidia_smi.txt" 2>&1 || true
    else
      echo 'NVIDIA_SMI_NOT_AVAILABLE' > "$dir/nvidia_smi.txt"
    fi
    if [[ -r "$HOME/.gz/rendering/ogre2.log" ]]; then
      tail -n 180 "$HOME/.gz/rendering/ogre2.log" > "$dir/ogre2_gui.log"
    else
      echo 'OGRE2_LOG_NOT_PRESENT' > "$dir/ogre2_gui.log"
    fi
  fi
  tree="$(xwininfo -root -tree 2>/dev/null || true)"
  printf '%s\n' "$tree" > "$dir/x11_tree_$tag.txt"
  for title in Gazebo RViz; do
    id="$(printf '%s\n' "$tree" | grep -Ei "\"[^\"]*${title}[^\"]*\"" | \
         awk 'NR==1 {print $1}' || true)"
    case "$id" in
      0x[0-9a-fA-F]*)
        if command -v xwd >/dev/null; then
          if [[ "$title" == Gazebo ]]; then
            output="$dir/gazebo_scene.xwd"
            [[ "$tag" == late ]] && output="$dir/gazebo_scene_late.xwd"
          else
            output="$dir/rviz_scene.xwd"
            [[ "$tag" == late ]] && output="$dir/rviz_scene_late.xwd"
          fi
          timeout 8s xwd -silent -id "$id" -out "$output" 2>> "$dir/xwd_capture.log" || {
            rm -f -- "$output"
            echo "XWD_CAPTURE_FAILED title=$title tag=$tag" >> "$dir/xwd_capture.log"
          }
        else
          echo 'XWD_NOT_INSTALLED' >> "$dir/xwd_capture.log"
        fi
        ;;
      *) echo "X11_WINDOW_ID_UNAVAILABLE title=$title tag=$tag" >> "$dir/xwd_capture.log";;
    esac
  done
}
# Shared production and public CI L0 pre-ROS watcher lifecycle.
axia_d07_watch_start() {
  local run_dir="${1:-}"
  [[ -n "$run_dir" && -d "$run_dir" && ! -L "$run_dir" ]] || {
    echo 'AXIA_D07_H01_WATCH_DIR_INVALID_NO_ROS' >&2; return 3;
  }
  WATCH="$run_dir/.x11_watch_alive"
  WINDOWS="$run_dir/x11_real_windows.txt"
  [[ -n "$WATCH" && "$WATCH" == "$run_dir/.x11_watch_alive" ]] || {
    echo 'AXIA_D07_H01_WATCH_PATH_EMPTY_NO_ROS' >&2; return 3;
  }
  (umask 077; : > "$WATCH") || {
    echo 'AXIA_D07_H01_WATCH_CREATE_FAILED_NO_ROS' >&2; return 3;
  }
  [[ -f "$WATCH" ]] || return 3
  (
    observed=0
    while [[ -e "$WATCH" ]]; do
      tree="$(xwininfo -root -tree 2>/dev/null || true)"
      if grep -Eiq 'RViz' <<<"$tree"; then echo 'RVIZ' >> "$WINDOWS"; fi
      if grep -Eiq 'Gazebo' <<<"$tree"; then echo 'GAZEBO' >> "$WINDOWS"; fi
      if grep -Eiq 'Gazebo' <<<"$tree" && grep -Eiq 'RViz' <<<"$tree"; then
        observed=$((observed+1))
        if [[ "$observed" -eq 3 ]]; then
          axia_d07_capture_render_evidence "$run_dir" initial || true
        elif [[ "$observed" -eq 9 ]]; then
          axia_d07_capture_render_evidence "$run_dir" late || true
        fi
      fi
      sleep 2
    done
  ) &
  WATCH_PID=$!
  [[ "$WATCH_PID" =~ ^[0-9]+$ ]] || {
    echo 'AXIA_D07_H01_WATCH_PROCESS_NOT_STARTED' >&2; return 3;
  }
}
axia_d07_watch_stop() {
  [[ -z "${WATCH:-}" ]] || rm -f -- "$WATCH"
  if [[ -n "${WATCH_PID:-}" ]]; then
    kill "$WATCH_PID" 2>/dev/null || true
    wait "$WATCH_PID" 2>/dev/null || true
  fi
  WATCH_PID=''
  WATCH=''
}
# Runs exactly once on any Owner failure after RUN creation. All evidence
# comes from this run's isolated directory, never gh auth or private HOME.
axia_d07_pack_failure() {
  local folder="${1:-}"
  [[ -n "$folder" && -d "$folder" && ! -L "$folder" &&
     "$(basename "$folder")" == d07-h01-owner-* ]] || {
    echo 'AXIA_D07_H01_FAILURE_BUNDLE_DIR_INVALID' >&2; return 3;
  }
  (cd "$folder" &&
    find . -type f ! -name SHA256SUMS -print0 |
    sort -z | xargs -0 -r sha256sum > SHA256SUMS) || return 3
  if [[ ! -f "$folder.tar.gz" ]]; then
    tar -czf "$folder.tar.gz" -C "$(dirname "$folder")" "$(basename "$folder")" || return 3
  fi
  sha256sum "$folder.tar.gz" > "$folder.tar.gz.sha256" || return 3
  echo "AXIA_D07_H01_OWNER_FIRST_FAILURE_ARCHIVE=$folder.tar.gz"
}
if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# == 1 && "$PRIVATE_SHA" =~ ^[0-9a-f]{40}$ &&
     "$PUBLIC_REAL_GAZEBO_XVFB_L2_RUN" =~ ^[0-9]{11}$ ]] || exit 3
  # Compile exactly the embedded L3 verdict code before any WSL2/Gazebo work.
  # This check is purely static; no ROS imports or fabricated acceptance.
  python3 - "$0" <<'PYCHECK'
from pathlib import Path
import sys
source=Path(sys.argv[1]).read_text()
tag="<<'PY'\n"
start=source.rfind(tag)
if start<0:
    raise SystemExit("D07_H01_OWNER_VERDICT_HEREDOC_NOT_FOUND")
start+=len(tag)
end=source.index("\nPY\nVERDICT_RC=",start)
compile(source[start:end],"<d07_h01_owner_embedded_verifier>","exec")
print("AXIA_D07_H01_OWNER_PY_VERDICT_STATIC_COMPILE_PASS")
PYCHECK
  CHECK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/d07-h01-owner-check-XXXXXXXX")"
  trap 'axia_d07_watch_stop; rm -rf -- "$CHECK_DIR" "$CHECK_DIR.tar.gz" "$CHECK_DIR.tar.gz.sha256"' EXIT
  axia_d07_watch_start "$CHECK_DIR"
  [[ -n "$WATCH" && -f "$WATCH" && "$WATCH_PID" =~ ^[0-9]+$ ]] || exit 3
  axia_d07_watch_stop
  [[ ! -e "$CHECK_DIR/.x11_watch_alive" ]] || exit 3
  echo 'AXIA_D07_H01_WATCH_SENTINEL_LIFECYCLE_L0_PASS'
  axia_d07_capture_render_evidence "$CHECK_DIR" selfcheck
  [[ -s "$CHECK_DIR/gui_diagnostics/resource_samples.jsonl" &&
     -s "$CHECK_DIR/gui_diagnostics/glxinfo_B.txt" ]] || exit 3
  echo 'AXIA_D07_H01_RENDER_RESOURCE_PROBE_L0_PASS_NO_DISPLAY'
  echo 'simulated PRE-ROS failure fixture, NOT an Owner run' > "$CHECK_DIR/fixture.txt"
  axia_d07_pack_failure "$CHECK_DIR" >/dev/null
  [[ -f "$CHECK_DIR.tar.gz" && -s "$CHECK_DIR.tar.gz.sha256" ]] || exit 3
  (cd "$(dirname "$CHECK_DIR")" && sha256sum -c "$(basename "$CHECK_DIR").tar.gz.sha256" >/dev/null) || exit 3
  tar -tzf "$CHECK_DIR.tar.gz" > "$CHECK_DIR/tar_listing.txt" || exit 3
  grep -Fq 'fixture.txt' "$CHECK_DIR/tar_listing.txt" || exit 3
  echo 'AXIA_D07_H01_FAILURE_BUNDLE_L0_PASS'
  echo "AXIA_D07_H01_OWNER_BOOTSTRAP_STATIC_L0_PASS pinned_private=$PRIVATE_SHA public_l2=$PUBLIC_REAL_GAZEBO_XVFB_L2_RUN"
  echo 'NO_ROS_NO_GAZEBO_NO_GOAL OWNER_WSL2_L3_NOT_RUN'
  exit 0
fi
[[ $# == 0 || ( $# == 1 && "$1" == '--run' ) ]] || {
  echo 'AXIA_D07_H01_OWNER_USAGE=--self-check|--run' >&2
  exit 3
}
[[ -t 0 && -t 1 ]] || {
  echo 'AXIA_D07_H01_OWNER_BLOCKED_INTERACTIVE_WSL2_TTY_REQUIRED' >&2
  exit 3
}
[[ -r /etc/os-release ]] || exit 3
# shellcheck disable=SC1091
source /etc/os-release
[[ "$ID" == 'ubuntu' && "$VERSION_ID" == '24.04' ]] || {
  echo 'AXIA_D07_H01_OWNER_BLOCKED_UBUNTU_2404_REQUIRED' >&2
  exit 3
}
grep -qiE 'microsoft|wsl2' /proc/sys/kernel/osrelease || {
  echo 'AXIA_D07_H01_OWNER_BLOCKED_WSL2_REQUIRED' >&2
  exit 3
}
[[ "${GITHUB_ACTIONS:-}" != 'true' && -n "${DISPLAY:-}" &&
   -r /opt/ros/jazzy/setup.bash ]] || {
  echo 'AXIA_D07_H01_OWNER_BLOCKED_WSLG_DISPLAY_OR_JAZZY_MISSING' >&2
  exit 3
}
for exe in gh git bash python3 mktemp sha256sum tee timeout gz rviz2 ros2 colcon; do
  command -v "$exe" >/dev/null || {
    echo "AXIA_D07_H01_OWNER_BLOCKED_MISSING_CMD=$exe" >&2
    exit 3
  }
done
gh auth status >/dev/null 2>&1 || {
  echo 'AXIA_D07_H01_OWNER_BLOCKED_GH_PRIVATE_AUTH_REQUIRED: gh auth login' >&2
  exit 3
}
for flag in AXIA_G07_CI_SIM_GOAL_ALLOWED AXIA_P3_S01_CI_GOAL_ALLOWED \
            AXIA_P3_S03_CI_COMPOUND_ALLOWED AXIA_P3_S04_CI_PNU_ALLOWED \
            AXIA_P3_S05_CI_GOAL_ALLOWED; do
  [[ "${!flag:-0}" != 1 ]] || {
    echo "AXIA_D07_H01_OWNER_BLOCKED_MOVING_GOAL_FLAG=$flag" >&2
    exit 3
  }
done
# This is exactly the visual window probe used by the successful public L2.
if ! command -v xwininfo >/dev/null; then
  command -v sudo >/dev/null || {
    echo 'AXIA_D07_H01_OWNER_BLOCKED_X11_UTILS_REQUIRED: sudo apt-get install -y x11-utils' >&2
    exit 3
  }
  echo 'AXIA_D07_H01_OWNER_INSTALLING_X11_UTILS_ONCE'
  sudo env DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends x11-utils
fi
command -v xwininfo >/dev/null || exit 3

ROOT="$HOME/.axia_d07_h01_owner_evidence"
mkdir -p -- "$ROOT"
chmod 700 "$ROOT"
RUN="$(mktemp -d "$ROOT/d07-h01-owner-XXXXXXXX")"
WORK="$(mktemp -d "$HOME/.axia_d07_h01_checkout_XXXXXXXX")"
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  set +e
  axia_d07_watch_stop
  cd "$HOME" 2>/dev/null || cd /
  if [[ "$rc" != 0 && -d "${RUN:-}" ]]; then
    printf 'owner_bootstrap_exit_code=%s\n' "$rc" > "$RUN/bootstrap_first_exit.txt"
    timeout 5s xwininfo -root -tree > "$RUN/x11_last_snapshot.txt" 2>&1 || true
    axia_d07_pack_failure "$RUN" || \
      echo "AXIA_D07_H01_FAILURE_BUNDLE_CREATION_FAILED_ROOT=$RUN" >&2
  fi
  if [[ "$WORK" == "$HOME"/.axia_d07_h01_checkout_* && -d "$WORK" ]]; then
    rm -rf -- "$WORK"
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Credential-free WSLg/ROS package provenance preserved on every failure.
{
  printf 'private_source_sha=%s\npublic_real_l2_run=%s\n' "$PRIVATE_SHA" "$PUBLIC_REAL_GAZEBO_XVFB_L2_RUN"
  printf 'display_present=%s\n' "$([[ -n "${DISPLAY:-}" ]] && echo yes || echo no)"
  uname -sr
  grep -E '^(NAME|VERSION_ID)=' /etc/os-release || true
  dpkg-query -W ros-jazzy-nav2-bringup ros-jazzy-rviz2 2>/dev/null || true
} > "$RUN/bootstrap_versions.txt"

gh repo clone "$PRIVATE_REPO" "$WORK/instructor" -- \
  --filter=blob:none --no-checkout --quiet
git -C "$WORK/instructor" fetch --no-tags --depth 1 origin "$PRIVATE_SHA"
git -C "$WORK/instructor" -c advice.detachedHead=false \
  checkout --quiet --detach "$PRIVATE_SHA"
[[ "$(git -C "$WORK/instructor" rev-parse HEAD)" == "$PRIVATE_SHA" &&
   -z "$(git -C "$WORK/instructor" status --porcelain)" ]] || {
  echo 'AXIA_D07_H01_OWNER_BLOCKED_PINNED_PRIVATE_CHECKOUT_MISMATCH' >&2
  exit 3
}
PRIVATE_RUNNER="$WORK/instructor/scripts/d07_h01_gui_no_goal_once.sh"
[[ -s "$PRIVATE_RUNNER" ]] || exit 3
bash -n "$PRIVATE_RUNNER"
bash "$PRIVATE_RUNNER" --doctor || {
  echo 'AXIA_D07_H01_OWNER_BLOCKED_PRIVATE_JAZZY_DOCTOR' >&2
  exit 3
}

export ROS_DOMAIN_ID=95
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_PARTITION="axia_p2_d07_owner_${ROS_DOMAIN_ID}_$$_$(date +%s)"
export AXIA_P2_SMOKE_RESULTS="$RUN/real-l2"
export AXIA_D07_GUI_EVIDENCE_DIR="$RUN/rviz"
export AXIA_D07_GUI_HOLD_S=8
export AXIA_G07_CI_OWNER_OBSERVER_PARITY=1
export AXIA_G07_CI_SIM_GOAL_ALLOWED=0
export LIBGL_ALWAYS_SOFTWARE=1
export QT_QPA_PLATFORM=xcb
export QT_X11_NO_MITSHM=1

echo "AXIA_D07_H01_OWNER_PRIVATE_SOURCE_VERIFIED=$PRIVATE_SHA"
echo "AXIA_D07_H01_CI_SAME_SHA_GAZEBO_XVFB_L2_PASS_RUN=$PUBLIC_REAL_GAZEBO_XVFB_L2_RUN"
echo "AXIA_D07_H01_CI_L0_PASS_RUN=$PUBLIC_NO_ROS_L0_RUN"
echo "AXIA_D07_H01_CI_RUNTIME_DIGEST=$CI_CONTAINER_DIGEST"
echo 'AXIA_D07_H01_OWNER_WSLG_KERNEL_GPU_PARITY_NOT_YET_VERIFIED'
echo 'D07_H01_SIMULATED_NOISE_FREE_LIDAR_ONLY: not real sensor safety'
echo 'NO NavigateToPose / NO cmd_vel / NO certified hardware E-Stop'
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD; this validates only D07-H01 GUI L3'
echo "AXIA_D07_H01_OWNER_EVIDENCE_ROOT=$RUN"
# D07 GPU experiment is opt-in, only AFTER the Windows/WSLg D3D12
# OpenGL hardware path is demonstrated, before ANY Gazebo/ROS process.
command -v glxinfo >/dev/null || {
  echo AXIA_D07_GPU_PREFLIGHT_BLOCKED_GLXINFO_MISSING >&2
  echo 'Install Ubuntu mesa-utils, then do --self-check without ROS.' >&2
  exit 3
}
set +e
# Do not depend on the Owner's permanent ~/.bashrc GALLIUM_DRIVER.
env -u LIBGL_ALWAYS_SOFTWARE \
  GALLIUM_DRIVER=d3d12 \
  MESA_D3D12_DEFAULT_ADAPTER_NAME="${AXIA_D07_H01_GPU_ADAPTER:-NVIDIA}" \
  glxinfo -B > "$RUN/gpu_glxinfo_unforced.txt" 2>&1
GPU_PROBE_RC=$?
set -e
if [[ "$GPU_PROBE_RC" != 0 ]] ||
   ! grep -Eiq 'D3D12 \(' "$RUN/gpu_glxinfo_unforced.txt" ||
   ! grep -Eiq 'Accelerated:[[:space:]]*yes' "$RUN/gpu_glxinfo_unforced.txt"; then
  echo 'AXIA_D07_GPU_PREFLIGHT_HOLD_NOT_D3D12_ACCELERATED' >&2
  echo 'Do not launch the expensive ROS+Gazebo demo in software mode.' >&2
  exit 3
fi
export AXIA_D07_H01_GPU_GUI_TRIAL=1
export AXIA_D07_H01_GPU_ADAPTER="${AXIA_D07_H01_GPU_ADAPTER:-NVIDIA}"
echo "AXIA_D07_GUI_GPU_PREFLIGHT_D3D12_ACCELERATED adapter=$AXIA_D07_H01_GPU_ADAPTER"
echo "AXIA_D07_GPU_GUI_TRIAL_PRIVATE_SOURCE=$PRIVATE_SHA"
# Server, physics/sensors, Nav2 and safety nodes keep their baseline
# environment. The private GUI children opt-in to D3D12 individually.
# This also neutralizes accidental global ~/.bashrc GALLIUM_DRIVER=d3d12.
unset GALLIUM_DRIVER MESA_D3D12_DEFAULT_ADAPTER_NAME
# Never allow the CI software-GL fallback inside Owner WSL2.
unset AXIA_D07_H01_CI_SOFTWARE_GUI
echo AXIA_D07_GPU_GUI_SERVER_RENDER_ENV_ISOLATED

echo 'AXIA_D07_H01_CI_SAME_SHA_GAZEBO_XVFB_L2_PASS_WSLG_D3D12_GUI_NOT_VERIFIED'
# Capture-only tools; if unavailable, record the dependency boundary and
# still run the unchanged original ROS simulation (visual verdict stays HOLD).
if ! command -v xwd >/dev/null || ! command -v glxinfo >/dev/null; then
  (
    set +e
    echo 'D07_H01_RENDER_DIAGNOSTICS_OPTIONAL_PACKAGES=x11-apps mesa-utils'
    if command -v sudo >/dev/null; then
      sudo env DEBIAN_FRONTEND=noninteractive apt-get update -qq &&
      sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends x11-apps mesa-utils
    else
      echo 'SUDO_MISSING_RENDER_CAPTURE_TOOLS_NOT_INSTALLED'
    fi
    command -v xwd || echo XWD_NOT_INSTALLED
    command -v glxinfo || echo GLXINFO_NOT_INSTALLED
  ) > "$RUN/renderer_probe_dependencies.log" 2>&1 || true
fi

# Same X11 watcher lifecycle as --self-check, no separate shell recipe.
axia_d07_watch_start "$RUN"

set +e
bash "$PRIVATE_RUNNER" --run 2>&1 | tee "$RUN/owner_stdout.log"
RUNNER_RC=${PIPESTATUS[0]}
set -e
# FIRST GUI execution boundary outranks later DDS subscriber failure
# or FileNotFoundError (Owner mVWZNr7m source evidence had a zero-byte
# watcher log and no GUI/transport file despite the free baseline marker).
if [[ "$RUNNER_RC" != 0 ]]; then
  GUI_L2="$RUN/real-l2"
  FIRST_GUI_ERROR=''
  if [[ -s "$GUI_L2/d07_gui_watcher.log" ]]; then
    FIRST_GUI_ERROR="$(grep -m1 -E 'D07_H01_GUI_(CHILD_TERMINATED|WATCHER_|TRANSPORT_|GPU_TRIAL_SCOPE_DENIED|AFTER_FREE_BASELINE_MARKER_MISSING)' "$GUI_L2/d07_gui_watcher.log" || true)"
  fi
  if [[ -z "$FIRST_GUI_ERROR" && -s "$GUI_L2/d07_gui_watcher_exit.txt" ]]; then
    FIRST_GUI_ERROR="D07_H01_GUI_WATCHER_EXITED_BEFORE_DDS"
  elif [[ -z "$FIRST_GUI_ERROR" && ! -s "$GUI_L2/d07_gui_watcher_started.txt" ]]; then
    FIRST_GUI_ERROR="D07_H01_GUI_WATCHER_SPAWN_ACK_ABSENT"
  elif [[ -z "$FIRST_GUI_ERROR" && ! -s "$GUI_L2/d07_gui_watcher.log" ]]; then
    FIRST_GUI_ERROR="D07_H01_GUI_WATCHER_LOG_EMPTY_BEFORE_DDS"
  fi
  if [[ -n "$FIRST_GUI_ERROR" ]]; then
    printf '%s\n' "$FIRST_GUI_ERROR" > "$RUN/owner_first_gui_boundary.txt"
    echo "AXIA_D07_H01_FIRST_GUI_FAILURE_FROM_WATCHER=$FIRST_GUI_ERROR"
  fi
fi
axia_d07_watch_stop

# Read-only scoped L3 verifier: same pure three-phase oracle as the L2 workflow,
# plus original exit status and physically observed X11 window titles.
set +e
python3 - "$WORK/instructor/tools" "$RUN" "$PRIVATE_SHA" "$RUNNER_RC" \
  "$PUBLIC_REAL_GAZEBO_XVFB_L2_RUN" <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from d07_h01_path_visual import assess_gui_stages
root=Path(sys.argv[2])
source=sys.argv[3]
runner_rc=int(sys.argv[4])
ci_run=int(sys.argv[5])
report_file=root/'owner_l3_verdict.json'
evidence_root=root/'real-l2'/'d07_h01_geometry'
windows=set((root/'x11_real_windows.txt').read_text().splitlines()) if (
    root/'x11_real_windows.txt').exists() else set()
reason='SOURCE_EVIDENCE_MISSING_OR_NOT_VERIFIED'
phases=[]
geo={}
scope={}
try:
    geo=json.loads((evidence_root/'d07_h01_geometry.json').read_text())
    phases=[json.loads(s) for s in (
        evidence_root/'phase_evidence.jsonl').read_text().splitlines()]
    scope=assess_gui_stages(phases,source_sha=source,
         actual_ros=geo.get('real_nav2') is True,
         actual_gazebo=geo.get('obstacle_pose_native_ack') is True,
         rviz_window='RVIZ' in windows)
    require=(runner_rc==0
        and 'RVIZ' in windows and 'GAZEBO' in windows
        and geo.get('source_sha')==source
        and geo.get('goal_sent') is False
        and geo.get('real_nav2') is True
        and geo.get('real_laser_scan') is True
        and geo.get('actual_costmap_obstacle_observed') is True
        and geo.get('obstacle_restored_away') is True
        and geo.get('route_oracle',{}).get('geometry_ready') is True
        and geo.get('certified_estop') is False
        and geo.get('formal_accepted') is False
        and scope.get('ready') is True)
    if runner_rc!=0:
        reason='ORIGINAL_NO_GOAL_RUNNER_FAILED'
    elif not {'RVIZ','GAZEBO'}<=windows:
        reason='REAL_X11_GAZEBO_OR_RVIZ_WINDOW_NOT_OBSERVED'
    elif not require:
        reason=scope.get('first_failed_boundary','EXACT_REAL_GEOMETRY_GATE_HOLD')
    else:
        reason='SCOPED_READONLY_GUI_REAL_PHASES_AND_X11_PROVEN'
except (OSError,ValueError,TypeError,KeyError,ImportError) as exc:
    require=False
    reason='PROVENANCE_OR_REPORT_INVALID_'+type(exc).__name__
first_gui_file=root/'owner_first_gui_boundary.txt'
first_gui_boundary=(first_gui_file.read_text().strip()
                    if runner_rc!=0 and first_gui_file.is_file() else '')
if first_gui_boundary:
    reason=first_gui_boundary
# Actual WSL2 X11 window titles and ROS/DDS do NOT prove rendered 3D
# pixels. Current Owner Xoszr6rv demonstrates why. Snapshot files must
# be manually reviewed for robot+world and RViz TF/map, never auto-accepted.
frame_dir=root/'gui_diagnostics'
frames=[p.name for p in frame_dir.glob('*.xwd') if p.is_file() and p.stat().st_size>=512] if frame_dir.is_dir() else []
resource_present=(frame_dir/'resource_samples.jsonl').is_file()
source_scope_ready=bool(require)
if source_scope_ready:
    reason=('OWNER_GUI_SCENE_PIXEL_REVIEW_PENDING' if frames
            else 'OWNER_GUI_SCENE_PIXELS_UNVERIFIED')
out={
    'schema':'axia_d07_h01_owner_gui_l3_scoped_v2_visual_review',
    'status':'D07_H01_OWNER_GUI_VISUAL_HOLD',
    'reason':reason,
    'first_missing_visual_boundary':(first_gui_boundary or
        (reason if source_scope_ready else 'ROS_SOURCE_OR_X11_NOT_READY')),
    'first_gui_boundary':first_gui_boundary or None,
    'private_source_sha':source,
    'public_same_source_gazebo_xvfb_l2_run_not_wslg_gpu':ci_run,
    'owner_runner_rc':runner_rc,
    'rviz_x11_window_observed':'RVIZ' in windows,
    'gazebo_x11_window_observed':'GAZEBO' in windows,
    'stage_names':[x.get('stage') for x in phases if isinstance(x,dict)],
    'official_path_pose_counts':[x.get('pose_count') for x in phases if isinstance(x,dict)],
    'gui_stage_oracle':scope,
    'owner_wsl2_source_l3_verified':source_scope_ready,
    'owner_wsl2_gui_l3_accepted':False,
    'gazebo_3d_scene_render_proven':False,
    'rviz_robot_visual_render_proven':False,
    'render_frame_files':frames,
    'resource_probe_file_present':resource_present,
    'visual_review_required':True,
    'moving_goal_accepted':False,
    'formal_axia_mvp_accepted':False,
    'certified_estop':False,
}
report_file.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print('AXIA_D07_H01_OWNER_L3_VERDICT '+json.dumps(out,sort_keys=True))
print('AXIA_D07_H01_OWNER_L3_EVIDENCE='+str(report_file))
if source_scope_ready:
    print('D07_H01_OWNER_ROS_PATH_L3_VERIFIED_GUI_VISUAL_HOLD NO_MOVING_GOAL')
print('D07_H01_OWNER_GUI_VISUAL_HOLD FIRST_BOUNDARY='+reason)
# Synthetic screenshots or X11 title matching CANNOT promote this to L3.
sys.exit(3)
PY
VERDICT_RC=$?
set -e

(cd "$RUN" && find . -type f ! -name SHA256SUMS -print0 |
  sort -z | xargs -0 -r sha256sum > SHA256SUMS)
echo "AXIA_D07_H01_OWNER_RAW_EVIDENCE_PRESERVED=$RUN"
if [[ "$RUNNER_RC" != 0 || "$VERDICT_RC" != 0 ]]; then
  echo 'NO REPEATED WSL2 RETRY: import first reproducible boundary into public CI.'
  # Exit trap now packs ALL evidence including the earliest shell error.
  exit 3
fi
echo "AXIA_D07_H01_OWNER_GAZEBO_RVIZ_WSL2_L3_SCOPE_ACCEPTED=$RUN"
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD (not part of this classroom-only GUI result)'
