#!/usr/bin/env bash
# AXIA D06 instructor WSL2 — official Nav2 Collision Monitor, isolated test topics.
# This tests ROS command transformation, NOT Gazebo motion or certified E-Stop.
set -Eeuo pipefail
umask 077
PUBLIC_SOURCE_SHA="d045e245b0faee6ad88f78e7a9878207b494b6f2"
REPO="https://github.com/silverbjin/axia-robot-safety-ci-public.git"
if [[ "${1:-}" == "--self-check" ]]; then
  [[ "$PUBLIC_SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]]
  echo "D06_WSL2_WRAPPER_STATIC_PASS; ROS_AND_GAZEBO_NOT_RUN"
  exit 0
fi
[[ $# -eq 0 ]] || { echo "BLOCKED: unsupported arguments"; exit 2; }
source /etc/os-release
[[ "$ID" == "ubuntu" && "$VERSION_ID" == "24.04" ]] || {
  echo "BLOCKED: Ubuntu 24.04 is required"; exit 2; }
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo "BLOCKED: this owner wrapper is WSL2 only"; exit 2; }
[[ -f /opt/ros/jazzy/setup.bash ]] || {
  echo "BLOCKED: ROS2 Jazzy not installed"; exit 2; }
for exe in git python3 ros2 sha256sum tar timeout; do
  command -v "$exe" >/dev/null || { echo "BLOCKED: missing $exe"; exit 2; }
done
BASE="$HOME/axia_d06_evidence"
mkdir -p "$BASE"
chmod 700 "$BASE"
OUT="$(mktemp -d "$BASE/d06-owner-XXXXXXXX")"
SRC="$(mktemp -d "$BASE/checkout-XXXXXXXX")"
STATUS="BLOCKED"
RC_GATE=125
finish() {
  rc="$?"
  trap - EXIT INT TERM
  set +e
  cd "$HOME" || cd /
  python3 - "$OUT/owner_summary.json" "$STATUS" "$RC_GATE" "$rc" "$PUBLIC_SOURCE_SHA" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({
  "status":sys.argv[2],"gate_rc":int(sys.argv[3]),"wrapper_rc":int(sys.argv[4]),
  "tested_public_source_sha":sys.argv[5],"actual_wsl2":True,
  "gazebo_actual":False,"p1_executed":False,
  "cmd_vel_published":False,"certified_estop":False
},indent=2)+"\n")
PY
  if [[ "$SRC" == "$BASE"/checkout-* ]]; then rm -rf -- "$SRC"; fi
  (cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 |
     sort -z | xargs -0 -r sha256sum > SHA256SUMS)
  tar -czf "$OUT.tar.gz" -C "$BASE" "$(basename "$OUT")"
  sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256"
  echo "D06_OWNER_STATUS=$STATUS"
  echo "GATE_RC=$RC_GATE WRAPPER_RC=$rc"
  echo "EVIDENCE=$OUT"
  echo "ARCHIVE=$OUT.tar.gz"
  echo "G7_GAZEBO_NOT_RUN=true CERTIFIED_ESTOP=false"
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
echo "[D06] Fetching pinned official CM test fixture source"
git -C "$SRC" init -q
git -C "$SRC" remote add origin "$REPO"
git -C "$SRC" fetch --quiet --depth 1 origin "$PUBLIC_SOURCE_SHA" > "$OUT/git_fetch.log" 2>&1
git -C "$SRC" checkout -q --detach FETCH_HEAD
test "$(git -C "$SRC" rev-parse HEAD)" = "$PUBLIC_SOURCE_SHA"
set +u
source /opt/ros/jazzy/setup.bash
set -u
if ! ros2 pkg prefix nav2_collision_monitor >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
      ros-jazzy-nav2-collision-monitor ros-jazzy-nav2-msgs \
      ros-jazzy-rclpy ros-jazzy-geometry-msgs ros-jazzy-sensor-msgs \
      ros-jazzy-ros2lifecycle
fi
echo "[D06] Running isolated ROS test (no /cmd_vel publication)"
cd "$SRC"
if timeout --signal=TERM --kill-after=20s 150s \
    python3 -u d06/scripts/d06_cm_live_gate.py \
      --params d06/params/collision_monitor_d06.yaml \
      --out "$OUT/live" 2>&1 | tee "$OUT/runtime.log"; then
  RC_GATE=0
else
  RC_GATE=$?
  echo "D06_OWNER_ROS_TEST_BLOCKED rc=$RC_GATE"
  exit 2
fi
python3 - "$OUT/live/verdict.json" <<'PY'
from pathlib import Path
import json,sys
v=json.loads(Path(sys.argv[1]).read_text())
assert v["status"]=="PASS_OFFICIAL_JAZZY_CM_CLEAR_SLOWDOWN_STOP"
assert v["ros_actual"] is True and v["gazebo_actual"] is False
assert v["graph"]["final_test_output_publishers"]==1
assert v["graph"]["robot_cmd_publishers"]==0
assert [s["expected_action"] for s in v["stages"]]==["CLEAR","SLOWDOWN","STOP"]
assert [s["status"] for s in v["stages"]]==["PASS"]*3
assert v["certified_estop"] is False
print("D06_OWNER_OFFICIAL_CM_L1_PASS")
PY
STATUS="PASS_OFFICIAL_JAZZY_CM_CLEAR_SLOWDOWN_STOP"
