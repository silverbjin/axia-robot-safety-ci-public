#!/usr/bin/env bash
# AXIA D3 v2 one-time setup from a clean WSL2 Ubuntu 24.04 shell.
# Does NOT start Gazebo, send goals, request faults, change main or overwrite local edits.
set -Eeuo pipefail
REPO='silverbjin/axia-robot-safety-instructor'
BRANCH='feat/d3-intrusion-scan-stop-demo-20261108'
WORK="$HOME/axia_d3_classroom"
ROOT="$WORK/axia-d3-instructor"
if [[ "$(uname -s)" != Linux ]] || ! grep -qi microsoft /proc/version; then
  echo '[BLOCKED] Run inside Ubuntu 24.04 WSL2, not Windows CMD/PowerShell' >&2; exit 2
fi
source /etc/os-release
if [[ "${ID:-}" != ubuntu || "${VERSION_ID:-}" != 24.04 ]]; then
  echo '[BLOCKED] Ubuntu 24.04 required' >&2; exit 2
fi
for cmd in git gh python3 colcon; do
  command -v "$cmd" >/dev/null || { echo "[BLOCKED] Missing: $cmd" >&2; exit 2; }
done
[[ -f /opt/ros/jazzy/setup.bash ]] || { echo '[BLOCKED] ROS2 Jazzy missing' >&2; exit 2; }
source /opt/ros/jazzy/setup.bash
for cmd in ros2 gz; do
  command -v "$cmd" >/dev/null || { echo "[BLOCKED] Missing after Jazzy source: $cmd" >&2; exit 2; }
done
gh auth status >/dev/null || { echo '[BLOCKED] GitHub private repository auth required: gh auth login' >&2; exit 2; }
mkdir -p "$WORK"
if [[ ! -e "$ROOT" ]]; then
  gh repo clone "$REPO" "$ROOT" -- --branch feat/d3-intrusion-scan-stop-demo-20261108 --single-branch
else
  [[ -d "$ROOT/.git" ]] || { echo '[BLOCKED] Existing path is not Git checkout' >&2; exit 2; }
  [[ "$(git -C "$ROOT" branch --show-current)" == "$BRANCH" ]] || { echo '[BLOCKED] Existing checkout on wrong branch'; exit 2; }
  [[ -z "$(git -C "$ROOT" status --porcelain)" ]] || { echo '[BLOCKED] Uncommitted local changes: preserve them first'; exit 2; }
  git -C "$ROOT" fetch origin "$BRANCH"
  git -C "$ROOT" merge --ff-only "origin/$BRANCH"
fi
cd "$ROOT"
echo "[SOURCE] branch=$(git branch --show-current) commit=$(git rev-parse HEAD)"
for package in nav2_bringup nav2_minimal_tb3_sim ros_gz_sim; do
  ros2 pkg prefix "$package" >/dev/null || { echo "[BLOCKED] Missing $package" >&2; exit 2; }
done
colcon build --base-paths ros2_ws/src --symlink-install \
  --packages-select axia_safety_supervisor axia_fault_injector \
  axia_scenario_verifier axia_d3_demo
source install/setup.bash
ros2 pkg prefix axia_d3_demo
ros2 pkg executables axia_d3_demo
bash training/d03/d3_demo/scripts/d3_session.sh --init
source "$WORK/d3_session.env"
bash training/d03/d3_demo/scripts/run_d3_instructor.sh --preflight
printf '%s\n' '[READY] D3_V2_SOURCE_BUILD_SESSION_PREFLIGHT'
printf '%s\n' '[NEXT] Terminal A: bash training/d03/d3_demo/scripts/run_d3_instructor.sh --launch'
printf '%s\n' '[NEXT] Terminal B: gz service -l | grep "/world/.*/set_pose"'
printf '%s\n' '[NEXT] Terminal B: bash training/d03/d3_demo/scripts/d3_route.sh WORLD START_X START_Y END_X END_Y'
printf '%s\n' '[NEXT] Terminal B: bash training/d03/d3_demo/scripts/run_d3_preview.sh'
printf '%s\n' '[NEXT] After P1 approved navigation: bash training/d03/d3_demo/scripts/run_d3_live_scene.sh'
printf '%s\n' '[SCOPE] Gazebo launch/moving model/P1 stop NOT_RUN by this prepare script.'