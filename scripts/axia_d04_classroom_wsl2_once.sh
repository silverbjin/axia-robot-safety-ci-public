#!/usr/bin/env bash
# AXIA D04 classroom owner entrypoint: official P1 + ROS2 Jazzy + Gazebo Harmonic
# + pinned C++ yolo_ros ONNX. NO Python Ultralytics/.pt/photo assets required.
# No Goal, Fault injection, motor publication, or certified E-Stop.
set -Eeuo pipefail
umask 077

PIN='3668250ac14680b0ea81a67063938374a8c6820f'
ORIGIN='silverbjin/axia-robot-safety-ci-public'
RVIZ_BUNDLE_SHA='916a3623a1370c513201011a1b410b938e2b3752'
RUNNER='scripts/axia_d04_ros_package_wsl2_once.sh'
SINGLE_IMAGE_PIN='e16804ec240d4b4ec295d964f826c3015a2ba9e9'
SINGLE_IMAGE_RUNNER='scripts/axia_d04_instructor_single_image_once.sh'
MODE="${1:---run}"
[[ $# -le 1 ]] || { echo 'D04_CLASSROOM_USAGE: use --run, --preflight, --self-check or --single-image' >&2; exit 2; }
case "$MODE" in
  --run|--preflight|--self-check|--single-image) ;;
  *) echo 'D04_CLASSROOM_USAGE: use --run, --preflight, --self-check or --single-image' >&2; exit 2 ;;
esac

if [[ "$MODE" == --self-check ]]; then
  echo "D04_CLASSROOM_PUBLIC_SHA=$PIN"
  echo "D04_CLASSROOM_SINGLE_IMAGE_PUBLIC_SHA=$SINGLE_IMAGE_PIN"
  echo "D04_RVIZ_BUNDLE_SHA=$RVIZ_BUNDLE_SHA"
  echo "D04_RVIZ_STATIC_CONFIGURATION=READ_ONLY"
  echo "D04_CLASSROOM_STATIC_PASS GAZEBO_NOT_RUN YOLO_NOT_RUN"
  echo "D04_CLASSROOM_PATH=GAZEBO_ROS2_JAZZY_CPP_ONNX NO_PYTHON_PT_REQUIRED"
  echo "D04_CLASSROOM_SINGLE_IMAGE_AVAILABLE=--single-image NO_ROS_NO_GAZEBO"
  exit 0
fi

# Optional lecture add-on. Separate lifecycle and evidence from the proven P1 demo.
# The SINGLE_IMAGE_PIN is immutable and contains ONLY public student inference
# plus read-only annotation; it never launches ROS/Gazebo or xdg-open.
run_single_image() {
  local temp_script
  temp_script="$(mktemp)"
  local rc=0
  if curl -fsSL --retry 3 --connect-timeout 15 \
      "https://raw.githubusercontent.com/$ORIGIN/$SINGLE_IMAGE_PIN/$SINGLE_IMAGE_RUNNER" \
      -o "$temp_script" &&
     bash -n "$temp_script" &&
     bash "$temp_script" --self-check &&
     bash "$temp_script" --run; then
    rc=0
  else
    rc=$?
    echo "D04_CLASSROOM_SINGLE_IMAGE_BLOCKED rc=$rc (Gazebo owner verdict unchanged)" >&2
  fi
  rm -f -- "$temp_script"
  return "$rc"
}
if [[ "$MODE" == --single-image ]]; then
  # No unnecessary gh auth, ROS2, Nav2 or Gazebo check for the image-only demo.
  run_single_image
  exit $?
fi

check_host() {
  # The classroom GUI acceptance is deliberately limited to Owner WSL2.
  if ! grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease; then
    echo 'D04_CLASSROOM_WSL2_REQUIRED: this entrypoint is for WSL2 Ubuntu 24.04'
    return 2
  fi
  if [[ ! -f /etc/os-release ]]; then
    echo 'D04_CLASSROOM_UBUNTU_24_04_REQUIRED'
    return 2
  fi
  (
    . /etc/os-release
    if [[ "$ID" != ubuntu || "$VERSION_ID" != 24.04 ]]; then
      echo 'D04_CLASSROOM_UBUNTU_24_04_REQUIRED'
      exit 2
    fi
  ) || return 2
  local failed=0
  for bin in curl bash git gh gz ros2 colcon python3 sha256sum timeout tar; do
    if ! command -v "$bin" >/dev/null 2>&1; then
      echo "D04_CLASSROOM_MISSING_TOOL=$bin"
      failed=1
    fi
  done
  if [[ ! -r /opt/ros/jazzy/setup.bash ]]; then
    echo 'D04_CLASSROOM_ROS_JAZZY_MISSING=/opt/ros/jazzy/setup.bash'
    failed=1
  fi
  if ! command -v gh >/dev/null 2>&1 || ! gh auth status >/dev/null 2>&1; then
    echo 'D04_CLASSROOM_GH_AUTH_REQUIRED: gh auth login for private instructor repository'
    failed=1
  fi
  if [[ -z "${DISPLAY:-}" ]]; then
    echo 'D04_CLASSROOM_WSLG_DISPLAY_MISSING: start WSLg before GUI demonstration'
    failed=1
  fi
  if ((failed > 0)); then
    echo 'D04_CLASSROOM_PREFLIGHT_BLOCKED NO_GOAL_SENT GAZEBO_NOT_RUN'
    return 2
  fi
  echo 'D04_CLASSROOM_PREFLIGHT_PASS: host prerequisites only, Gazebo NOT_RUN'
}
check_host
if [[ "$MODE" == --preflight ]]; then
  exit 0
