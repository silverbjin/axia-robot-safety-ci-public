#!/usr/bin/env bash
# D06 Owner WSL2: original G07 Gazebo GUI + RViz observer. SIM ONLY.
# No automatic Goal, controller, Guard, Collision Monitor, or TTL modifications.
set -Eeuo pipefail
umask 077
readonly OWNER_REPO='silverbjin/axia-robot-safety-instructor'
readonly OWNER_SHA='eb984b73138e592caa67426eed9c60dde2ca2ebd'
PUBLIC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
SIDECAR="$PUBLIC_ROOT/d06/scripts/d06_rviz_sidecar.sh"
MONITOR="$PUBLIC_ROOT/d06/live/d06_readonly_monitor.py"
RVIZ_CONFIG="$PUBLIC_ROOT/d06/rviz/d06_safety_bubble.rviz"
self_check() {
  for path in "$SIDECAR" "$MONITOR" "$RVIZ_CONFIG";do
    [[ -s "$path" ]] || { echo "D06_STATIC_BLOCKED_FILE_MISSING=$path";exit 2; }
  done
  bash -n "$SIDECAR"
  /usr/bin/python3 -m py_compile "$MONITOR"
  [[ "$OWNER_SHA" =~ ^[0-9a-f]{40}$ ]]
  echo "D06_OWNER_RVIZ_STATIC_PASS private_g07_sha=$OWNER_SHA GAZEBO_NOT_RUN RVIZ_NOT_RUN"
}
if [[ "${1:-}" == '--self-check' ]];then
  [[ $# == 1 ]] || exit 2
  self_check
  exit 0
fi
[[ $# == 0 ]] || { echo 'D06_USAGE --self-check or no arguments';exit 2; }
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'D06_BLOCKED: real Owner interactive TTY is required';exit 2;
}
[[ -n "${DISPLAY:-}" ]] || { echo 'D06_BLOCKED: WSLg DISPLAY missing';exit 2; }
[[ -z "${VIRTUAL_ENV:-}" ]] || { echo 'D06_BLOCKED: deactivate Python venv';exit 2; }
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || {
  echo 'D06_BLOCKED: Ubuntu 24.04 required';exit 2;
}
grep -qiE 'wsl|microsoft' /proc/sys/kernel/osrelease || {
  echo 'D06_BLOCKED: WSL2 required';exit 2;
}
[[ -r /opt/ros/jazzy/setup.bash ]] || {
  echo 'D06_BLOCKED: ROS 2 Jazzy missing';exit 2;
}
for cmd in bash gh git setsid ros2 gz colcon timeout sha256sum python3;do
  command -v "$cmd" >/dev/null || { echo "D06_BLOCKED_MISSING_CMD=$cmd";exit 2; }
done
set +u
source /opt/ros/jazzy/setup.bash
set -u
if ! command -v rviz2 >/dev/null 2>&1;then
  echo 'D06_INSTALL_OFFICIAL_RVIZ_ONLY'
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    ros-jazzy-rviz2 ros-jazzy-visualization-msgs ros-jazzy-nav-msgs ros-jazzy-nav2-msgs
fi
for pkg in rviz2 visualization_msgs nav_msgs nav2_msgs;do
  ros2 pkg prefix "$pkg" >/dev/null 2>&1 || {
    echo "D06_BLOCKED_MISSING_ROS_PACKAGE=$pkg";exit 2;
  }
done
self_check
gh auth status >/dev/null 2>&1 || {
  echo 'D06_BLOCKED: gh auth login required for private instructor';exit 2;
}
OUT="$(mktemp -d "$HOME/axia_d06_gazebo_rviz_owner_XXXXXXXX")"
chmod 700 "$OUT"
CHECKOUT="$OUT/source"
SIDECAR_PID=''
finish() {
  rc=$?
  trap - EXIT INT TERM
  set +e
  if [[ "$SIDECAR_PID" =~ ^[0-9]+$ ]];then
    kill -TERM "$SIDECAR_PID" 2>/dev/null || true
    wait "$SIDECAR_PID" 2>/dev/null || true
  fi
  # Never remove original G07 Owner raw evidence; only ephemeral source copy.
  [[ ! -d "$CHECKOUT" ]] || rm -rf -- "$CHECKOUT"
  (cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 |
    sort -z | xargs -0 -r sha256sum > SHA256SUMS)
  echo "D06_GUI_EVIDENCE=$OUT"
  if grep -Fq D06_RVIZ_STARTED "$OUT/sidecar.log" 2>/dev/null;then
    echo 'D06_RVIZ_PROCESS_START_OBSERVED; WSLG_VISUAL_CONFIRMATION_NOT_AUTOMATED'
  else
    echo 'D06_RVIZ_NOT_CONFIRMED; inspect sidecar.log'
    if [[ "$rc" == 0 ]];then rc=3;fi
  fi
  if grep -Fq D06_RVIZ_SIDECAR_EXITED_BEFORE_OWNER_COMPLETION \
      "$OUT/sidecar.log" 2>/dev/null;then
    echo 'D06_RVIZ_EARLY_EXIT_BLOCKED; original safety result retained separately'
    if [[ "$rc" == 0 ]];then rc=3;fi
  fi
  echo "D06_GUI_OWNER_WRAPPER_RC=$rc"
  echo 'D06_GAZEBO_GUI_NOT_YET_VERIFIED: original G07 numerical result is not GUI acceptance'
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir -p "$CHECKOUT"
# Private exact-SHA checkout: no teacher reference or Hidden Test is uploaded.
gh repo clone "$OWNER_REPO" "$CHECKOUT" -- --no-checkout --filter=blob:none >/dev/null
git -C "$CHECKOUT" fetch -q --depth 1 origin "$OWNER_SHA"
git -C "$CHECKOUT" checkout -q --detach "$OWNER_SHA"
[[ "$(git -C "$CHECKOUT" rev-parse HEAD)" == "$OWNER_SHA" ]] || {
  echo 'D06_BLOCKED_PRIVATE_SOURCE_PIN_MISMATCH';exit 2;
}
[[ -z "$(git -C "$CHECKOUT" status --porcelain)" ]] || {
  echo 'D06_BLOCKED_PRIVATE_CHECKOUT_DIRTY';exit 2;
}
bash -n "$CHECKOUT/scripts/p2_owner_l3_wsl2.sh"
MARKER="$OUT/started.marker"
touch "$MARKER"
bash "$SIDECAR" "$MARKER" "$OUT" "$OWNER_SHA" > "$OUT/sidecar.log" 2>&1 &
SIDECAR_PID=$!
export AXIA_P2_OWNER_PINNED_SHA="$OWNER_SHA"
echo '============================================================'
echo 'D06 Gazebo GUI + RViz2 — official Waffle; physical G07 obstacle; ONE Goal'
echo 'Original G07 Owner manually requests YES-P2-G07-GOAL from your TTY.'
echo 'RViz shows /scan /odom TF and educational 0.4/0.75m rings, NOT CM verdict.'
echo 'No new safety code, no automatic Goal, no certified E-Stop.'
echo '============================================================'
# DO NOT pipe stdout through tee: Owner requires an actual stdout TTY.
# DO NOT type or fake YES-P2-G07-GOAL automatically.
bash "$CHECKOUT/scripts/p2_owner_l3_wsl2.sh" --case G07 --mvp-relocated-obstacle
