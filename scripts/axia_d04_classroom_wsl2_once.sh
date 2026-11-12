#!/usr/bin/env bash
# AXIA D04 classroom owner entrypoint: official P1 + ROS2 Jazzy + Gazebo Harmonic
# + pinned C++ yolo_ros ONNX. NO Python Ultralytics/.pt/photo assets required.
# No Goal, Fault injection, motor publication, or certified E-Stop.
set -Eeuo pipefail
umask 077

PIN='c775820077917c4da56c6aa60001b224071664b3'
ORIGIN='silverbjin/axia-robot-safety-ci-public'
RUNNER='scripts/axia_d04_ros_package_wsl2_once.sh'
MODE="${1:---run}"
[[ $# -le 1 ]] || { echo 'D04_CLASSROOM_USAGE: use --run, --preflight or --self-check' >&2; exit 2; }
case "$MODE" in
  --run|--preflight|--self-check) ;;
  *) echo 'D04_CLASSROOM_USAGE: use --run, --preflight or --self-check' >&2; exit 2 ;;
esac

if [[ "$MODE" == --self-check ]]; then
  echo "D04_CLASSROOM_PUBLIC_SHA=$PIN"
  echo "D04_CLASSROOM_STATIC_PASS GAZEBO_NOT_RUN YOLO_NOT_RUN"
  echo "D04_CLASSROOM_PATH=GAZEBO_ROS2_JAZZY_CPP_ONNX NO_PYTHON_PT_REQUIRED"
  exit 0
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

TMP="$(mktemp)"
trap 'rm -f -- "$TMP"' EXIT
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
AXIA_D04_PUBLIC_SHA="$PIN" \
AXIA_D04_REPEAT=1 \
AXIA_D04_GUI=1 \
AXIA_D04_DEMO_HOLD_S=90 \
  bash "$TMP"
echo 'D04_CLASSROOM_OWNER_SCRIPT_EXIT_ZERO: review EVIDENCE and verdict.json before acceptance'
