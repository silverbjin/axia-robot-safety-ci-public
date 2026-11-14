#!/usr/bin/env bash
# D06 WSL2 classroom: P4 G11 PINNED Owner real G07 + read-only RViz2.
# SIM ONLY, SINGLE MANUAL TTY GOAL. Never changes safety TTL or Guard.
set -Eeuo pipefail
umask 077
readonly P4_PUBLIC_RELEASE_SHA='d1769b8675c85e7ee564966637cef9113435904a'
readonly P4_OWNER_PRIVATE_SHA='afe4e9ae3f6542ef7b2bd3097ce5c15ae5a5ddcc'
readonly P4_OWNER_PRIVATE_TREE='580dec5be1988b26d5189616b1b01559a0f1f9a5'
readonly P4_G11_SCRIPT='scripts/axia_p4_g11_owner_g07_rmw_provenance_once.sh'
# The G11 owner release itself sets AXIA_P2_OWNER_PINNED_SHA and collects
# YES-P2-G07-GOAL on a physical TTY. No AXIA_G07_CI_SIM_GOAL_ALLOWED override.
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
SIDECAR="$ROOT/d06/scripts/d06_rviz_sidecar.sh"
MONITOR="$ROOT/d06/live/d06_readonly_monitor.py"
TRIAGE="$ROOT/d06/live/d06_g07_field_triage.py"
RVIZ_CONFIG="$ROOT/d06/rviz/d06_safety_bubble.rviz"

self_check() {
  for p in "$SIDECAR" "$MONITOR" "$TRIAGE" "$RVIZ_CONFIG"; do
    [[ -s "$p" ]] || { echo "D06_STATIC_BLOCKED_FILE_MISSING=$p";return 2; }
  done
  bash -n "$SIDECAR"
  /usr/bin/python3 -m py_compile "$MONITOR" "$TRIAGE"
  [[ "$P4_PUBLIC_RELEASE_SHA" =~ ^[0-9a-f]{40}$ &&
     "$P4_OWNER_PRIVATE_SHA" =~ ^[0-9a-f]{40}$ &&
     "$P4_OWNER_PRIVATE_TREE" =~ ^[0-9a-f]{40}$ ]] || return 2
  echo "D06_OWNER_RVIZ_STATIC_PASS private_p4_g07_sha=$P4_OWNER_PRIVATE_SHA GAZEBO_NOT_RUN RVIZ_NOT_RUN"
}
if [[ "$#" -eq 1 && "$1" == --self-check ]];then
  self_check;exit $?
fi
[[ "$#" -eq 0 ]] || { echo 'D06_USAGE --self-check or no arguments' >&2;exit 2; }
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'D06_BLOCKED_REAL_OWNER_INTERACTIVE_TTY_REQUIRED' >&2;exit 2;
}
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || {
  echo 'D06_BLOCKED_UBUNTU_24_04_REQUIRED';exit 2;
}
grep -qiE '(microsoft|wsl)' /proc/sys/kernel/osrelease || {
  echo 'D06_BLOCKED_WSL2_REQUIRED';exit 2;
}
[[ -f /opt/ros/jazzy/setup.bash && -n "${DISPLAY:-}" ]] || {
  echo 'D06_BLOCKED_ROS_JAZZY_OR_WSLG_DISPLAY_MISSING';exit 2;
}
for c in git gh bash ros2 gz colcon setsid timeout python3;do
  command -v "$c" >/dev/null || { echo "D06_BLOCKED_MISSING_CMD=$c";exit 2; }
done
gh auth status >/dev/null 2>&1 || {
  echo 'D06_BLOCKED_GITHUB_PRIVATE_AUTH';exit 2;
}
set +u
source /opt/ros/jazzy/setup.bash
set -u
if ! command -v rviz2 >/dev/null 2>&1;then
  echo 'D06_INSTALL_OFFICIAL_RVIZ_ONLY'
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    ros-jazzy-rviz2 ros-jazzy-visualization-msgs ros-jazzy-nav-msgs ros-jazzy-nav2-msgs
fi
for p in rviz2 visualization_msgs nav_msgs nav2_msgs;do
  ros2 pkg prefix "$p" >/dev/null || {
    echo "D06_BLOCKED_OFFICIAL_PACKAGE=$p";exit 2;
  }
