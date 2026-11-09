#!/usr/bin/env bash
# AXIA D05 — one-shot instructor WSL2 acceptance: real Gazebo RGBD + YOLO,
# private D05 read-only observer, sensor loss VALID -> UNKNOWN.
# This is a SIMULATION / NON-SAFETY-GRADED demo. No Nav2 Goal or E-Stop.
set -Eeuo pipefail
umask 077

CI_REPO="silverbjin/axia-robot-safety-ci-public"
INSTRUCTOR_REPO="silverbjin/axia-robot-safety-instructor"
PUBLIC_SHA="2dcd5f5cad091f9bd3e5fce71e0009d9e18d609d"
PRIVATE_SHA="e26069e3d2396e9d9ee89addfb6d7c07794ef6fb"
YOLO_SHA="94d2dd500cb26027ee9c019f4d3a02029ac615cc"
ONNX_SHA="4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf"
ACTOR_SHA="49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e"

if [[ "$#" -eq 1 && "$1" == "--self-check" ]]; then
  for sha in "$PUBLIC_SHA" "$PRIVATE_SHA" "$YOLO_SHA" "$ONNX_SHA" "$ACTOR_SHA"; do
    [[ "$sha" =~ ^[0-9a-f]{40,64}$ ]] || exit 2
  done
  echo "AXIA_D05_WSL2_WRAPPER_STATIC_OK; GAZEBO_NOT_RUN"
  exit 0
fi
[[ "$#" -eq 0 ]] || { echo "BLOCKED: no arguments expected (or --self-check)"; exit 2; }
[[ -f /etc/os-release ]] || { echo "BLOCKED: no /etc/os-release"; exit 2; }
source /etc/os-release
[[ "$ID" == "ubuntu" && "$VERSION_ID" == "24.04" ]] || {
  echo "BLOCKED: Ubuntu 24.04 required"; exit 2;
}
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo "BLOCKED: WSL2 is required"; exit 2;
}
[[ -f /opt/ros/jazzy/setup.bash ]] || {
  echo "BLOCKED: ROS 2 Jazzy not installed"; exit 2;
}
for cmd in gh git curl colcon ros2 gz python3 sha256sum timeout tar sudo; do
  command -v "$cmd" >/dev/null || { echo "BLOCKED: missing $cmd"; exit 2; }
done
gh auth status >/dev/null 2>&1 || {
  echo "BLOCKED: run 'gh auth login' in WSL2, with private instructor repo access";
  exit 2;
}
set +u
source /opt/ros/jazzy/setup.bash
set -u

