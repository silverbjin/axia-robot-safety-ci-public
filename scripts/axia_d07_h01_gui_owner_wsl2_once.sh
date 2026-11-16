#!/usr/bin/env bash
# AXIA D07-H01 Owner WSL2: ONE read-only, NO-MOVING-GOAL GUI run.
# Exact private source and actual public ROS/Gazebo/RViz L2 are pinned.
# This is a simulation-only classroom demonstration, NOT P4 G07 motion,
# a certified E-Stop, or AXIA_MVP_DEMO_ACCEPTED.
set -Eeuo pipefail
umask 077

readonly PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'
readonly PRIVATE_SHA='0e16c3781cdee603518a653f120a3be352e5f7b2'
readonly PUBLIC_REAL_GAZEBO_L2_RUN='43793585641'
readonly PUBLIC_NO_ROS_L0_RUN='43793526290'
readonly CI_CONTAINER_DIGEST='sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e'

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
    while [[ -e "$WATCH" ]]; do
      tree="$(xwininfo -root -tree 2>/dev/null || true)"
      if grep -Eiq 'RViz' <<<"$tree"; then echo 'RVIZ' >> "$WINDOWS"; fi
      if grep -Eiq 'Gazebo' <<<"$tree"; then echo 'GAZEBO' >> "$WINDOWS"; fi
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
if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# == 1 && "$PRIVATE_SHA" =~ ^[0-9a-f]{40}$ &&
     "$PUBLIC_REAL_GAZEBO_L2_RUN" =~ ^[0-9]{11}$ ]] || exit 3
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
  echo "AXIA_D07_H01_OWNER_BOOTSTRAP_STATIC_L0_PASS pinned_private=$PRIVATE_SHA public_l2=$PUBLIC_REAL_GAZEBO_L2_RUN"
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
  if [[ "$WORK" == "$HOME"/.axia_d07_h01_checkout_* && -d "$WORK" ]]; then
    rm -rf -- "$WORK"
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

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
echo "AXIA_D07_H01_CI_REAL_GAZEBO_L2_PASS_RUN=$PUBLIC_REAL_GAZEBO_L2_RUN"
echo "AXIA_D07_H01_CI_L0_PASS_RUN=$PUBLIC_NO_ROS_L0_RUN"
echo "AXIA_D07_H01_CI_RUNTIME_DIGEST=$CI_CONTAINER_DIGEST"
echo 'AXIA_D07_H01_OWNER_WSLG_KERNEL_GPU_PARITY_NOT_YET_VERIFIED'
echo 'D07_H01_SIMULATED_NOISE_FREE_LIDAR_ONLY: not real sensor safety'
echo 'NO NavigateToPose / NO cmd_vel / NO certified hardware E-Stop'
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD; this validates only D07-H01 GUI L3'
echo "AXIA_D07_H01_OWNER_EVIDENCE_ROOT=$RUN"

# Same X11 watcher lifecycle as --self-check, no separate shell recipe.
axia_d07_watch_start "$RUN"

set +e
bash "$PRIVATE_RUNNER" --run 2>&1 | tee "$RUN/owner_stdout.log"
RUNNER_RC=${PIPESTATUS[0]}
set -e
axia_d07_watch_stop

# Read-only scoped L3 verifier: same pure three-phase oracle as the L2 workflow,
# plus original exit status and physically observed X11 window titles.
set +e
python3 - "$WORK/instructor/tools" "$RUN" "$PRIVATE_SHA" "$RUNNER_RC" \
  "$PUBLIC_REAL_GAZEBO_L2_RUN" <<'PY'
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
out={
    'schema':'axia_d07_h01_owner_gui_l3_scoped_v1',
    'status':('D07_H01_OWNER_WSL2_GUI_L3_ACCEPTED'
              if require else 'D07_H01_OWNER_WSL2_GUI_L3_HOLD'),
    'reason':reason,
    'private_source_sha':source,
    'public_real_gazebo_l2_run':ci_run,
    'owner_runner_rc':runner_rc,
    'rviz_x11_window_observed':'RVIZ' in windows,
    'gazebo_x11_window_observed':'GAZEBO' in windows,
    'stage_names':[x.get('stage') for x in phases if isinstance(x,dict)],
    'official_path_pose_counts':[x.get('pose_count') for x in phases
                                 if isinstance(x,dict)],
    'gui_stage_oracle':scope,
    'owner_wsl2_gui_l3_accepted':bool(require),
    'moving_goal_accepted':False,
    'formal_axia_mvp_accepted':False,
    'certified_estop':False,
}
report_file.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print('AXIA_D07_H01_OWNER_L3_VERDICT '+json.dumps(out,sort_keys=True))
print('AXIA_D07_H01_OWNER_L3_EVIDENCE='+str(report_file))
if require:
    print('D07_H01_OWNER_WSL2_GUI_L3_ACCEPTED NO_MOVING_GOAL')
else:
    print('D07_H01_OWNER_WSL2_GUI_L3_HOLD FIRST_BOUNDARY='+reason)
sys.exit(0 if require else 3)
PY
VERDICT_RC=$?
set -e

(cd "$RUN" && find . -type f ! -name SHA256SUMS -print0 |
  sort -z | xargs -0 -r sha256sum > SHA256SUMS)
echo "AXIA_D07_H01_OWNER_RAW_EVIDENCE_PRESERVED=$RUN"
if [[ "$RUNNER_RC" != 0 || "$VERDICT_RC" != 0 ]]; then
  tar -czf "$RUN.tar.gz" -C "$(dirname "$RUN")" "$(basename "$RUN")"
  sha256sum "$RUN.tar.gz" > "$RUN.tar.gz.sha256"
  echo "AXIA_D07_H01_OWNER_FIRST_FAILURE_ARCHIVE=$RUN.tar.gz"
  echo 'NO REPEATED WSL2 RETRY: import first reproducible boundary into public CI.'
  exit 3
fi
echo "AXIA_D07_H01_OWNER_GAZEBO_RVIZ_WSL2_L3_SCOPE_ACCEPTED=$RUN"
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD (not part of this classroom-only GUI result)'
