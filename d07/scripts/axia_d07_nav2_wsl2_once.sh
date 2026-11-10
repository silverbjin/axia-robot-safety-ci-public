#!/usr/bin/env bash
# AXIA D07 instructor WSL2 one-shot official Nav2 planner Costmap acceptance.
# ROS L1 ONLY; no Gazebo physical motion, no NavigateToPose and no /cmd_vel.
set -Eeuo pipefail
umask 077
SOURCE_SHA="158b7c6032d987177d1e1302bf85fd741120fd9e"
REPO_URL="https://github.com/silverbjin/axia-robot-safety-ci-public.git"
if [[ "${1:-}" == "--self-check" ]]; then
  [[ "$SOURCE_SHA" =~ ^[a-f0-9]{40}$ ]] || exit 2
  echo "D07_WSL2_WRAPPER_STATIC_OK; NAV2_AND_GAZEBO_NOT_RUN"
  exit 0
fi
[[ $# -eq 0 ]] || { echo "BLOCKED: unexpected args"; exit 2; }
source /etc/os-release
[[ "$ID" == "ubuntu" && "$VERSION_ID" == "24.04" ]] || {
  echo "BLOCKED: Ubuntu 24.04 required";exit 2; }
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo "BLOCKED: WSL2 required";exit 2; }
[[ -f /opt/ros/jazzy/setup.bash ]] || {
  echo "BLOCKED: ROS 2 Jazzy missing";exit 2; }
for x in git python3 ros2 curl tar sha256sum timeout; do
  command -v "$x" >/dev/null || { echo "BLOCKED: missing $x";exit 2; }
done

BASE="$HOME/axia_d07_evidence"
mkdir -p "$BASE";chmod 700 "$BASE"
OUT="$(mktemp -d "$BASE/d07-owner-XXXXXXXX")"
SRC="$(mktemp -d "$BASE/d07-source-XXXXXXXX")"
STATUS="BLOCKED";GATE_RC=125
finish() {
  rc="$?"
  trap - EXIT INT TERM
  set +e
  cd "$HOME" || cd /
  python3 - "$OUT/owner_summary.json" "$STATUS" "$GATE_RC" "$rc" "$SOURCE_SHA" <<'PY'
import sys,json
from pathlib import Path
p,status,gate,wrapper,sha=sys.argv[1:]
Path(p).write_text(json.dumps({
 "status":status,"gate_rc":int(gate),"wrapper_rc":int(wrapper),
 "tested_source_sha":sha,"owner_wsl2_actual":True,"gazebo_actual":False,
 "navigate_to_pose_sent":False,"cmd_vel_published":False,
 "certified_estop":False},indent=2)+"\n")
PY
  if [[ "$SRC" == "$BASE"/d07-source-* ]];then rm -rf -- "$SRC";fi
  (cd "$OUT";find . -type f ! -name SHA256SUMS -print0 |sort -z|
   xargs -0 -r sha256sum > SHA256SUMS)
  tar -czf "$OUT.tar.gz" -C "$BASE" "$(basename "$OUT")"
  sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256"
  echo "D07_OWNER_STATUS=$STATUS"
  echo "GATE_RC=$GATE_RC WRAPPER_RC=$rc"
  echo "EVIDENCE=$OUT"
  echo "ARCHIVE=$OUT.tar.gz"
  echo "GAZEBO_PHYSICS_NOT_RUN=true CERTIFIED_ESTOP=false"
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "[D07] Fetch pinned official Nav2 replanning test source $SOURCE_SHA"
git -C "$SRC" init -q
git -C "$SRC" remote add origin "$REPO_URL"
git -C "$SRC" fetch --quiet --depth 1 origin "$SOURCE_SHA" > "$OUT/git_fetch.log" 2>&1
git -C "$SRC" checkout -q --detach FETCH_HEAD
test "$(git -C "$SRC" rev-parse HEAD)" = "$SOURCE_SHA"
set +u
source /opt/ros/jazzy/setup.bash
set -u
MISSING=0
for pkg in nav2_planner nav2_navfn_planner nav2_costmap_2d nav2_msgs tf2_ros;do
  ros2 pkg prefix "$pkg" >/dev/null 2>&1 || MISSING=1
done
if [[ "$MISSING" -eq 1 ]];then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    ros-jazzy-nav2-planner ros-jazzy-nav2-navfn-planner \
    ros-jazzy-nav2-costmap-2d ros-jazzy-nav2-msgs \
    ros-jazzy-tf2-ros ros-jazzy-rclpy ros-jazzy-nav-msgs \
    ros-jazzy-geometry-msgs ros-jazzy-sensor-msgs \
    ros-jazzy-action-msgs ros-jazzy-ros2lifecycle
fi
echo "[D07] Launch official PlannerServer; synthetic scan -> actual Costmap -> ComputePathToPose"
cd "$SRC"
if timeout --signal=TERM --kill-after=20s 170s \
   python3 -u d07/scripts/d07_nav2_planner_l1.py \
     --params d07/params/nav2_d07_planner.yaml \
     --out "$OUT/live" 2>&1 | tee "$OUT/runtime.log";then
  GATE_RC=0
else
  GATE_RC="$?"
  echo "D07_OWNER_BLOCKED: actual ROS L1 gate failed rc=$GATE_RC"
  exit 2
fi
python3 - "$OUT/live/verdict.json" <<'PY'
import json,sys
from pathlib import Path
v=json.loads(Path(sys.argv[1]).read_text())
assert v["status"]=="PASS_OFFICIAL_NAV2_COSTMAP_REPLAN_L1"
assert v["ros_actual"] is True and v["gazebo_actual"] is False
assert v["graph"]["actual_nav2_costmap_publishers"]==1
assert v["graph"]["actual_nav2_scan_subscribers"]==1
assert v["graph"]["actual_robot_cmd_publishers"]==0
a,b,c=(v["stages"][name] for name in ("clear_before","person_blocking","person_cleared"))
assert a["grid"]["actual_obstacle_lethal_cells"]<=2
assert b["grid"]["actual_obstacle_lethal_cells"]>=3
assert b["route"]["min_distance_to_person_proxy_m"]>=0.30
assert c["grid"]["actual_obstacle_lethal_cells"]<=2
assert all(x["route"]["status"]=="SUCCEEDED" for x in (a,b,c))
assert v["cmd_vel_published"] is False and v["certified_estop"] is False
print("D07_OWNER_OFFICIAL_NAV2_L1_PASS")
PY
STATUS="PASS_OFFICIAL_NAV2_COSTMAP_REPLAN_L1"