CACHE="$HOME/.cache/axia/d05"
EVIDENCE_BASE="$HOME/axia_d05_evidence"
mkdir -p "$CACHE" "$EVIDENCE_BASE"
chmod 700 "$CACHE" "$EVIDENCE_BASE"
OUT="$(mktemp -d "$EVIDENCE_BASE/d05-owner-XXXXXXXX")"
SRC="$(mktemp -d "$CACHE/checkout-XXXXXXXX")"
GATE_RC=125
STATUS="BLOCKED"
finish() {
  rc="$?"
  trap - EXIT INT TERM
  set +e
  cd "$HOME" || cd /
  python3 - "$OUT/owner_summary.json" "$STATUS" "$GATE_RC" "$rc" "$PUBLIC_SHA" "$PRIVATE_SHA" <<'PY'
import json,sys
from pathlib import Path
path,status,gate_rc,wrapper_rc,public_sha,private_sha=sys.argv[1:]
Path(path).write_text(json.dumps({
 "status":status,"gate_exit_code":int(gate_rc),"wrapper_exit_code":int(wrapper_rc),
 "public_test_sha":public_sha,"private_runtime_sha":private_sha,
 "owner_wsl2_actual":True,"p1_goal_sent":False,"cmd_vel_published":False,
 "fault_injector_used":False,"certified_estop":False
},indent=2,ensure_ascii=False)+"\n")
PY
  if [[ "$SRC" == "$CACHE"/checkout-* ]]; then rm -rf -- "$SRC"; fi
  (
    cd "$OUT"
    find . -type f ! -name SHA256SUMS -print0 | sort -z |
      xargs -0 -r sha256sum > SHA256SUMS
  )
  tar -czf "$OUT.tar.gz" -C "$EVIDENCE_BASE" "$(basename "$OUT")"
  sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256"
  echo "===================================================="
  echo "D05_OWNER_STATUS=$STATUS"
  echo "GATE_RC=$GATE_RC WRAPPER_RC=$rc"
  echo "EVIDENCE=$OUT"
  echo "ARCHIVE=$OUT.tar.gz"
  echo "P1_GOAL_SENT=false CERTIFIED_ESTOP=false"
  echo "===================================================="
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "[D05][PREP] WSL2 local real Gazebo RGBD+YOLO read-only acceptance"
echo "[D05][PIN] public=$PUBLIC_SHA private=$PRIVATE_SHA upstream=$YOLO_SHA"
echo "[D05][NOTE] No robot motion, Nav2 Goal, cmd_vel, or certified HW E-Stop test"

# Pinned fetch: the tested public harness and private teacher D05 source.
gh repo clone "$CI_REPO" "$SRC/public" -- --no-checkout > "$OUT/public_checkout.log" 2>&1
git -C "$SRC/public" fetch --depth 1 origin "$PUBLIC_SHA" >> "$OUT/public_checkout.log" 2>&1
git -C "$SRC/public" checkout -q --detach "$PUBLIC_SHA"
test "$(git -C "$SRC/public" rev-parse HEAD)" = "$PUBLIC_SHA"
gh repo clone "$INSTRUCTOR_REPO" "$SRC/instructor" -- --no-checkout > "$OUT/instructor_checkout.log" 2>&1
git -C "$SRC/instructor" fetch --depth 1 origin "$PRIVATE_SHA" >> "$OUT/instructor_checkout.log" 2>&1
git -C "$SRC/instructor" checkout -q --detach "$PRIVATE_SHA"
test "$(git -C "$SRC/instructor" rev-parse HEAD)" = "$PRIVATE_SHA"

# Prefer the D04 tested local dependencies; apt installs only if missing.
MISSING=0
for pkg in turtlebot3_gazebo ros_gz_image ros_gz_bridge; do
  if ! ros2 pkg prefix "$pkg" >/dev/null 2>&1; then MISSING=1; fi
done
if ! python3 -c 'import cv2,numpy,rclpy,pytest' >/dev/null 2>&1; then MISSING=1; fi
if [[ "$MISSING" -eq 1 ]]; then
  echo "[D05][APT] Installing only missing Jazzy/Harmonic runtime dependencies"
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    python3-pytest python3-colcon-common-extensions \
    ros-jazzy-turtlebot3-gazebo ros-jazzy-ros-gz \
    ros-jazzy-rclpy ros-jazzy-sensor-msgs ros-jazzy-std-msgs \
    ros-jazzy-cv-bridge python3-opencv python3-numpy \
    libgl1-mesa-dri libglx-mesa0 xvfb xauth
fi
for cmd in xvfb-run cmake g++ pkg-config; do
  command -v "$cmd" >/dev/null || {
    echo "[D05][APT] installing C++/headless prerequisites"
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
      build-essential cmake pkg-config xvfb xauth libcurl4-openssl-dev \
      libopencv-dev ros-jazzy-pluginlib ros-jazzy-vision-msgs \
      ros-jazzy-message-filters ros-jazzy-tf2-ros
    break
  }
done

# Only essential local regression; main gate will use actual ROS messages.
echo "[D05][L0] Running pinned private contract tests"
(
  cd "$SRC/instructor"
  python3 -m pytest -q --tb=short \
    ros2_ws/src/axia_d05_depth_demo/test \
    training/block_B/tests training/block_B/instructor/hidden_tests
) > "$OUT/private_l0.log" 2>&1 || {
  tail -n 35 "$OUT/private_l0.log"; echo "[D05][BLOCKED] private L0"; exit 2;
}
tail -n 3 "$OUT/private_l0.log"

# Cache immutable versioned D05 install, not a working copy of the private source.
D05_WS="$CACHE/d05_ws_$PRIVATE_SHA"
if [[ ! -f "$D05_WS/install/setup.bash" ]]; then
  echo "[D05][L1] Building private Jazzy observer (source remains private)"
  mkdir -p "$D05_WS"
  (
    cd "$D05_WS"
    colcon build --base-paths "$SRC/instructor/ros2_ws/src" \
      --packages-select axia_d05_depth_demo --executor sequential \
      --event-handlers console_direct+
  ) > "$OUT/d05_build.log" 2>&1 || {
    tail -n 35 "$OUT/d05_build.log"; echo "[D05][BLOCKED] d05 build"; exit 2;
  }
else
  echo "[D05][L1] Reusing exact-SHA D05 build cache"
fi

# Reuse verified D04 upstream C++/ONNX build when available.
D04_YOLO_WS="$HOME/.cache/axia/d04/yolo_ws_$YOLO_SHA"
YOLO_WS="$CACHE/yolo_ws_$YOLO_SHA"
if [[ -f "$D04_YOLO_WS/install/setup.bash" ]] &&
   [[ -d "$D04_YOLO_WS/src/yolo_ros/.git" ]] &&
   [[ "$(git -C "$D04_YOLO_WS/src/yolo_ros" rev-parse HEAD)" == "$YOLO_SHA" ]]; then
  YOLO_WS="$D04_YOLO_WS"
  echo "[D05][YOLO] Reusing previously accepted D04 yolo_ros C++ build"
elif [[ ! -f "$YOLO_WS/install/setup.bash" ]]; then
  echo "[D05][YOLO] Building pinned MIT upstream YOLO once"
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    build-essential cmake pkg-config libcurl4-openssl-dev libopencv-dev \
    ros-jazzy-pluginlib ros-jazzy-vision-msgs ros-jazzy-message-filters ros-jazzy-tf2-ros
  mkdir -p "$YOLO_WS/src" "$CACHE/onnxruntime"
  git clone -q https://github.com/mgonzs13/yolo_ros.git "$YOLO_WS/src/yolo_ros"
  git -C "$YOLO_WS/src/yolo_ros" checkout -q --detach "$YOLO_SHA"
  test "$(git -C "$YOLO_WS/src/yolo_ros" rev-parse HEAD)" = "$YOLO_SHA"
  ORT="$CACHE/onnxruntime/onnxruntime-linux-x64-1.20.0.tgz"
  if [[ ! -s "$ORT" ]] || [[ "$(stat -c %s "$ORT")" != 6184676 ]] ||
      ! tar -tzf "$ORT" >/dev/null 2>&1; then
    curl --fail --location --retry 4 --retry-all-errors --retry-delay 2 \
      --connect-timeout 15 --max-time 130 \
      -o "$ORT.tmp" \
      'https://github.com/microsoft/onnxruntime/releases/download/v1.20.0/onnxruntime-linux-x64-1.20.0.tgz'
    test "$(stat -c %s "$ORT.tmp")" = 6184676
    tar -tzf "$ORT.tmp" >/dev/null
    mv -f "$ORT.tmp" "$ORT"
  fi
  ORT_ROOT="$CACHE/onnxruntime/onnxruntime-linux-x64-1.20.0"
  if [[ ! -s "$ORT_ROOT/lib/libonnxruntime.so" ]]; then
    tar -xzf "$ORT" -C "$CACHE/onnxruntime"
  fi
  test -s "$ORT_ROOT/lib/libonnxruntime.so"
  (
    cd "$YOLO_WS"
    colcon build --merge-install --executor sequential --packages-up-to yolo_bringup \
      --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
      "-DONNXRUNTIME_ROOT=$ORT_ROOT" \
      --event-handlers console_direct+
  ) > "$OUT/yolo_build.log" 2>&1 || {
    tail -n 40 "$OUT/yolo_build.log"; echo "[D05][BLOCKED] yolo_ros build"; exit 2;
  }
else
  echo "[D05][YOLO] Reusing exact-SHA D05 upstream C++ cache"
fi
test -f "$YOLO_WS/install/setup.bash"
set +u
source "$YOLO_WS/install/setup.bash"
source "$D05_WS/install/setup.bash"
set -u
ros2 pkg executables axia_d05_depth_demo | grep -F 'd05_range_observer'
ros2 pkg prefix yolo_bringup >/dev/null

# Local licensed assets are never copied into public source or evidence.
ASSET_DIR="$CACHE/assets"
mkdir -p "$ASSET_DIR"
chmod 700 "$ASSET_DIR"
MODEL="$ASSET_DIR/yolo26n.onnx"
ACTOR="$ASSET_DIR/walk.dae"
D04_ASSET_DIR="$HOME/.cache/axia/d04/assets"
if [[ ! -f "$MODEL" ]] && [[ -f "$D04_ASSET_DIR/yolo26n.onnx" ]] &&
   echo "$ONNX_SHA  $D04_ASSET_DIR/yolo26n.onnx" | sha256sum -c - >/dev/null 2>&1; then
  cp "$D04_ASSET_DIR/yolo26n.onnx" "$MODEL"
fi
if [[ ! -f "$ACTOR" ]] && [[ -f "$D04_ASSET_DIR/walk.dae" ]] &&
   echo "$ACTOR_SHA  $D04_ASSET_DIR/walk.dae" | sha256sum -c - >/dev/null 2>&1; then
  cp "$D04_ASSET_DIR/walk.dae" "$ACTOR"
fi
if [[ ! -f "$MODEL" ]] || ! echo "$ONNX_SHA  $MODEL" | sha256sum -c - >/dev/null 2>&1; then
  curl --fail --location --retry 3 --max-time 120 \
    -o "$MODEL.tmp" 'https://huggingface.co/unileon-robotics/YOLO26-ONNX/resolve/main/yolo26n.onnx'
  mv -f "$MODEL.tmp" "$MODEL"
fi
if [[ ! -f "$ACTOR" ]] || ! echo "$ACTOR_SHA  $ACTOR" | sha256sum -c - >/dev/null 2>&1; then
  curl --fail --location --retry 3 --max-time 120 \
    -o "$ACTOR.tmp" 'https://fuel.gazebosim.org/1.0/Mingfei/models/actor/tip/files/meshes/walk.dae'
  mv -f "$ACTOR.tmp" "$ACTOR"
fi
echo "$ONNX_SHA  $MODEL" | sha256sum -c -
echo "$ACTOR_SHA  $ACTOR" | sha256sum -c -
echo "[D05][ASSETS] Pinned assets OK. ONNX is AGPL-3.0, local evaluation only."

WAIT_S="$(printenv AXIA_D05_WAIT_S 2>/dev/null || printf '190')"
[[ "$WAIT_S" =~ ^[0-9]{2,3}$ ]] && (( WAIT_S >= 60 && WAIT_S <= 300 )) || {
  echo "BLOCKED: AXIA_D05_WAIT_S must be 60..300"; exit 2;
}
echo "[D05][LIVE] Real Gazebo RGB-D person, then Depth bridge loss -> UNKNOWN"
echo "[D05][DISPLAY] Xvfb is headless; saved PNG is opened after the run if WSLg is available"
cd "$SRC/public"
if timeout --signal=TERM --kill-after=25s 410s \
    python3 -u scripts/d05_real_rgbd_l2_gate.py \
      --model "$MODEL" --actor "$ACTOR" \
      --private-sha "$PRIVATE_SHA" --wait-s "$WAIT_S" \
      --out "$OUT/live" 2>&1 | tee "$OUT/runtime.log"; then
  GATE_RC=0
else
  GATE_RC="$?"
  echo "[D05][BLOCKED] actual L2 gate failed rc=$GATE_RC"
  tail -n 35 "$OUT/runtime.log" || true
  exit 2
fi

python3 - "$OUT/live/verdict.json" <<'PY'
import json,sys,math
from pathlib import Path
v=json.loads(Path(sys.argv[1]).read_text())
valid=v.get("valid_status") or {}
unknown=v.get("unknown_after_loss") or {}
assert v.get("status")=="PASS_REAL_GAZEBO_PERSON_RANGE_VALID_TO_UNKNOWN",v.get("blocker")
assert valid.get("status")=="VALID" and valid.get("safety_certified") is False
assert isinstance(valid.get("distance_m"),(int,float)) and math.isfinite(valid["distance_m"])
assert 1.0<valid["distance_m"]<4.0 and valid.get("valid_fraction",0)>=0.5
assert all(valid.get(key,0)>0 for key in ("frame_stamp_ns","depth_stamp_ns","detection_stamp_ns"))
assert unknown.get("status")=="UNKNOWN" and unknown.get("distance_m") is None
assert unknown.get("reason")=="STALE_INPUT"
assert v.get("rgb_continued_after_loss") is True
assert v.get("yolo_continued_after_loss") is True
assert v.get("goal_sent") is False and v.get("cmd_vel_published") is False
assert v.get("certified_estop") is False
print("AXIA_D05_WSL2_REAL_RGBD_VALID_TO_UNKNOWN_PASS")
print("D05_PERSON_DISTANCE_M="+str(valid["distance_m"]))
print("D05_UNKNOWN_REASON="+str(unknown["reason"]))
PY
STATUS="PASS_REAL_GAZEBO_RGBD_VALID_TO_UNKNOWN"
if [[ -f "$OUT/live/person_yolo_debug.png" && -n "$(printenv DISPLAY 2>/dev/null || true)" ]] &&
   command -v xdg-open >/dev/null; then
  xdg-open "$OUT/live/person_yolo_debug.png" >/dev/null 2>&1 || true
fi
echo "D05_IMAGE=$OUT/live/person_yolo_debug.png"
