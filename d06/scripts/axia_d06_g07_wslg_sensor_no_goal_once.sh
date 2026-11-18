#!/usr/bin/env bash
# Public read-only WSLg sensor TRUTH diagnostic — never authorizes a Goal.
set -Eeuo pipefail
umask 077
MODE="${1:---run}"
[[ $# -le 1 && ( "$MODE" == --run || "$MODE" == --self-check ) ]] || {
  echo 'D06_WSLG_SENSOR_USAGE=--self-check|--run' >&2;exit 2;
}
readonly STUDENT_SHA='41e77f1aa187abf041c1fd839c117e25d934bd8e'
readonly PROBE_BLOB='15938b98f56a512e50ad75ece3ef0317494dd472'
readonly SMOKE_BLOB='48203661d92b92517f5ea44f4a0b14cc26b24630'
readonly LAUNCH_BLOB='b2886cdf509d99ea62528cd013669258764b05e0'
readonly REPO='https://github.com/silverbjin/axia-robot-safety-student.git'
readonly REL='block_B/day07/h01_runtime'

if [[ "$MODE" == --self-check ]];then
  echo "AXIA_D06_G07_WSLG_NO_GOAL_STATIC_PASS student=$STUDENT_SHA NO_ROS_NO_GAZEBO_NO_GOAL"
  echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
[[ "${GITHUB_ACTIONS:-}" != true && -n "${DISPLAY:-}" ]] || {
  echo 'D06_WSLG_NO_GOAL_REAL_OWNER_WSLG_REQUIRED' >&2;exit 3;
}
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo 'D06_WSLG_NO_GOAL_REAL_WSL2_REQUIRED' >&2;exit 3;
}
[[ "${LIBGL_ALWAYS_SOFTWARE:-0}" != 1 ]] || {
  echo 'D06_WSLG_SOFTWARE_RENDERER_OVERRIDE_DENIED' >&2;exit 3;
}
for flag in AXIA_G07_CI_SIM_GOAL_ALLOWED AXIA_G07_TASK04_OWNER_MOVING_L3 \
  AXIA_G07_TASK04_CI_GUI_MOVING AXIA_P3_S01_CI_GOAL_ALLOWED \
  AXIA_P3_S03_CI_COMPOUND_ALLOWED AXIA_P3_S04_CI_PNU_ALLOWED \
  AXIA_P3_S05_CI_GOAL_ALLOWED AXIA_FAULT_INJECTION_ENABLED;do
  [[ "${!flag:-0}" != 1 ]] || {
    echo "D06_WSLG_NO_GOAL_MOTION_AUTHORITY_DENIED=$flag" >&2;exit 3;
  }
done
for exe in git bash python3 glxinfo xwininfo sha256sum tar timeout;do
  command -v "$exe" >/dev/null || {
    echo "D06_WSLG_MISSING_EXECUTABLE=$exe" >&2;exit 3;
  }
done
[[ -r /opt/ros/jazzy/setup.bash ]] || { echo 'D06_WSLG_ROS_JAZZY_MISSING';exit 3; }
set +u
source /opt/ros/jazzy/setup.bash
set -u
[[ "${ROS_DISTRO:-}" == jazzy ]] || { echo 'D06_WSLG_ROS_DISTRO_MISMATCH';exit 3; }
# Fresh WSL2 shells may not have ros2/rviz2 in PATH until Jazzy is sourced.
for exe in ros2 gz rviz2 colcon;do
  command -v "$exe" >/dev/null || {
    echo "D06_WSLG_MISSING_EXECUTABLE_AFTER_JAZZY_SOURCE=$exe" >&2;exit 3;
  }
done

