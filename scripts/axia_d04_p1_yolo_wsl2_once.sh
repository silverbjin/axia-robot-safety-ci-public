#!/usr/bin/env bash
# AXIA D04 P1+YOLO WSL2 owner-only integration (no Goal/Fault, not P1 G00~G04).
# Download from an immutable public SHA and pass AXIA_D04_PUBLIC_SHA=that SHA.
set -Eeuo pipefail
umask 077
P1_REPO='silverbjin/axia-robot-safety-instructor'
P1_BRANCH='release/p1-r08-owner-signoff-wsl2-20261108'
P1_SHA='653ef49c30973c57a9fcc34b7b2fcc185bc84d95'
PUB_REPO='silverbjin/axia-robot-safety-ci-public'
PUB_BRANCH='preflight/d04-p1-yolo-integration-20261108'
YOLO_REPO='https://github.com/mgonzs13/yolo_ros.git'
YOLO_SHA='94d2dd500cb26027ee9c019f4d3a02029ac615cc'
ONNX_SHA='4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf'
ACTOR_SHA='49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e'
PUBLIC_SHA="${AXIA_D04_PUBLIC_SHA:-}"
if [[ "${1:-}" == "--self-check" ]]; then
  [[ "$P1_SHA" =~ ^[a-f0-9]{40}$ && "$YOLO_SHA" =~ ^[a-f0-9]{40}$ ]] || exit 2
  echo "AXIA_D04_OWNER_CONTRACT_OK P1=$P1_SHA P1_G00_G04_ACCEPTED=false"
  exit 0
fi
[[ $# -eq 0 ]] || { echo 'BLOCKED: invalid argument'; exit 2; }
[[ "$PUBLIC_SHA" =~ ^[a-f0-9]{40}$ ]] || { echo 'BLOCKED: AXIA_D04_PUBLIC_SHA must be a pinned commit'; exit 2; }
[[ -f /etc/os-release ]] || exit 2
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == '24.04' ]] || { echo 'BLOCKED: Ubuntu 24.04 required'; exit 2; }
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || { echo 'BLOCKED: WSL2 required'; exit 2; }
[[ -f /opt/ros/jazzy/setup.bash ]] || { echo 'BLOCKED: ROS 2 Jazzy required'; exit 2; }
set +u
source /opt/ros/jazzy/setup.bash
set -u
for b in gh git curl python3 ros2 gz colcon sha256sum timeout tar; do
  command -v "$b" >/dev/null || { echo "BLOCKED: missing executable $b"; exit 2; }
done
gh auth status >/dev/null 2>&1 || { echo 'BLOCKED: run gh auth login for private instructor access'; exit 2; }
ROOT="$HOME/.cache/axia/d04"
RUN_BASE="$HOME/axia_d04_evidence"
mkdir -p "$ROOT" "$RUN_BASE"
chmod 700 "$ROOT" "$RUN_BASE"
OUT="$(mktemp -d "$RUN_BASE/d04-p1-yolo-XXXXXXXX")"
SRC="$(mktemp -d "$ROOT/source-XXXXXXXX")"
STATE=BLOCKED
GATE_RC=125
finish() {
  local code=$?
  trap - EXIT INT TERM
  set +e
  python3 - "$OUT/owner_summary.json" "$STATE" "$GATE_RC" "$P1_SHA" "$PUBLIC_SHA" "$code" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);p.write_text(json.dumps({
 'status':sys.argv[2],'runtime_rc':int(sys.argv[3]),
 'p1_sha':sys.argv[4],'public_sha':sys.argv[5],
 'wrapper_exit':int(sys.argv[6]),'goal_sent':False,
 'fault_injected':False,'cmd_vel_published_by_demo':False,
 'p1_g00_g04_accepted':False,'certified_estop':False
},indent=2)+'\n')
PY
  if [[ -d "$SRC" && "$SRC" == "$ROOT"/source-* ]]; then rm -rf -- "$SRC"; fi
  (cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 -r sha256sum > SHA256SUMS)
  tar -czf "$OUT.tar.gz" -C "$RUN_BASE" "$(basename "$OUT")"
  sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256"
  printf '\nD04_OWNER_STATUS=%s\nGATE_RC=%s\nEVIDENCE=%s\nARCHIVE=%s\n' "$STATE" "$GATE_RC" "$OUT" "$OUT.tar.gz"
  echo 'G00_G04_ACCEPTED=false G_D04_P1_RUNTIME_PASS_ONLY_IF_VERDICT_JSON CERTIFIED_ESTOP=false'
  exit "$code"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
