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
export AXIA_D08_EXACT_SOURCE_SHA="$SHA"
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
 ros-jazzy-navigation2 ros-jazzy-rviz2 libgl1-mesa-dri libglx-mesa0 mesa-utils
 ros-jazzy-ros2trace lttng-tools babeltrace
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

# Actual Owner evidence selected Intel Iris Xe on a dual-GPU WSLg host.
# Official Microsoft WSLg selection: MESA_D3D12_DEFAULT_ADAPTER_NAME.
# Request NVIDIA and verify GLX actually uses it; software fallback or
# an unchanged Intel renderer is a BLOCKER before burning 100+ MB assets.
# NVIDIA selection improves GPU eligibility but is NOT a 500ms/RTF PASS.
export MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
GPU_INFO="$(glxinfo -B 2>&1 || true)"
GPU_RENDERER="$(printf '%s\n' "$GPU_INFO" | grep -m1 'OpenGL renderer string:' || true)"
if [[ "$GPU_RENDERER" != *'D3D12 (NVIDIA'* ]]; then
  echo "D08_OWNER_WSLG_NVIDIA_D3D12_NOT_AVAILABLE=$GPU_RENDERER" >&2
  echo 'D08_OWNER_L3_HOLD_SELECT_DISCRETE_GPU_IN_WINDOWS_AND_VERIFY_GLX' >&2
  exit 2
fi
echo "D08_OWNER_WSLG_NVIDIA_D3D12_VERIFIED=$GPU_RENDERER"
printf '%s\n' "$GPU_INFO" > "$RUN_DIR/owner_gpu_probe.txt"

# Exact public Owner diagnostic branch fetched for immutable SHA checkout;
# preserve older PR #166 successful evidence without using its obsolete tip.
SRC="$RUN_DIR/src"
git clone -q --filter=blob:none \
  https://github.com/silverbjin/axia-robot-safety-ci-public.git "$SRC"
git -C "$SRC" fetch -q origin refs/heads/fix/d08-owner-rmw-one-shot-20261119
git -C "$SRC" checkout -q --detach "$SHA"
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$SHA" ]] || {
  echo D08_OWNER_SOURCE_SHA_MISMATCH >&2; exit 2; }
echo "D08_OWNER_EXACT_SOURCE_SHA_VERIFIED=$SHA"

# Reuse existing CI-tested native Gazebo / independent ROS Scan observers.
# Fail closed rather than silently running without one causal layer.
if ! /usr/bin/python3 -c 'from gz.transport13 import Node; from gz.msgs10.laserscan_pb2 import LaserScan; from gz.msgs10.clock_pb2 import Clock' >/dev/null 2>&1; then
  if ! apt-cache show python3-gz-transport13 >/dev/null 2>&1; then
    curl -fLsS --retry 2 --connect-timeout 15 --max-time 60 \
      https://packages.osrfoundation.org/gazebo.gpg \
      -o "$RUN_DIR/gazebo-package-key.gpg"
    sudo install -m 0644 "$RUN_DIR/gazebo-package-key.gpg" \
      /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
    printf 'deb [arch=%s signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable noble main\n' \
      "$(dpkg --print-architecture)" | \
      sudo tee /etc/apt/sources.list.d/axia-d08-gazebo-stable.list >/dev/null
    sudo apt-get update -qq
  fi
  sudo apt-get install -y -qq --no-install-recommends --no-upgrade \
    python3-gz-transport13 python3-gz-msgs10
fi
/usr/bin/python3 -c 'from gz.transport13 import Node; from gz.msgs10.laserscan_pb2 import LaserScan; from gz.msgs10.clock_pb2 import Clock' || {
  echo D08_OWNER_NATIVE_GZ_RX_PRECHECK_BLOCKED >&2; exit 2;
}
echo D08_OWNER_NATIVE_GZ_ROS_RX_PROBES_AVAILABLE

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
# Retain asset digests only; 100MiB official NuGet/ONNX/binary is NEVER
# added to the outgoing diagnostic archive.
sha256sum "$ASSETS/walk.dae" "$ORT_PACKAGE" "$MODEL" > "$RUN_DIR/asset_sha256.txt"

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

# One WSL2 run, bounded 120-second (configurable <=180s) tracing.
# Trace begins before existing YOLO and Gazebo child ROS nodes, so the
# publisher, original Observer, and independent subscriber are identifiable.
export AXIA_D08_NATIVE_RX_PROBE=1
export AXIA_D08_ROS_ISOLATED_RX_PROBE=1
export AXIA_D08_TRACE_OUT="$RUN_DIR/rmw_trace"
export AXIA_D08_TRACE_SESSION="axia_d08_owner_$"
AXIA_D08_TRACE_CAPTURE_MAX_S="${AXIA_D08_TRACE_CAPTURE_MAX_S:-120}"
if [[ ! "$AXIA_D08_TRACE_CAPTURE_MAX_S" =~ ^[0-9]+$ ]] ||
   ((AXIA_D08_TRACE_CAPTURE_MAX_S<60 || AXIA_D08_TRACE_CAPTURE_MAX_S>180)); then
  echo D08_OWNER_TRACE_DURATION_RANGE_60_TO_180_REQUIRED >&2; exit 2
