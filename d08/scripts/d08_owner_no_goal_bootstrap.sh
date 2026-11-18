#!/usr/bin/env bash
# Public D08 NO_GOAL WSL2/WSLg owner bootstrap, exact-SHA and evidence-safe.
set -Eeuo pipefail
MODE="${1:---run}"
case "$MODE" in --self-check|--doctor|--run) ;; *)
  echo D08_OWNER_USAGE=--self-check\|--doctor\|--run >&2; exit 2 ;; esac
if [[ "$MODE" == --self-check ]]; then
  bash -n "$0"
  echo D08_OWNER_BOOTSTRAP_L0_PASS_ROS_GAZEBO_WSLG_NOT_RUN_NO_GOAL
  exit 0
fi
SHA="${AXIA_D08_PUBLIC_SHA:-}"
if [[ ! "$SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo D08_OWNER_PINNED_PUBLIC_SHA_REQUIRED >&2; exit 2
fi
if [[ ! -r /opt/ros/jazzy/setup.bash ]]; then
  echo D08_OWNER_ROS_JAZZY_REQUIRED >&2; exit 2
fi
if ! grep -Eiq '(microsoft|wsl)' /proc/version; then
  echo D08_OWNER_WSL2_REQUIRED >&2; exit 2
fi
if [[ -z "${DISPLAY:-}" ]]; then
  echo D08_OWNER_WSLG_DISPLAY_NOT_AVAILABLE >&2; exit 2
fi
set +u
source /opt/ros/jazzy/setup.bash
set -u
export ROS_DOMAIN_ID=69
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export MAKEFLAGS=-j2
echo "D08_OWNER_PINNED_PUBLIC_SHA=$SHA"
if command -v glxinfo >/dev/null 2>&1; then
  glxinfo -B 2>/dev/null | grep -E 'OpenGL renderer|OpenGL vendor' || true
else
  echo D08_OWNER_GLXINFO_OPTIONAL_MISSING
fi
if [[ "$MODE" == --doctor ]]; then
  for pkg in nav2_bringup nav2_minimal_tb3_sim turtlebot3_gazebo ros_gz_image; do
    ros2 pkg prefix "$pkg" >/dev/null 2>&1 ||
      echo "D08_OWNER_PACKAGE_MISSING=$pkg"
  done
  for cmd in git curl gz ros2 colcon xacro cmake; do
    command -v "$cmd" >/dev/null 2>&1 ||
      echo "D08_OWNER_COMMAND_MISSING=$cmd"
  done
  echo D08_OWNER_DOCTOR_ONLY_ROS_AND_GAZEBO_NOT_LAUNCHED
  exit 0
fi

BASE="${AXIA_D08_OWNER_EVIDENCE_ROOT:-$HOME/axia_d08_owner_runs}"
mkdir -p "$BASE"
RUN_DIR="$(mktemp -d "$BASE/run_$(date -u +%Y%m%dT%H%M%SZ)_XXXXXX")"
echo "D08_OWNER_EVIDENCE_ROOT=$RUN_DIR"

# Dependency list mirrors the successful public Jazzy/YOLO source build.
required=(
 git curl ca-certificates build-essential cmake python3-pip
 python3-colcon-common-extensions python3-opencv libopencv-dev
 libyaml-cpp-dev libcurl4-openssl-dev libjpeg-dev
 ros-jazzy-rclpy ros-jazzy-rclcpp ros-jazzy-rclcpp-lifecycle
 ros-jazzy-sensor-msgs ros-jazzy-std-msgs ros-jazzy-geometry-msgs
 ros-jazzy-visualization-msgs ros-jazzy-message-filters
 ros-jazzy-tf2-ros ros-jazzy-cv-bridge ros-jazzy-image-transport
 ros-jazzy-vision-msgs ros-jazzy-pluginlib ros-jazzy-launch-ros
 ros-jazzy-ament-index-cpp ros-jazzy-ament-cmake ros-jazzy-ament-cmake-python
 ros-jazzy-nav2-minimal-tb3-sim ros-jazzy-turtlebot3-gazebo
 ros-jazzy-ros-gz ros-jazzy-ros-gz-image ros-jazzy-xacro
 ros-jazzy-nav2-collision-monitor ros-jazzy-nav2-bringup
 ros-jazzy-navigation2 ros-jazzy-rviz2 libgl1-mesa-dri libglx-mesa0
)
missing=()
for pkg in "${required[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null |
       grep -Fq 'install ok installed'; then missing+=("$pkg"); fi
done
if ((${#missing[@]}>0)); then
  echo "D08_OWNER_INSTALL_OFFICIAL_MISSING_COUNT=${#missing[@]}"
  sudo -v
  sudo apt-get update -qq
  sudo apt-get install -y -qq --no-install-recommends "${missing[@]}"
fi

# This SHA must be reachable from public PR #166, never a mutable branch tip.
SRC="$RUN_DIR/src"
git clone -q --filter=blob:none \
  https://github.com/silverbjin/axia-robot-safety-ci-public.git "$SRC"
git -C "$SRC" fetch -q origin refs/pull/166/head
git -C "$SRC" checkout -q --detach "$SHA"
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$SHA" ]] || {
  echo D08_OWNER_SOURCE_SHA_MISMATCH >&2; exit 2; }
echo "D08_OWNER_EXACT_SOURCE_SHA_VERIFIED=$SHA"

ASSETS="$RUN_DIR/assets"
mkdir -p "$ASSETS"
curl -fL --retry 3 --connect-timeout 15 --max-time 100 \
  'https://fuel.gazebosim.org/1.0/Mingfei/models/actor/tip/files/meshes/walk.dae' \
  -o "$ASSETS/walk.dae"
echo "49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e  $ASSETS/walk.dae" |
  sha256sum -c -

ORT_PACKAGE="$ASSETS/microsoft.ml.onnxruntime.1.20.0.nupkg"
curl -fL --retry 2 --connect-timeout 15 --max-time 120 \
  'https://api.nuget.org/v3-flatcontainer/microsoft.ml.onnxruntime/1.20.0/microsoft.ml.onnxruntime.1.20.0.nupkg' \
  -o "$ORT_PACKAGE"
echo "36dbafacb1bc532e92d02371bd70582a61105872561fc9982314854d1c7ebf72  $ORT_PACKAGE" |
  sha256sum -c -
ORT_ROOT="$RUN_DIR/official_ort"
python3 "$SRC/d08/scripts/d08_prepare_official_ort_nuget.py" \
  --package "$ORT_PACKAGE" --root "$ORT_ROOT"
readelf -d "$ORT_ROOT/lib/libonnxruntime.so" |
  grep -Fq 'Library soname: [libonnxruntime.so.1]'
[[ -L "$ORT_ROOT/lib/libonnxruntime.so.1" ]] ||
  { echo D08_OWNER_ORT_ELF_SONAME_MISSING >&2; exit 2; }

MODEL="$ASSETS/yolo26n.onnx"
curl -fL --retry 3 --max-time 160 \
  'https://huggingface.co/unileon-robotics/YOLO26-ONNX/resolve/main/yolo26n.onnx' \
  -o "$MODEL"
echo "4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf  $MODEL" |
  sha256sum -c -

YOLO_WS="$RUN_DIR/yolo_ws"
mkdir -p "$YOLO_WS/src"
git clone -q https://github.com/mgonzs13/yolo_ros.git "$YOLO_WS/src/yolo_ros"
git -C "$YOLO_WS/src/yolo_ros" checkout -q --detach \
  94d2dd500cb26027ee9c019f4d3a02029ac615cc
[[ "$(git -C "$YOLO_WS/src/yolo_ros" rev-parse HEAD)" == \
   94d2dd500cb26027ee9c019f4d3a02029ac615cc ]] ||
  { echo D08_OWNER_YOLO_UPSTREAM_SHA_MISMATCH >&2; exit 2; }
(
  cd "$YOLO_WS"
  set +u; source /opt/ros/jazzy/setup.bash; set -u
  colcon build --merge-install --executor sequential \
    --packages-up-to yolo_bringup \
    --cmake-args -DBUILD_TESTING=OFF "-DONNXRUNTIME_ROOT=$ORT_ROOT" \
    --event-handlers console_cohesion+
) > "$RUN_DIR/yolo_build.log" 2>&1 || {
  tail -n 60 "$RUN_DIR/yolo_build.log" >&2
  echo D08_OWNER_YOLO_BUILD_BLOCKED >&2; exit 2; }
set +u
source /opt/ros/jazzy/setup.bash
source "$YOLO_WS/install/setup.bash"
set -u
ldd "$YOLO_WS/install/lib/yolo_ros/yolo_node" > "$RUN_DIR/yolo_ldd.log"
if grep -Fq 'not found' "$RUN_DIR/yolo_ldd.log" ||
   ! grep -Fq 'libonnxruntime.so.1 =>' "$RUN_DIR/yolo_ldd.log"; then
  echo D08_OWNER_YOLO_ELF_NOT_RESOLVED >&2; exit 2
fi
echo D08_OWNER_PINNED_YOLO_BUILD_AND_ELF_PASS

PARAMS="$ASSETS/d08_owner_yolo.yaml"
cat > "$PARAMS" <<YAML
/yolo/yolo_node:
  ros__parameters:
    use_sim_time: true
    plugins: ["detection", "debug"]
    cameras: ["cam0"]
    cam0:
      rgb_topic: /axia/d08/rgbd/image
      image_reliability: 2
    detection:
      plugin: yolo_ros/DetectionPlugin
      cameras: ["cam0"]
      model_path: "$MODEL"
      model_repo: ""
      model_filename: ""
      model_type: auto
      provider: cpu
      threshold: 0.25
      iou: 0.45
      n_threads: 2
      max_fps: 5
    debug:
      plugin: yolo_ros/DebugPlugin
      cameras: ["cam0"]
YAML

YOLO_GROUP=""
cleanup() {
  if [[ -n "$YOLO_GROUP" ]]; then
    kill -- "-$YOLO_GROUP" 2>/dev/null || true
  fi
}
trap cleanup EXIT
setsid ros2 launch yolo_bringup yolo.launch.py \
  "params_file:=$PARAMS" > "$RUN_DIR/yolo_native.log" 2>&1 &
YOLO_GROUP="$!"
sleep 3
if ! kill -0 "$YOLO_GROUP" 2>/dev/null; then
  tail -n 60 "$RUN_DIR/yolo_native.log" >&2
  echo D08_OWNER_YOLO_NODE_NOT_ALIVE >&2; exit 2
fi
echo D08_OWNER_GUI_PUBLIC_NO_GOAL_BEGIN
echo D08_OWNER_GUI_CTRL_C_TO_END
if python3 -u "$SRC/d08/scripts/d08_public_gazebo_l2.py" \
     --actor "$ASSETS/walk.dae" \
     --out "$RUN_DIR/live_evidence" \
     --official-nav2 --official-path-phases --live-person-range --owner-gui; then
  echo D08_OWNER_GUI_NO_GOAL_RUNTIME_EXIT0
else
  rc="$?"
  echo "D08_OWNER_GUI_FIRST_BOUNDARY_RC=$rc"
  echo "D08_OWNER_EVIDENCE_ROOT=$RUN_DIR"
  exit "$rc"
fi
echo D08_OWNER_WSLG_PIXEL_ACCEPTANCE_NOT_AUTOMATICALLY_PROVEN
echo "D08_OWNER_EVIDENCE_ROOT=$RUN_DIR"
