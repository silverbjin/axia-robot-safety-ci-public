#!/usr/bin/env bash
# Public read-only WSLg sensor TRUTH diagnostic — never authorizes a Goal.
set -Eeuo pipefail
umask 077
MODE="${1:---run}"
[[ $# -le 1 && ( "$MODE" == --run || "$MODE" == --self-check ) ]] || {
  echo 'D06_WSLG_SENSOR_USAGE=--self-check|--run' >&2;exit 2;
}
readonly STUDENT_SHA='8e19742fd7bd80db73a37dc7b1d798768dc33e2a'
readonly PROBE_BLOB='cb38a2b288b9bf9db80def7b1fe37d975db2cdfa'
readonly SMOKE_BLOB='9cb5baf6c766a79cf6fd5134707981e32bb23e85'
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
cleanup(){
  # NO_GOAL read-only probes owned by this wrapper on any early failure.
  if [[ -n "${SMOKE_PID:-}" ]] && kill -0 "$SMOKE_PID" 2>/dev/null;then
    kill -TERM "$SMOKE_PID" 2>/dev/null || true
    wait "$SMOKE_PID" 2>/dev/null || true
  fi
  local owned
  for owned in "${RX_PID:-}" "${GZ_PID:-}";do
    [[ -n "$owned" ]] || continue
    kill -TERM "$owned" 2>/dev/null || true
    wait "$owned" 2>/dev/null || true
  done
  rm -rf -- "$GIT_ROOT"
}
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
# Official Nav2 Lifecycle Manager cleanly shuts down CM before launch SIGINT;
# preserve any earlier sensor TTL FAIL and require real CM process exit0.
export AXIA_G07_NO_GOAL_ORDERED_SHUTDOWN=1
# Gazebo 8 documented WorldControl pause before launch SIGINT.
# Never changes Scan300/CM120/Guard150 limits or authorizes Goal.
export AXIA_G07_NO_GOAL_GZ_PAUSE_BEFORE_SIGINT=1
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

# Opt-in same-session Gazebo native -> ROS read-only Scan receipt witness.
# Reuses D08 transport tool unchanged. No Goal, Twist, or TTL alteration.
RX_WITNESS="${AXIA_D06_G07_RX_WITNESS:-0}"
[[ "$RX_WITNESS" == 0 || "$RX_WITNESS" == 1 ]] || exit 3
RX_PID=''; GZ_PID=''
RX_TOOL=''; GZ_TOOL=''
if [[ "$RX_WITNESS" == 1 ]];then
  command -v curl >/dev/null || { echo D06_G07_RX_CURL_REQUIRED_NO_GOAL >&2;exit 3; }
  /usr/bin/python3 - <<'PY' || { echo D06_G07_NATIVE_PROBE_IMPORT_MISSING_NO_GOAL >&2;exit 3; }
from gz.transport13 import Node
from gz.msgs10.laserscan_pb2 import LaserScan
from gz.msgs10.clock_pb2 import Clock
PY
  # Exact D08 and D06 immutable commits and git blobs.
  D06_GZ_SAFE_RECEIVER_SHA='7b4b6b553d13c07dd8fc60f4f9a065500cf1cb9a'
  D06_GZ_SAFE_RECEIVER_BLOB='653ec644e80eb832f32c4db6ed46a5a0db02b60d'
  D06_RECEIVER_SHA='baf2ee907757ff248e45a9f02e62b40de40a3aed'
  D06_RECEIVER_BLOB='d55bce65cefe41ea046503445511b68e916607c2'
  RX_TOOL="$GIT_ROOT/d06_g07_scan_rx_witness.py"
  GZ_TOOL="$GIT_ROOT/d06_gz_native_scan_probe_safe.py"
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$D06_RECEIVER_SHA/d06/tools/d06_g07_scan_rx_witness.py" \
    -o "$RX_TOOL"
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$D06_GZ_SAFE_RECEIVER_SHA/d06/tools/d06_gz_native_scan_probe_safe.py" \
    -o "$GZ_TOOL"
  [[ "$(git hash-object "$RX_TOOL")" == "$D06_RECEIVER_BLOB" &&
     "$(git hash-object "$GZ_TOOL")" == "$D06_GZ_SAFE_RECEIVER_BLOB" ]] || {
       echo D06_G07_NATIVE_RX_BLOB_MISMATCH_NO_GOAL >&2;exit 3;
     }
  python3 -m py_compile "$RX_TOOL" "$GZ_TOOL"
  mkdir -p "$RUN_DIR/native"
  /usr/bin/python3 -u "$GZ_TOOL" --topic /scan \
    --out "$RUN_DIR/native/d06_gz_scan_receipts.jsonl" \
    --clock-out "$RUN_DIR/native/d06_gz_clock_receipts.jsonl" \
    > "$RUN_DIR/native/d06_gz_scan_rx.log" 2>&1 &
  GZ_PID=$!
  /usr/bin/python3 -u "$RX_TOOL" --capture \
    --ros-jsonl "$RUN_DIR/native/d06_ros_scan_receipts.jsonl" \
    --output "$RUN_DIR/native/d06_ros_rx_unused.json" \
    > "$RUN_DIR/native/d06_ros_scan_rx.log" 2>&1 &
  RX_PID=$!
  sleep 2
  kill -0 "$RX_PID" "$GZ_PID" 2>/dev/null || {
    echo D06_G07_NATIVE_RX_WITNESS_DIED_BEFORE_SMOKE_NO_GOAL >&2
    kill -TERM "$RX_PID" "$GZ_PID" 2>/dev/null || true
    wait "$RX_PID" "$GZ_PID" 2>/dev/null || true
    exit 3
  }
  echo D06_G07_NATIVE_RX_WITNESS_STARTED_GZ_AND_ROS_NO_GOAL
fi
RC=0
RX_RC=0; GZ_RC=0; HANDOFF_DONE=0; SMOKE_PID=''
if [[ "$RX_WITNESS" == 1 ]];then
  # The Student process writes a probe-complete marker after its actual
  # strict 20s dual-Scan verdict, then WAITS for observers to stop before
  # it requests the official Nav2 lifecycle shutdown.
  export AXIA_G07_NO_GOAL_WITNESS_HANDOFF=1
  bash "$RUNTIME/scripts/p2_no_goal_smoke_ci.sh" > "$RUN_DIR/owner_no_goal.log" 2>&1 &
  SMOKE_PID=$!
  while kill -0 "$SMOKE_PID" 2>/dev/null;do
    if [[ -f "$RUN_DIR/native/g07_witness_probe_complete.signal" ]];then
      kill -TERM "$RX_PID" "$GZ_PID" 2>/dev/null || true
      wait "$RX_PID" || RX_RC=$?
      wait "$GZ_PID" || GZ_RC=$?
      RX_PID='';GZ_PID=''
      if [[ "$RX_RC" == 0 && "$GZ_RC" == 0 ]] &&
         grep -Fq 'D06_GZ_NATIVE_SUBSCRIPTIONS_RELEASED' "$RUN_DIR/native/d06_gz_scan_rx.log";then
        echo 'D06_GZ_NATIVE_RX_UNSUBSCRIBE_BEFORE_NAV2_SHUTDOWN_PASS'
        echo 'G07_READONLY_WITNESSES_STOPPED' > "$RUN_DIR/native/g07_witness_stopped.ack"
        HANDOFF_DONE=1
        echo 'D06_G07_WSLG_READONLY_WITNESS_HANDOFF_DONE_BEFORE_SHUTDOWN'
      else
        echo 'D06_G07_WSLG_WITNESS_NONCLEAN_HANDOFF_HOLD' >&2
        RC=3
      fi
      break
    fi
    sleep .2
  done
  wait "$SMOKE_PID" || RC=3
  SMOKE_PID=''
  if [[ "$HANDOFF_DONE" != 1 ]];then
    if [[ -n "$RX_PID" ]];then
      kill -TERM "$RX_PID" "$GZ_PID" 2>/dev/null || true
      wait "$RX_PID" || RX_RC=$?
      wait "$GZ_PID" || GZ_RC=$?
      RX_PID='';GZ_PID=''
    fi
    echo 'D06_G07_WSLG_WITNESS_HANDOFF_MISSING_HOLD' >&2
    RC=3
  fi
else
  export AXIA_G07_NO_GOAL_WITNESS_HANDOFF=0
  bash "$RUNTIME/scripts/p2_no_goal_smoke_ci.sh" > "$RUN_DIR/owner_no_goal.log" 2>&1 || RC=$?
fi
if [[ "$RX_WITNESS" == 1 ]];then
  echo "D06_G07_RX_WITNESS_EXIT ros=$RX_RC native=$GZ_RC"
  if [[ "$RX_RC" != 0 || "$GZ_RC" != 0 ]];then
    echo D06_G07_RX_WITNESS_DID_NOT_FINISH_CLEANLY_NO_GOAL >&2
    RC=3
  fi
  if ! /usr/bin/python3 "$RX_TOOL" --analyze \
      --ros-jsonl "$RUN_DIR/native/d06_ros_scan_receipts.jsonl" \
      --native-jsonl "$RUN_DIR/native/d06_gz_scan_receipts.jsonl" \
      --native-clock-jsonl "$RUN_DIR/native/d06_gz_clock_receipts.jsonl" \
      --startup-verdict "$RUN_DIR/native/startup_verdict.json" \
      --student-truth "$RUN_DIR/native/g07_wslg_sensor_truth.json" \
      --output "$RUN_DIR/native/d06_g07_scan_delivery_layer.json" \
      > "$RUN_DIR/native/d06_g07_scan_delivery_layer.log" 2>&1;then
    echo D06_G07_NATIVE_SCAN_LAYER_NOT_MEASURED_NO_GOAL >&2
    RC=3
  fi
  cat "$RUN_DIR/native/d06_g07_scan_delivery_layer.log" || true
fi
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