done
self_check
OUT="$(mktemp -d "$HOME/axia_d06_gazebo_rviz_owner_XXXXXXXX")"
chmod 700 "$OUT"
CHECKOUT="$OUT/public_p4_release"
MARKER="$OUT/owner-start.marker"
SIDECAR_PID=''
OWNER_RC=125
cleanup() {
  rc=$?
  trap - EXIT INT TERM
  set +e
  if [[ "$SIDECAR_PID" =~ ^[0-9]+$ ]];then
    kill -TERM "$SIDECAR_PID" 2>/dev/null || true
    wait "$SIDECAR_PID" 2>/dev/null || true
  fi
  # Only the newly created public checkout is removed, never Original Owner RAW.
  if [[ -d "$CHECKOUT" ]];then rm -rf -- "$CHECKOUT";fi
  mapfile -d '' -t runs < <(
    find "$HOME/axia_p2_private_evidence" -mindepth 2 -maxdepth 2 \
      -type f -name summary.json -newer "$MARKER" -print0 2>/dev/null
  )
  if (( ${#runs[@]} == 1 ));then
    owner_root="$(dirname "${runs[0]}")"
    echo "D06_G07_OWNER_ORIGINAL=$owner_root"
    if [[ -f "$owner_root/source.sha" &&
          "$(cat "$owner_root/source.sha")" == "$P4_OWNER_PRIVATE_SHA" ]];then
      /usr/bin/python3 -u "$TRIAGE" \
        --live-result "$owner_root/G07/live/ci_moving_goal_result.json" \
        --output "$OUT/first_failure_triage.json" \
        > "$OUT/first_failure_triage.log" 2>&1 || true
      cat "$OUT/first_failure_triage.log" 2>/dev/null || true
    else
      echo 'D06_G07_POSTRUN_TRIAGE_SOURCE_MISMATCH_OR_MISSING'
      if [[ "$rc" == 0 ]];then rc=3;fi
    fi
  else
    echo "D06_G07_POSTRUN_TRIAGE_RUN_AMBIGUOUS count=${#runs[@]}"
    if [[ "$rc" == 0 ]];then rc=3;fi
  fi
  if grep -Fq 'D06_RVIZ_STARTED' "$OUT/sidecar.log" 2>/dev/null;then
    echo 'D06_RVIZ_PROCESS_STARTED WSLG_VISUAL_CONFIRMATION_NOT_AUTOMATED'
  else
    echo 'D06_RVIZ_NOT_CONFIRMED'
    if [[ "$rc" == 0 ]];then rc=3;fi
  fi
  if grep -Fq 'D06_RVIZ_SIDECAR_EXITED_BEFORE_OWNER_COMPLETION' \
       "$OUT/sidecar.log" 2>/dev/null;then
    echo 'D06_RVIZ_EARLY_EXIT_BLOCKED'
    if [[ "$rc" == 0 ]];then rc=3;fi
  fi
  echo 'D06_RVIZ_DIAGNOSTICS (exact original sidecar log follows):'
  tail -n 35 "$OUT/sidecar.log" 2>/dev/null || true
  (cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 |
    sort -z | xargs -0 -r sha256sum > SHA256SUMS)
  echo "D06_GUI_EVIDENCE=$OUT"
  echo "D06_GUI_OWNER_WRAPPER_RC=$rc P4_G11_OWNER_RC=$OWNER_RC"
  echo 'D06_GAZEBO_GUI_NOT_YET_VERIFIED: static/ROS L1 is not actual WSLg or full safety PASS'
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir -p "$CHECKOUT"
git -C "$CHECKOUT" init -q
git -C "$CHECKOUT" remote add origin \
  https://github.com/silverbjin/axia-robot-safety-ci-public.git
git -C "$CHECKOUT" fetch -q --depth 1 origin "$P4_PUBLIC_RELEASE_SHA"
git -C "$CHECKOUT" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$CHECKOUT" rev-parse HEAD)" == "$P4_PUBLIC_RELEASE_SHA" ]] || {
  echo 'D06_BLOCKED_P4_PUBLIC_SHA_MISMATCH';exit 2;
}
RELEASE="$CHECKOUT/$P4_G11_SCRIPT"
[[ -f "$RELEASE" ]] && bash -n "$RELEASE" || {
  echo 'D06_BLOCKED_P4_G11_RELEASE_MISSING_OR_INVALID';exit 2;
}
grep -Fq "$P4_OWNER_PRIVATE_SHA" "$RELEASE" &&
grep -Fq "$P4_OWNER_PRIVATE_TREE" "$RELEASE" || {
  echo 'D06_BLOCKED_P4_PRIVATE_PIN_OR_TREE_MISMATCH';exit 2;
}
touch "$MARKER"
bash "$SIDECAR" "$MARKER" "$OUT" "$P4_OWNER_PRIVATE_SHA" \
  > "$OUT/sidecar.log" 2>&1 & SIDECAR_PID=$!
echo 'D06_G07_P4_OWNER_REUSE_G11_RMW_SOURCE_PROVENANCE NO_SAFETY_RUNTIME_MODIFICATION'
echo 'SIMULATION ONLY. A single moving Goal requires manual YES-P2-G07-GOAL.'
echo 'RViz educational read-only display; NOT actual CollisionMonitorState or E-Stop.'
echo 'Safety TTL 150ms unchanged. Any first Guard latch stops the trial.'
# This release (not this D06 wrapper) owns the ONLY actual Owner Goal.
# The current G11 release writes raw custody and first RMW publication diagnostics
# even when G07 BLOCKED. It never uploads private originals to PUBLIC CI.
if bash "$RELEASE";then
  OWNER_RC=0
else
  OWNER_RC=$?
fi
if (( OWNER_RC != 0 ));then exit "$OWNER_RC";fi
