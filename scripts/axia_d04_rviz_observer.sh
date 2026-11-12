#!/usr/bin/env bash
# D04 read-only RViz2: GUI observation ONLY. No Goal, no action client, no
# cmd_vel publisher and NO certified E-Stop. Do not modify P1/YOLO sources.
set -Eeuo pipefail
umask 022

MODE="${1:---doctor}"
[[ $# -le 2 ]] || { echo "D04_RVIZ_USAGE=--install <config.rviz>|--doctor|--open|--self-check" >&2; exit 2; }
case "$MODE" in
  --self-check)
    echo "D04_RVIZ_STATIC_PASS ROS_NOT_RUN GAZEBO_NOT_RUN NO_GOAL"
    exit 0 ;;
  --install|--doctor|--open) ;;
  *) echo "D04_RVIZ_USAGE=--install <config.rviz>|--doctor|--open" >&2; exit 2 ;;
esac

USER_DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
SHARE="$USER_DATA/axia-d04/rviz"
CONFIG="$SHARE/axia_d04_robot_state.rviz"
BIN="$HOME/.local/bin/axia-d04-rviz"
DESKTOP="$HOME/Desktop/AXIA-D04-RViz.desktop"
APPLICATIONS="$USER_DATA/applications/AXIA-D04-RViz.desktop"

if [[ "$MODE" == --install ]]; then
  [[ $# -eq 2 && -r "$2" && "$2" == *.rviz ]] || {
    echo "D04_RVIZ_CONFIG_MISSING: provide existing .rviz file" >&2
    exit 2
  }
  mkdir -p "$SHARE" "$HOME/.local/bin" "$HOME/Desktop" "$USER_DATA/applications"
  cp -f -- "$2" "$CONFIG"
  if [[ "$(realpath -- "${BASH_SOURCE[0]}")" != "$(realpath -m -- "$BIN")" ]]; then
    cp -f -- "${BASH_SOURCE[0]}" "$BIN"
  fi
  chmod 755 "$BIN"
  chmod 644 "$CONFIG"
  # Desktop Entry Exec needs a simple absolute path.
  if [[ "$BIN" =~ [[:space:]] ]]; then
    echo "D04_RVIZ_DESKTOP_PATH_CONTAINS_SPACES: use '$BIN --open' in terminal" >&2
    exit 2
  fi
  cat > "$APPLICATIONS" <<DESKTOP_ENTRY
[Desktop Entry]
Type=Application
Version=1.0
Name=AXIA D04 RViz - Robot State
Comment=Read-only D04 RobotModel LaserScan TF RGB YOLO viewer
Exec=$BIN --open
Icon=applications-science
Terminal=false
Categories=Education;Science;
StartupNotify=true
DESKTOP_ENTRY
  cp -f -- "$APPLICATIONS" "$DESKTOP"
  chmod 755 "$APPLICATIONS" "$DESKTOP"
  echo "D04_RVIZ_CONFIG_INSTALLED=$CONFIG"
  echo "D04_RVIZ_DESKTOP_LAUNCHER=$DESKTOP"
  echo "D04_RVIZ_COMMAND=$BIN --open"
  echo "D04_RVIZ_NOTE=click_during_GUI_DEMO_HOLD_only"
  exit 0
fi

ROS_SETUP="${AXIA_D04_RVIZ_ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
YOLO_SETUP="${AXIA_D04_RVIZ_YOLO_SETUP:-$HOME/.cache/axia/d04/yolo_ws_94d2dd500cb26027ee9c019f4d3a02029ac615cc/install/setup.bash}"
D04_SETUP="${AXIA_D04_RVIZ_D04_SETUP:-$HOME/.cache/axia/d04/d04_package_ws_f2edba114dd0540d1f27a1e216bfda2b885c5cb9/install/setup.bash}"
for kind in ROS YOLO D04; do
  case "$kind" in
    ROS) file="$ROS_SETUP" ;;
    YOLO) file="$YOLO_SETUP" ;;
    D04) file="$D04_SETUP" ;;
  esac
  if [[ ! -r "$file" ]]; then
    echo "D04_RVIZ_${kind}_OVERLAY_MISSING=$file"
    echo "D04_RVIZ_READY=NO"
    exit 2
  fi
done
if [[ ! -r "$CONFIG" ]]; then
  echo "D04_RVIZ_CONFIG_MISSING=$CONFIG"
  exit 2
fi

# ROS setup scripts are not guaranteed nounset-clean.
set +u
source "$ROS_SETUP"
source "$YOLO_SETUP"
source "$D04_SETUP"
set -u
export ROS_DOMAIN_ID=40
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
if ! command -v rviz2 >/dev/null 2>&1; then
  echo "D04_RVIZ2_COMMAND_MISSING: install official ros-jazzy-rviz2 on WSL2"
  exit 2
fi
if [[ -z "${DISPLAY:-}" ]]; then
  echo "D04_RVIZ_DISPLAY_MISSING: WSLg GUI DISPLAY required"
  exit 2
fi
echo "D04_RVIZ_DOMAIN=40"
echo "D04_RVIZ_CONFIG=$CONFIG"
echo "D04_RVIZ_READY=OVERLAY_AND_GUI"
if [[ "$MODE" == --doctor ]]; then
  echo "D04_RVIZ_DOCTOR_PASS RVIZ_NOT_LAUNCHED"
  exit 0
fi
echo "D04_RVIZ_VIEWER_START READ_ONLY NO_GOAL NO_CMD_VEL"
exec rviz2 -d "$CONFIG" --ros-args -p use_sim_time:=true