fi
TRACE_SCRIPT="$SRC/d08/scripts/d08_ros_trace_live_ci.sh"
TRACE_STARTED=0
TRACE_WATCH_PID=""
YOLO_GROUP=""
cleanup() {
  local original_rc="$?"
  local trace_rc=0
  trap - EXIT
  if [[ -n "$YOLO_GROUP" ]]; then
    kill -- "-$YOLO_GROUP" 2>/dev/null || true
  fi
  if [[ -n "$TRACE_WATCH_PID" ]]; then
    kill "$TRACE_WATCH_PID" 2>/dev/null || true
    wait "$TRACE_WATCH_PID" 2>/dev/null || true
  fi
  if ((TRACE_STARTED)); then
    if ! bash "$TRACE_SCRIPT" stop > "$RUN_DIR/rmw_trace_stop.log" 2>&1; then
      trace_rc=2
      echo D08_OWNER_RMW_TRACE_STOP_OR_SUMMARY_BLOCKED >&2
      tail -n 30 "$RUN_DIR/rmw_trace_stop.log" >&2 || true
    fi
  else
    trace_rc=2
  fi
  if ! python3 "$SRC/d08/scripts/d08_owner_rmw_first_gap.py" \
       --phase finalize --run "$RUN_DIR" \
       --rows "$AXIA_D08_TRACE_OUT/rmw_source_rows.jsonl" \
       --trace-summary "$AXIA_D08_TRACE_OUT/summary.json" \
       --out "$AXIA_D08_TRACE_OUT/owner_first_gap_verdict.json"; then
    trace_rc=2
    echo D08_OWNER_FIRST_BOUNDARY_RMW_CLASSIFIER_BLOCKED >&2
  fi
  echo "D08_OWNER_FIRST_BOUNDARY_RMW_VERDICT=$AXIA_D08_TRACE_OUT/owner_first_gap_verdict.json"
  # A real first >500ms violation with missing/expired RMW trace is HOLD,
  # even if the separate no-Goal GUI code exited zero.
  if ! python3 - "$AXIA_D08_TRACE_OUT/owner_first_gap_verdict.json" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
if not p.is_file():
    sys.exit(2)
x=json.loads(p.read_text())
if x.get("first_500ms_violation_retained") and x.get("candidate")=="EVIDENCE_INCOMPLETE":
    sys.exit(2)
PY
  then
    trace_rc=2
    echo D08_OWNER_FIRST_SCAN_CAPTURE_INCOMPLETE_HOLD >&2
  fi
  # Always create a bounded PRIVATE diagnostics ZIP on Owner GUI exit,
  # including Ctrl+C and first timing failures. Raw CTF, JSONL, .git,
  # models, binaries, full run logs are NEVER in the outgoing ZIP.
  if [[ -f "$SRC/d08/scripts/d08_compact_evidence.py" ]]; then
    local compact="${RUN_DIR}.diagnostics.zip"
    if python3 "$SRC/d08/scripts/d08_compact_evidence.py" \
         --run "$RUN_DIR" --out "$compact"; then
      sha256sum "$compact" > "${compact}.sha256"
      echo "D08_OWNER_COMPACT_EVIDENCE=$compact"
      echo "D08_OWNER_COMPACT_EVIDENCE_SHA256=$(cut -d' ' -f1 "${compact}.sha256")"
      echo D08_OWNER_RAW_RUN_RETAINED_LOCALLY_NOT_ARCHIVED
    else
      trace_rc=2
      echo D08_OWNER_COMPACT_EVIDENCE_FAILED >&2
    fi
  fi
  if ((trace_rc!=0)); then
    echo D08_OWNER_RMW_EVIDENCE_HOLD_NOT_L3_ACCEPTED >&2
    ((original_rc==0)) && original_rc=2
  fi
  echo D08_OWNER_FIRST_BOUNDARY_RMW_CAUSE_UNDETERMINED
  exit "$original_rc"
}
trap cleanup EXIT
if ! bash "$TRACE_SCRIPT" start; then
  echo D08_OWNER_RMW_TRACE_START_BLOCKED_NOT_L3_ACCEPTED >&2
  exit 2
fi
TRACE_STARTED=1
(
  sleep "$AXIA_D08_TRACE_CAPTURE_MAX_S"
  bash "$TRACE_SCRIPT" stop > "$RUN_DIR/rmw_trace_watchdog.log" 2>&1 ||
    echo D08_OWNER_RMW_TRACE_WATCHDOG_STOP_BLOCKED >> "$RUN_DIR/rmw_trace_watchdog.log"
) &
TRACE_WATCH_PID="$!"
echo "D08_OWNER_RMW_TRACE_CAPTURE_MAX_S=$AXIA_D08_TRACE_CAPTURE_MAX_S"
echo D08_OWNER_RMW_TRACE_STARTED_BEFORE_YOLO_AND_GAZEBO
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