fi

# Optional read-only RViz sidecar: do not alter the Owner gate/Goal semantics.
RVIZ_AUTO="${AXIA_D04_RVIZ_AUTO:-1}"
[[ "$RVIZ_AUTO" == 0 || "$RVIZ_AUTO" == 1 ]] || {
  echo "D04_RVIZ_AUTO_INVALID: use 0 or 1" >&2; exit 2; }
RVIZ_TMP="$(mktemp -d)"
RVIZ_READY=0
TMP="$(mktemp)"
trap 'rm -rf -- "$RVIZ_TMP"; rm -f -- "$TMP"' EXIT
fetch_rviz_asset() {
  local rel="$1" dest="$2"
  curl -fsSL --retry 3 --connect-timeout 15 \
    "https://raw.githubusercontent.com/$ORIGIN/$RVIZ_BUNDLE_SHA/$rel" -o "$dest"
}
if fetch_rviz_asset "scripts/axia_d04_rviz_observer.sh" "$RVIZ_TMP/launcher.sh" &&
   fetch_rviz_asset "scripts/d04_rviz_hold_observer.py" "$RVIZ_TMP/observer.py" &&
   fetch_rviz_asset "rviz/axia_d04_robot_state.rviz" "$RVIZ_TMP/axia_d04_robot_state.rviz"; then
  if bash -n "$RVIZ_TMP/launcher.sh" &&
     python3 -m py_compile "$RVIZ_TMP/observer.py" &&
     bash "$RVIZ_TMP/launcher.sh" --install "$RVIZ_TMP/axia_d04_robot_state.rviz"; then
    RVIZ_READY=1
    echo "D04_RVIZ_CONFIG_READY: saved .rviz + one-click shortcut"
  else
    echo "D04_RVIZ_INSTALL_BLOCKED: Owner demo remains independently available"
  fi
else
  echo "D04_RVIZ_DOWNLOAD_BLOCKED: Owner demo remains independently available"
fi

URL="https://raw.githubusercontent.com/$ORIGIN/$PIN/$RUNNER"
curl -fsSL --retry 3 --connect-timeout 15 "$URL" -o "$TMP"
bash -n "$TMP"
STATIC_OUTPUT="$(bash "$TMP" --self-check)"
if [[ "$STATIC_OUTPUT" != *'AXIA_D04_PACKAGE_WRAPPER_STATIC_OK'* ]]; then
  echo 'D04_CLASSROOM_PINNED_OWNER_RUNNER_INVALID' >&2
  exit 2
fi
echo "D04_CLASSROOM_PINNED_OWNER_RUNNER_READY sha=$PIN"
echo 'D04_CLASSROOM_START: real Gazebo + YOLO ONNX + managed Nav2 shutdown'
# Run the viewer only AFTER P1/YOLO acceptance, during GUI_DEMO_HOLD.
HOLD_SECONDS="${AXIA_D04_DEMO_HOLD_S:-120}"
[[ "$HOLD_SECONDS" =~ ^[0-9]{1,3}$ ]] || {
  echo "D04_CLASSROOM_HOLD_INVALID" >&2; exit 2; }
echo "D04_RVIZ_AUTO=$RVIZ_AUTO RVIZ_READY=$RVIZ_READY"
if [[ "$RVIZ_AUTO" == 1 && "$RVIZ_READY" == 1 ]]; then
  # pipefail retains Owner errors; observer never upgrades verdict to PASS.
  AXIA_D04_PUBLIC_SHA="$PIN" \
  AXIA_D04_REPEAT=1 \
  AXIA_D04_GUI=1 \
  AXIA_D04_DEMO_HOLD_S="$HOLD_SECONDS" \
    bash "$TMP" | python3 -u "$RVIZ_TMP/observer.py" \
      --launcher "$HOME/.local/bin/axia-d04-rviz" \
      --log "$HOME/.cache/axia/d04/d04_rviz_observer.log"
else
  AXIA_D04_PUBLIC_SHA="$PIN" \
  AXIA_D04_REPEAT=1 \
  AXIA_D04_GUI=1 \
  AXIA_D04_DEMO_HOLD_S="$HOLD_SECONDS" \
    bash "$TMP"
fi
echo 'D04_CLASSROOM_OWNER_SCRIPT_EXIT_ZERO: review EVIDENCE and verdict.json before acceptance'
echo 'D04_RVIZ_GUI_ACCEPTANCE=NOT_INFERRED_FROM_OWNER_EXIT'
# Opt-in combined classroom flow. Preserve historical --run semantics and
# existing Gazebo evidence unless lecturer explicitly enables the second part.
if [[ "${AXIA_D04_SINGLE_IMAGE_AFTER_GAZEBO:-0}" == "1" ]]; then
  echo 'D04_CLASSROOM_GAZEBO_OWNER_FINISHED; BEGIN_INDEPENDENT_SINGLE_IMAGE'
  run_single_image
elif [[ "${AXIA_D04_SINGLE_IMAGE_AFTER_GAZEBO:-0}" != "0" ]]; then
  echo 'D04_CLASSROOM_SINGLE_IMAGE_AFTER_GAZEBO_INVALID: use 0 or 1' >&2
  exit 2
fi