echo "AXIA D04 owner WSL2 / P1 SHA=$P1_SHA / public SHA=$PUBLIC_SHA"
echo "Evidence directory: $OUT"
# Do not mutate the owner's existing project checkout.
gh repo clone "$PUB_REPO" "$SRC/public" -- --single-branch --branch "$PUB_BRANCH" --depth 1 > "$OUT/public_checkout.log" 2>&1 || {
  echo 'BLOCKED: cannot fetch public D04 sources'; exit 2; }
git -C "$SRC/public" fetch -q --depth 1 origin "$PUBLIC_SHA" >> "$OUT/public_checkout.log" 2>&1 || exit 2
git -C "$SRC/public" checkout --detach -q "$PUBLIC_SHA" >> "$OUT/public_checkout.log" 2>&1 || exit 2
[[ "$(git -C "$SRC/public" rev-parse HEAD)" == "$PUBLIC_SHA" ]] || exit 2
gh repo clone "$P1_REPO" "$SRC/instructor" -- --single-branch --branch "$P1_BRANCH" --depth 1 > "$OUT/private_checkout.log" 2>&1 || {
  echo 'BLOCKED: cannot clone private instructor'; exit 2; }
git -C "$SRC/instructor" fetch -q --depth 1 origin "$P1_SHA" >> "$OUT/private_checkout.log" 2>&1 || exit 2
git -C "$SRC/instructor" checkout --detach -q "$P1_SHA" >> "$OUT/private_checkout.log" 2>&1 || exit 2
[[ "$(git -C "$SRC/instructor" rev-parse HEAD)" == "$P1_SHA" ]] || exit 2
# No dependency reinstallation if the official environment is ready; permit apt
# only for missing known official packages.
MISSING=()
for package in nav2_bringup nav2_minimal_tb3_sim turtlebot3_gazebo ros_gz_image; do
  ros2 pkg prefix "$package" >/dev/null 2>&1 || MISSING+=("$package")
