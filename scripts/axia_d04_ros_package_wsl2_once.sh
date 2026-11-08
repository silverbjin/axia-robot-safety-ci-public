#!/usr/bin/env bash
# D04 owner-only package acceptance. Existing P1 / yolo code never modified.
set -Eeuo pipefail
umask 077
PUBLIC_SHA="${AXIA_D04_PUBLIC_SHA:-}"
PRIVATE_SHA="c1b92d9dd3dd2cd038db16253102542d120ea87e"
P1_REPO="silverbjin/axia-robot-safety-instructor"
P1_BRANCH="feature/d04-yolo-ros-package-20261109"
CI_REPO="silverbjin/axia-robot-safety-ci-public"
CI_BRANCH="feature/d04-yolo-ros-package-20261109"
YOLO_SHA="94d2dd500cb26027ee9c019f4d3a02029ac615cc"
ONNX_SHA="4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf"
DAE_SHA="49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e"

if [[ "${1:-}" == "--self-check" ]]; then
  [[ "$PRIVATE_SHA" =~ ^[0-9a-f]{40}$ && "$YOLO_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
  echo "AXIA_D04_PACKAGE_WRAPPER_STATIC_OK G_D04_PACKAGE_RUNTIME=NOT_RUN"
  exit 0
fi
[[ $# -eq 0 && "$PUBLIC_SHA" =~ ^[0-9a-f]{40}$ ]] || {
  echo "BLOCKED: set AXIA_D04_PUBLIC_SHA to an exact reviewed commit"; exit 2; }
[[ -f /etc/os-release ]] || exit 2
source /etc/os-release
[[ "$ID" == "ubuntu" && "$VERSION_ID" == "24.04" ]] || {
  echo "BLOCKED: Ubuntu 24.04 required"; exit 2; }
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo "BLOCKED: WSL2 required"; exit 2; }
[[ -f /opt/ros/jazzy/setup.bash ]] || {
  echo "BLOCKED: ROS2 Jazzy required"; exit 2; }
set +u
source /opt/ros/jazzy/setup.bash
set -u
for cmd in gh git curl colcon ros2 gz python3 sha256sum timeout tar; do
  command -v "$cmd" >/dev/null || { echo "BLOCKED: missing $cmd"; exit 2; }
done
gh auth status >/dev/null 2>&1 || { echo "BLOCKED: gh private instructor authentication required"; exit 2; }

CACHE="$HOME/.cache/axia/d04"
BASE="$HOME/axia_d04_evidence"
mkdir -p "$CACHE" "$BASE"
chmod 700 "$CACHE" "$BASE"
OUT="$(mktemp -d "$BASE/d04-package-XXXXXXXX")"
SRC="$(mktemp -d "$CACHE/d04-package-source-XXXXXXXX")"
STATUS="BLOCKED"
GATE_RC=125
finish() {
  rc=$?
  trap - EXIT INT TERM
  set +e
  cd "$HOME" || cd /
  python3 - "$OUT/owner_summary.json" "$STATUS" "$GATE_RC" "$rc" "$PUBLIC_SHA" "$PRIVATE_SHA" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({
  "status":sys.argv[2],"gate_exit":int(sys.argv[3]),
  "wrapper_exit":int(sys.argv[4]),"public_sha":sys.argv[5],
  "private_sha":sys.argv[6],"p1_g00_g04_accepted":False,
  "goal_sent":False,"fault_injected":False,"certified_estop":False
},indent=2)+"\n")
PY
  if [[ "$SRC" == "$CACHE"/d04-package-source-* ]]; then rm -rf -- "$SRC"; fi
  (cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 -r sha256sum > SHA256SUMS)
  tar -czf "$OUT.tar.gz" -C "$BASE" "$(basename "$OUT")"
  sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256"
  echo "D04_PACKAGE_STATUS=$STATUS"
  echo "GATE_RC=$GATE_RC"
  echo "EVIDENCE=$OUT"
  echo "ARCHIVE=$OUT.tar.gz"
  echo "P1_G00_G04_ACCEPTED=false CERTIFIED_ESTOP=false"
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "[D04][PREP] D04 packaged demo WSL2: public=$PUBLIC_SHA private=$PRIVATE_SHA"
echo "[D04][PREP] No Nav2 Goal/Fault/cmd_vel publication; visual human animation only"
gh repo clone "$CI_REPO" "$SRC/public" -- --single-branch --branch "$CI_BRANCH" --depth 1 > "$OUT/public_checkout.log" 2>&1 || exit 2
git -C "$SRC/public" fetch -q --depth 1 origin "$PUBLIC_SHA" >> "$OUT/public_checkout.log" 2>&1 || exit 2
git -C "$SRC/public" checkout -q --detach "$PUBLIC_SHA" || exit 2
[[ "$(git -C "$SRC/public" rev-parse HEAD)" == "$PUBLIC_SHA" ]] || exit 2

gh repo clone "$P1_REPO" "$SRC/instructor" -- --single-branch --branch "$P1_BRANCH" --depth 1 > "$OUT/private_checkout.log" 2>&1 || exit 2
git -C "$SRC/instructor" fetch -q --depth 1 origin "$PRIVATE_SHA" >> "$OUT/private_checkout.log" 2>&1 || exit 2
git -C "$SRC/instructor" checkout -q --detach "$PRIVATE_SHA" || exit 2
[[ "$(git -C "$SRC/instructor" rev-parse HEAD)" == "$PRIVATE_SHA" ]] || exit 2

# Reuse installed official stack, install only when missing. Do not touch P1 YAML.
MISSING=()
for pkg in nav2_bringup nav2_minimal_tb3_sim turtlebot3_gazebo ros_gz_image image_view; do
  ros2 pkg prefix "$pkg" >/dev/null 2>&1 || MISSING+=("$pkg")
done
if (( ${#MISSING[@]} > 0 )); then
  echo "Installing missing official ROS packages: ${MISSING[*]}"
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    ros-jazzy-nav2-bringup ros-jazzy-nav2-minimal-tb3-sim \
    ros-jazzy-turtlebot3-gazebo ros-jazzy-ros-gz ros-jazzy-image-view
fi
if ! python3 -c "import cv2; import rclpy" >/dev/null 2>&1; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-opencv ros-jazzy-rclpy
fi

echo "[D04][BUILD] Building D04/P1 packages; detailed logs: $OUT/package_build.log"
# Build the actual D04 ROS 2 package, not just the prior test runner.
D04_WS="$CACHE/d04_package_ws_$PRIVATE_SHA"
mkdir -p "$D04_WS"
(
  cd "$D04_WS"
  colcon build --base-paths "$SRC/instructor/ros2_ws/src" \
    --packages-select axia_d04_vision_demo axia_safety_supervisor axia_fault_injector axia_scenario_verifier \
    --executor sequential --event-handlers console_direct+
) > "$OUT/package_build.log" 2>&1 || {
  echo "BLOCKED: D04/P1 build"; tail -n 35 "$OUT/package_build.log"; exit 2; }

echo "[D04][BUILD] D04/P1 package build finished; verifying upstream yolo_ros engine"
YOLO_WS="$CACHE/yolo_ws_$YOLO_SHA"
if [[ ! -f "$YOLO_WS/install/setup.bash" ]]; then
  mkdir -p "$YOLO_WS/src"
  git clone -q https://github.com/mgonzs13/yolo_ros.git "$YOLO_WS/src/yolo_ros" || exit 2
  git -C "$YOLO_WS/src/yolo_ros" checkout -q --detach "$YOLO_SHA" || exit 2
  [[ "$(git -C "$YOLO_WS/src/yolo_ros" rev-parse HEAD)" == "$YOLO_SHA" ]] || exit 2
  (
    cd "$YOLO_WS"
    colcon build --merge-install --executor sequential --packages-up-to yolo_bringup \
      --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
      --event-handlers console_direct+
  ) > "$OUT/yolo_build.log" 2>&1 || {
    echo "BLOCKED: yolo_ros C++ build"; tail -n 30 "$OUT/yolo_build.log"; exit 2; }
fi

mkdir -p "$CACHE/assets"
MODEL="$CACHE/assets/yolo26n.onnx"
ACTOR="$CACHE/assets/walk.dae"
if [[ ! -f "$MODEL" ]] || ! echo "[D04][ASSETS] Confirming real ONNX weights and actor mesh SHA256"
echo "$ONNX_SHA  $MODEL" | sha256sum -c - >/dev/null; then
  curl -fL --retry 3 --max-time 160 \
    'https://huggingface.co/unileon-robotics/YOLO26-ONNX/resolve/main/yolo26n.onnx' \
    -o "$MODEL.tmp"
  mv "$MODEL.tmp" "$MODEL"
fi
if [[ ! -f "$ACTOR" ]] || ! echo "$DAE_SHA  $ACTOR" | sha256sum -c - >/dev/null; then
  curl -fL --retry 3 --max-time 160 \
    'https://fuel.gazebosim.org/1.0/Mingfei/models/actor/tip/files/meshes/walk.dae' \
    -o "$ACTOR.tmp"
  mv "$ACTOR.tmp" "$ACTOR"
fi
echo "$ONNX_SHA  $MODEL" | sha256sum -c -
echo "$DAE_SHA  $ACTOR" | sha256sum -c -

set +u
source "$YOLO_WS/install/setup.bash"
source "$D04_WS/install/setup.bash"
set -u
echo "[D04][LAUNCH_ARGS] Checking installed package launch --show-args (max 45s)"
ros2 pkg prefix axia_d04_vision_demo | tee "$OUT/package_prefix.txt"
timeout 45s ros2 launch axia_d04_vision_demo d04_p1_yolo.launch.py --show-args > "$OUT/launch_args.txt" 2>&1 || {
  echo "[D04][BLOCKED] launch --show-args failed"; tail -n 15 "$OUT/launch_args.txt"; exit 2; }
echo "[D04][LAUNCH_ARGS] PASS; starting actual Gazebo+YOLO integration now"

# default GUI when WSLg is present; user may set AXIA_D04_GUI=0.
GUI_ARGS=()
if [[ "${AXIA_D04_GUI:-1}" == "1" && -n "${DISPLAY:-}" ]]; then
  GUI_ARGS+=(--gui)
else
  echo "[D04][GUI] No WSLg DISPLAY or AXIA_D04_GUI=0; headless only. Review debug_frame.png after run."
fi

HOLD="${AXIA_D04_DEMO_HOLD_S:-90}"
[[ "$HOLD" =~ ^[0-9]{1,3}$ ]] || { echo "[D04][BLOCKED] invalid AXIA_D04_DEMO_HOLD_S"; exit 2; }
echo "[D04][LIVE] Starting P1/YOLO; GUI=${#GUI_ARGS[@]} preview-hold=${HOLD}s"
echo "[D04][LIVE] Real-time stage progress + saved detailed log: $OUT/runtime.log"
cd "$SRC/public"
if timeout --signal=TERM --kill-after=30s 640s \
  python3 -u scripts/d04_packaged_p1_yolo_gate.py \
  --instructor "$SRC/instructor" \
  --d04-private-sha "$PRIVATE_SHA" --model "$MODEL" --actor "$ACTOR" \
  --out "$OUT/live" --hold-seconds "$HOLD" "${GUI_ARGS[@]}" \
  2>&1 | tee "$OUT/runtime.log"; then
  GATE_RC=0
else
  GATE_RC=$?
  echo "BLOCKED: packaged ROS 2 runtime gate $GATE_RC"
  tail -n 45 "$OUT/runtime.log" || true
  exit 2
fi
python3 - "$OUT/live/verdict.json" <<'PY'
import json,sys
from pathlib import Path
v=json.loads(Path(sys.argv[1]).read_text())
assert v.get("status")=="PASS_P1_AND_YOLO_PACKAGE_RUNTIME"
assert v.get("graph_stable") is True
assert all(v.get(k) for k in ("person_valid","rgb_valid","debug_image_saved"))
assert v.get("goal_sent") is False and v.get("fault_injected") is False
print("AXIA_D04_PACKAGED_ROS2_P1_YOLO_ACTUAL_ACCEPTANCE_PASS")
PY
STATUS="PASS_PACKAGED_P1_YOLO"
echo "[D04][PASS] P1 graph unchanged and real person detected; evidence is under $OUT/live"
if [[ -n "${DISPLAY:-}" && -f "$OUT/live/debug_frame.png" ]] && command -v xdg-open >/dev/null; then
  xdg-open "$OUT/live/debug_frame.png" >/dev/null 2>&1 || true
fi
echo "D04_BBOX_IMAGE=$OUT/live/debug_frame.png"
