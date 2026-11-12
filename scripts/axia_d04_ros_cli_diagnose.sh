#!/usr/bin/env bash
# D04 read-only classroom diagnosis: yolo_msgs is in the pinned ROS overlay.
# No Gazebo launch, Goal, Fault, cmd_vel, or safety hardware interaction.
set -Eeuo pipefail

MODE="${1:---doctor}"
if [[ $# -gt 1 || ( "$MODE" != "--doctor" && "$MODE" != "--live" && "$MODE" != "--self-check" ) ]]; then
  echo "D04_CLI_USAGE: --doctor | --live | --self-check" >&2
  exit 2
fi

YOLO_SHA='94d2dd500cb26027ee9c019f4d3a02029ac615cc'
D04_SHA='f2edba114dd0540d1f27a1e216bfda2b885c5cb9'
ROS_SETUP="${AXIA_D04_CLI_ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
YOLO_SETUP="${AXIA_D04_CLI_YOLO_SETUP:-$HOME/.cache/axia/d04/yolo_ws_$YOLO_SHA/install/setup.bash}"
D04_SETUP="${AXIA_D04_CLI_D04_SETUP:-$HOME/.cache/axia/d04/d04_package_ws_$D04_SHA/install/setup.bash}"

if [[ "$MODE" == "--self-check" ]]; then
  echo "D04_CLI_STATIC_PASS ROS_NOT_RUN GAZEBO_NOT_RUN YOLO_NOT_RUN"
  echo "D04_CLI_EXPECTED_YOLO_SHA=$YOLO_SHA"
  echo "D04_CLI_EXPECTED_D04_SHA=$D04_SHA"
  exit 0
fi

for kind in ROS YOLO D04; do
  case "$kind" in
    ROS) file="$ROS_SETUP" ;;
    YOLO) file="$YOLO_SETUP" ;;
    D04) file="$D04_SETUP" ;;
  esac
  if [[ ! -r "$file" ]]; then
    echo "D04_CLI_$kind"_OVERLAY_MISSING="$file"
    echo "D04_CLI_LIVE_DATA=NOT_CHECKED"
    exit 2
  fi
done

set +u
source "$ROS_SETUP"
source "$YOLO_SETUP"
source "$D04_SETUP"
set -u
export ROS_DOMAIN_ID=40
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
echo "D04_CLI_ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
echo "D04_CLI_DISCOVERY_RANGE=$ROS_AUTOMATIC_DISCOVERY_RANGE"

if ! command -v ros2 >/dev/null 2>&1; then
  echo "D04_CLI_ROS2_COMMAND_MISSING"
  exit 2
fi
if ! ros2 pkg prefix yolo_msgs >/dev/null 2>&1; then
  echo "D04_CLI_YOLO_MSGS_PACKAGE_UNAVAILABLE"
  exit 2
fi
if ! ros2 interface show yolo_msgs/msg/DetectionArray >/dev/null 2>&1; then
  echo "D04_CLI_YOLO_MSGS_TYPE_INVALID"
  exit 2
fi
echo "D04_CLI_YOLO_MSGS_TYPE_READY=yolo_msgs/msg/DetectionArray"

if [[ "$MODE" == "--doctor" ]]; then
  echo "D04_CLI_LIVE_DATA=NOT_CHECKED"
  echo "D04_CLI_DOCTOR_PASS=OVERLAY_ONLY"
  exit 0
fi

# Query live topics only while the owner wrapper is in GUI_DEMO_HOLD.
if ! LIST="$(timeout 8s ros2 topic list -t 2>&1)"; then
  echo "D04_CLI_TOPIC_LIST_UNAVAILABLE=$LIST"
  echo "D04_CLI_LIVE_OBSERVATION=UNAVAILABLE"
  exit 3
fi
if ! grep -qF '/camera/image_raw [' <<< "$LIST" || \
   ! grep -qF '/yolo/cam0/detections [' <<< "$LIST"; then
  echo "D04_CLI_TOPIC_LIST_MISSING_CAMERA_OR_DETECTION"
  echo "D04_CLI_LIVE_OBSERVATION=UNAVAILABLE"
  echo "D04_CLI_HINT=check_owner_gui_hold_or_lifecycle"
  exit 3
fi

check_endpoint() {
  local topic="$1" label="$2" answer="" found=0 attempt
  for attempt in 1 2 3; do
    if answer="$(timeout 7s ros2 topic info -v "$topic" 2>&1)" && \
       grep -Eq 'Publisher count: [1-9][0-9]*' <<< "$answer"; then
      found=1
      break
    fi
    echo "D04_CLI_$label"_TOPIC_INFO_RETRY="$attempt"
    [[ "$attempt" == 3 ]] || sleep 1
  done
  if ((found == 0)); then
    echo "D04_CLI_$label"_PUBLISHER_UNVERIFIED
    return 1
  fi
  echo "D04_CLI_$label"_PUBLISHER_PRESENT
}
if ! check_endpoint /camera/image_raw CAMERA; then
  echo "D04_CLI_LIVE_OBSERVATION=UNAVAILABLE"
  exit 3
fi
if ! check_endpoint /yolo/cam0/detections DETECTION; then
  echo "D04_CLI_LIVE_OBSERVATION=UNAVAILABLE"
  exit 3
fi

check_rate() {
  local topic="$1" label="$2" answer="" rc=0
  answer="$(timeout 8s ros2 topic hz "$topic" 2>&1)" || rc=$?
  # timeout 124 is fine if the command observed actual samples.
  if grep -q 'average rate:' <<< "$answer"; then
    echo "D04_CLI_$label"_RATE_OBSERVED
    grep 'average rate:' <<< "$answer" | tail -n 1
  else
    echo "D04_CLI_$label"_NO_RATE_SAMPLE="rc=$rc"
    echo "$answer" | tail -n 2
    return 1
  fi
}
if ! check_rate /camera/image_raw CAMERA; then
  echo "D04_CLI_LIVE_OBSERVATION=UNAVAILABLE"
  exit 3
fi
if ! check_rate /yolo/cam0/detections DETECTION; then
  echo "D04_CLI_LIVE_OBSERVATION=UNAVAILABLE"
  exit 3
fi

echo "D04_CLI_LIVE_OBSERVATION=PASS_CLI_SAMPLING_ONLY"
echo "D04_CLI_SAFETY_TTL_AND_SHUTDOWN=NOT_CHECKED"