done
if (( ${#MISSING[@]} > 0 )); then
  echo "Installing missing official ROS packages: ${MISSING[*]}"
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    ros-jazzy-nav2-bringup ros-jazzy-nav2-minimal-tb3-sim \
    ros-jazzy-turtlebot3-gazebo ros-jazzy-ros-gz
fi
if ! ros2 pkg prefix image_view >/dev/null 2>&1; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ros-jazzy-image-view || true
fi
if ! dpkg-query -W libcurl4-openssl-dev >/dev/null 2>&1; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libcurl4-openssl-dev
fi
P1_WS="$ROOT/p1_ws_$P1_SHA"
mkdir -p "$P1_WS"
(
  cd "$P1_WS"
  colcon build --base-paths "$SRC/instructor/ros2_ws/src" \
    --packages-select axia_safety_supervisor axia_fault_injector axia_scenario_verifier \
    --executor sequential --event-handlers console_direct+
) > "$OUT/p1_build.log" 2>&1 || { echo 'BLOCKED: P1 build failed'; tail -n 35 "$OUT/p1_build.log"; exit 2; }
YOLO_WS="$ROOT/yolo_ws_$YOLO_SHA"
if [[ ! -f "$YOLO_WS/install/setup.bash" ]]; then
  mkdir -p "$YOLO_WS/src"
  git clone -q "$YOLO_REPO" "$YOLO_WS/src/yolo_ros" || exit 2
  git -C "$YOLO_WS/src/yolo_ros" checkout --detach -q "$YOLO_SHA" || exit 2
  [[ "$(git -C "$YOLO_WS/src/yolo_ros" rev-parse HEAD)" == "$YOLO_SHA" ]] || exit 2
  (
    cd "$YOLO_WS"
    colcon build --merge-install --executor sequential --packages-up-to yolo_bringup \
      --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
      --event-handlers console_direct+
  ) > "$OUT/yolo_build.log" 2>&1 || {
    echo 'BLOCKED: actual yolo_ros C++ build failed'; tail -n 45 "$OUT/yolo_build.log"; exit 2; }
fi
mkdir -p "$ROOT/assets"
MODEL="$ROOT/assets/yolo26n.onnx"
ACTOR="$ROOT/assets/walk.dae"
if [[ ! -f "$MODEL" ]] || ! echo "$ONNX_SHA  $MODEL" | sha256sum -c - >/dev/null; then
  curl -fL --retry 3 --max-time 160 -o "$MODEL.tmp" \
    'https://huggingface.co/unileon-robotics/YOLO26-ONNX/resolve/main/yolo26n.onnx'
  mv -f "$MODEL.tmp" "$MODEL"
fi
if [[ ! -f "$ACTOR" ]] || ! echo "$ACTOR_SHA  $ACTOR" | sha256sum -c - >/dev/null; then
  curl -fL --retry 3 --max-time 160 -o "$ACTOR.tmp" \
    'https://fuel.gazebosim.org/1.0/Mingfei/models/actor/tip/files/meshes/walk.dae'
  mv -f "$ACTOR.tmp" "$ACTOR"
fi
echo "$ONNX_SHA  $MODEL" | sha256sum -c - || exit 2
echo "$ACTOR_SHA  $ACTOR" | sha256sum -c - || exit 2
set +u
source "$YOLO_WS/install/setup.bash"
source "$P1_WS/install/setup.bash"
set -u
export AXIA_ONNX_PATH="$MODEL"
export AXIA_ACTOR_DAE="$ACTOR"
export TURTLEBOT3_GAZEBO_SHARE="$(ros2 pkg prefix turtlebot3_gazebo)/share/turtlebot3_gazebo"
NAV2_SIM="$(ros2 pkg prefix nav2_minimal_tb3_sim)/share/nav2_minimal_tb3_sim"
export ROS_DOMAIN_ID=40
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
RUN_ARGS=()
if [[ "${AXIA_D04_GUI:-1}" == "1" && -n "${DISPLAY:-}" ]]; then
  RUN_ARGS+=(--gui --display-hold 20)
else
  echo "INFO: WSLg DISPLAY missing/disabled; testing headless. Review debug_frame.png afterward."
fi
cd "$SRC/public"
echo "Running full real P1+Gazebo Waffle RGB human+YOLO integration (NO Goal/Fault)..."
if timeout --signal=TERM --kill-after=20s 620s \
    python3 scripts/d04_p1_yolo_live.py \
      --instructor "$SRC/instructor" --p1-sha "$P1_SHA" \
      --waffle "$NAV2_SIM/urdf/gz_waffle.sdf.xacro" \
      --world "$NAV2_SIM/worlds/tb3_sandbox.sdf.xacro" \
      --pi "$TURTLEBOT3_GAZEBO_SHARE/models/turtlebot3_waffle_pi/model.sdf" \
      --actor "$ACTOR" --onnx "$MODEL" \
      --out "$OUT/live" "${RUN_ARGS[@]}" \
    > "$OUT/live_stdout.log" 2>&1; then
  GATE_RC=0
else
  GATE_RC=$?
  echo "BLOCKED: live P1+YOLO runtime gate rc=$GATE_RC"
  tail -n 50 "$OUT/live_stdout.log" || true
  exit 2
fi
python3 - "$OUT/live/verdict.json" <<'PY'
import json,sys
from pathlib import Path
s=json.loads(Path(sys.argv[1]).read_text())
assert s.get('status')=='PASS_P1_GRAPH_UNCHANGED_REAL_PERSON'
assert s.get('graph_unchanged') is True
assert all(s.get(k,False) for k in ('person_valid','rgb_valid','debug_saved'))
assert s.get('goal_sent') is False and s.get('fault_injected') is False
print('AXIA_D04_P1_YOLO_REAL_SIMULTANEOUS_PASS_NOT_P1_G00_G04_ACCEPTANCE')
PY
STATE=PASS_P1_YOLO_READONLY
if command -v xdg-open >/dev/null 2>&1 && [[ -n "${DISPLAY:-}" ]]; then
  xdg-open "$OUT/live/debug_frame.png" >/dev/null 2>&1 || true
fi
echo "AXIA D04 actual debug image: $OUT/live/debug_frame.png"