EVIDENCE_ROOT="${AXIA_D06_SENSOR_EVIDENCE_ROOT:-$HOME/axia_d06_g07_sensor_no_goal_evidence}"
mkdir -p "$EVIDENCE_ROOT"
chmod 700 "$EVIDENCE_ROOT"
EVIDENCE_ROOT="$(cd "$EVIDENCE_ROOT" && pwd -P)"
RUN_DIR="$(mktemp -d -p "$EVIDENCE_ROOT" d06-wslg-sensor-XXXXXXXX)"
GIT_ROOT="$(mktemp -d)"
cleanup(){ rm -rf -- "$GIT_ROOT"; }
trap cleanup EXIT
{
  glxinfo -B
  printf 'REQUESTED_MESA_D3D12_ADAPTER=%s\n' "${MESA_D3D12_DEFAULT_ADAPTER_NAME:-INHERITED_DEFAULT}"
} > "$RUN_DIR/renderer.txt" 2>&1 || {
  echo 'D06_WSLG_RENDERER_DIAG_BLOCKED_NO_GOAL' >&2;exit 3;
}
git clone --quiet --no-checkout --filter=blob:none "$REPO" "$GIT_ROOT/student"
git -C "$GIT_ROOT/student" fetch --quiet --depth=1 origin "$STUDENT_SHA"
git -C "$GIT_ROOT/student" checkout --quiet --detach "$STUDENT_SHA"
[[ "$(git -C "$GIT_ROOT/student" rev-parse HEAD)" == "$STUDENT_SHA" ]] || {
  echo 'D06_WSLG_EXACT_STUDENT_SHA_MISMATCH_NO_GOAL' >&2;exit 3;
}
RUNTIME="$GIT_ROOT/student/$REL"
[[ "$(git hash-object "$RUNTIME/tools/g07_wslg_no_goal_sensor_probe.py")" == "$PROBE_BLOB"
   && "$(git hash-object "$RUNTIME/scripts/p2_no_goal_smoke_ci.sh")" == "$SMOKE_BLOB"
   && "$(git hash-object "$RUNTIME/ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p2.launch.py")" == "$LAUNCH_BLOB" ]] || {
  echo 'D06_WSLG_FROZEN_SOURCE_BLOB_MISMATCH_NO_GOAL' >&2;exit 3;
}
bash -n "$RUNTIME/scripts/p2_no_goal_smoke_ci.sh"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-58}"
[[ "$ROS_DOMAIN_ID" =~ ^[0-9]+$ && "$ROS_DOMAIN_ID" -ge 1 && "$ROS_DOMAIN_ID" -le 101 ]] || {
  echo 'D06_WSLG_ROS_DOMAIN_INVALID_NO_GOAL' >&2;exit 3;
}
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_PARTITION="axia_p2_wslg_sensor_${ROS_DOMAIN_ID}_$$_$(date +%s)"
export AXIA_P0_SIM_ONLY=1
export AXIA_G07_OWNER_STARTUP_PARITY=1
export AXIA_P2_G07_PHYSICAL_PREFLIGHT=1
export AXIA_P2_G07_RELOCATED_OBSTACLE=1
export AXIA_G07_OWNER_SENSOR_TRUTH_NO_GOAL=1
export AXIA_G07_CI_SIM_GOAL_ALLOWED=0
export AXIA_G07_TASK04_OWNER_MOVING_L3=0
export AXIA_G07_TASK04_CI_GUI_MOVING=0
export AXIA_G07_CI_OWNER_BAG_PARITY=0
export AXIA_G07_TASK02_SIMPLE_TF_CANDIDATE=0
export AXIA_D07_H01_GUI_NO_GOAL=0
# Never inherit the historical CI-only Owner kernel parity or ECM witness
# switches from a previous terminal. This run has no Goal/CM override.
export AXIA_P2_G07_OWNER_PARITY_CHECK=0
export AXIA_G07_CI_SENSOR_TRUTH_NO_GOAL=0
export AXIA_G07_TASK03_ECM_WITNESS=0
export AXIA_P2_SMOKE_RESULTS="$RUN_DIR/native"
export AXIA_WSLG_SENSOR_PROBE_DURATION_SEC="${AXIA_WSLG_SENSOR_PROBE_DURATION_SEC:-20}"
echo "AXIA_D06_G07_WSLG_NO_GOAL_SOURCE_PIN_VERIFIED=$STUDENT_SHA"
echo "AXIA_D06_G07_WSLG_NO_GOAL_REAL_SENSOR_BEGIN renderer=$(grep -m1 'OpenGL renderer' "$RUN_DIR/renderer.txt" || true)"
printf 'D06_SENSOR_PROBE_OWNER_MOVING=false\nD06_SENSOR_PROBE_SOURCE=%s\n' "$STUDENT_SHA" > "$RUN_DIR/source_manifest.txt"

RC=0
bash "$RUNTIME/scripts/p2_no_goal_smoke_ci.sh" > "$RUN_DIR/owner_no_goal.log" 2>&1 || RC=$?
grep -E 'G07_WSLG_NO_GOAL_SENSOR_|AXIA_G07_WSLG_NO_GOAL_SENSOR_TRUTH|P2_NO_GOAL_BLOCKED|P2_STAGED_NO_GOAL_BLOCKED' "$RUN_DIR/owner_no_goal.log" | tail -n 16 || true
tar -C "$EVIDENCE_ROOT" -czf "$RUN_DIR.tar.gz" "$(basename "$RUN_DIR")"
sha256sum "$RUN_DIR.tar.gz" > "$RUN_DIR.tar.gz.sha256"
echo "D06_WSLG_NO_GOAL_RAW_ARCHIVE=$RUN_DIR.tar.gz"
echo "D06_WSLG_NO_GOAL_RAW_SHA256=$RUN_DIR.tar.gz.sha256"
echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
if [[ "$RC" -ne 0 ]];then
  echo "D06_WSLG_NO_GOAL_SENSOR_HOLD_NATIVE_RC_$RC"
  exit 3
fi
echo 'D06_WSLG_NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE_OWNER_GOAL_NOT_RUN'
exit 0
