#!/usr/bin/env bash
# One bounded GPU A/B experiment, exactly 1 NO_GOAL session per adapter.
set -Eeuo pipefail
umask 077
MODE=--compare
if [[ $# -gt 0 ]]; then MODE="$1";fi
[[ $# -le 1 && ( "$MODE" == --compare || "$MODE" == --self-check ) ]] || exit 2
readonly OWNER_SHA='b711562c4c7f4c229b6a4079f74c3a912ca8b5e7'
readonly OWNER_BLOB='3ec8925d13e9357ffeb45e3d75e5f862b54e931a'
readonly ANALYZER_SHA='8875a02d53dee1e4346e20680b77b252e24d9ee7'
readonly ANALYZER_BLOB='9314fd4c8f5354d82cbcb43ad43fcbc371197f61'
readonly STUDENT_SHA='e4c2007064bec2103bb743bd27cdbdf0955961b7'
echo "AXIA_D06_GPU_RTF_PINNED_STUDENT=$STUDENT_SHA NO_GOAL_ONLY"
if [[ "$MODE" == --self-check ]];then
  echo 'D06_GPU_RTF_STATIC_PASS NO_ROS_NO_GAZEBO_NO_GOAL'
  echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
[[ -n "$(printenv DISPLAY || :)" && "$(printenv GITHUB_ACTIONS || :)" != true ]] || {
  echo D06_GPU_RTF_REAL_WSLG_REQUIRED >&2;exit 3;
}
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || exit 3
for cmd in curl git python3 glxinfo tar sha256sum cmp;do
  command -v "$cmd" >/dev/null || { echo "MISSING_EXECUTABLE=$cmd" >&2;exit 3; }
done
ROOT="$HOME/axia_d06_g07_gpu_rtf_evidence"
mkdir -p "$ROOT";chmod 700 "$ROOT"
ROOT="$(cd "$ROOT" && pwd -P)"
RUN_DIR="$(mktemp -d -p "$ROOT" ab-no-goal-XXXXXXXX)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
# Preflight *actual* GPU selection before ever launching a robot.
for gpu in NVIDIA Intel;do
  MESA_D3D12_DEFAULT_ADAPTER_NAME="$gpu" glxinfo -B > "$RUN_DIR/$gpu.preflight.txt"
  grep -Ei "OpenGL renderer string:.*D3D12.*$gpu" "$RUN_DIR/$gpu.preflight.txt" >/dev/null || {
    echo "D06_GPU_RTF_D3D12_$gpu_UNAVAILABLE_NO_GOAL" >&2;exit 3;
  }
done
URL="https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public"
curl -fLsS --retry 3 --max-time 90 "$URL/$OWNER_SHA/d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh" -o "$TMP/owner.sh"
curl -fLsS --retry 3 --max-time 90 "$URL/$ANALYZER_SHA/d06/tools/axia_d06_lidar_rtf_compare.py" -o "$TMP/compare.py"
[[ "$(git hash-object "$TMP/owner.sh")" == "$OWNER_BLOB" && "$(git hash-object "$TMP/compare.py")" == "$ANALYZER_BLOB" ]] || {
  echo 'D06_GPU_RTF_SOURCE_BLOB_MISMATCH_NO_GOAL' >&2;exit 3;
}
bash -n "$TMP/owner.sh"
# New NVIDIA first; the historically unsafe Intel is the last session.
for gpu in NVIDIA Intel;do
  if [[ "$gpu" == NVIDIA ]];then lc=nvidia; domain=86;else lc=intel;domain=87;fi
  echo "D06_GPU_RTF_AB_CASE_START=$gpu DOMAIN=$domain GOAL_NOT_SENT"
  rc=0
  MESA_D3D12_DEFAULT_ADAPTER_NAME="$gpu" ROS_DOMAIN_ID="$domain" \
    bash "$TMP/owner.sh" --run > "$RUN_DIR/$lc.run.log" 2>&1 || rc=$?
  [[ "$rc" == 0 || "$rc" == 3 ]] || {
    echo "D06_GPU_RTF_INFRA_FAILURE=$gpu:$rc" >&2;exit 3;
  }
  archive="$(sed -n 's/^D06_WSLG_NO_GOAL_RAW_ARCHIVE=//p' "$RUN_DIR/$lc.run.log" | tail -1)"
  [[ -n "$archive" && -s "$archive" && -s "$archive.sha256" ]] || {
    echo "D06_GPU_RTF_MISSING_SENSOR_EVIDENCE=$gpu" >&2;exit 3;
  }
  sha256sum -c --status "$archive.sha256" || exit 3
  sub="$(basename "$archive" .tar.gz)"
  for item in native/g07_wslg_sensor_truth.json renderer.txt native/g07_world.sdf.xacro native/g07_demo_waffle.sdf.xacro native/initialpose.json native/launch.log;do
    tar -xOf "$archive" "$sub/$item" > "$RUN_DIR/$lc.$(basename "$item")" || exit 3
  done
  grep -Ei "OpenGL renderer string:.*D3D12.*$gpu" "$RUN_DIR/$lc.renderer.txt" >/dev/null || {
    echo "D06_GPU_RTF_ACTUAL_RENDERER_MISMATCH=$gpu" >&2;exit 3;
  }
  python3 - "$RUN_DIR/$lc.g07_wslg_sensor_truth.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]));m=d.get("rtf_diagnostics",{})
assert d["goal_sent"] is False and d["fixture_moved"] is False
assert m.get("ros_clock_rtf") is not None and m["ros_clock_rtf"]>0
print("D06_GPU_RTF_CLOCK_MEASURED",m["ros_clock_rtf"],m["timing_pattern"])
PY
  # Record the actual Gazebo/Ogre2 GL renderer separately from glxinfo:
  # glxinfo describes the WSLg client, NOT conclusive sensor-server GPU use.
  # Filter to minimal render evidence; never assert GPU causation from it.
  if [[ -r "$HOME/.gz/rendering/ogre2.log" ]];then
    grep -Ei 'GL_RENDERER|GL_VENDOR|OpenGL|D3D12' "$HOME/.gz/rendering/ogre2.log" \
      | tail -n 12 > "$RUN_DIR/$lc.ogre2_gl_evidence.txt" || true
  fi
  echo "D06_GPU_RTF_AB_CASE_FINISHED=$gpu SENSOR_EXIT=$rc NO_GOAL"
  # A fatal shutdown after NVIDIA must not be followed by another session.
  if [[ "$gpu" == NVIDIA ]] && grep -Eiq 'exit code -11|SIGSEGV|Segmentation fault|Traceback' "$RUN_DIR/nvidia.launch.log";then
    echo D06_GPU_RTF_NVIDIA_SHUTDOWN_CRASH_ABORT_SECOND_RUN >&2;exit 3
  fi
done
for stem in g07_world.sdf.xacro g07_demo_waffle.sdf.xacro;do
  cmp -s "$RUN_DIR/intel.$stem" "$RUN_DIR/nvidia.$stem" || {
    echo "D06_GPU_RTF_WORLD_OR_WAFFLE_NOT_IDENTICAL=$stem" >&2;exit 3;
  }
done
# Same frozen initial pose and static occupancy map are required to
# attribute LiDAR geometry changes to renderer condition rather than scene.
python3 - "$RUN_DIR/intel.initialpose.json" "$RUN_DIR/nvidia.initialpose.json" <<'PY'
import json,sys
a,b=[json.load(open(p)) for p in sys.argv[1:]]
assert a["result"]=="POSE_DELIVERY_ACKNOWLEDGED"
assert b["result"]=="POSE_DELIVERY_ACKNOWLEDGED"
assert a["position"]==b["position"]==[-2.0,-0.5,0.0]
assert a["map_meta"]["data_sha256"]==b["map_meta"]["data_sha256"]
print("D06_GPU_RTF_AB_SAME_GAZEBO_WORLD_WAFFLE_INITIALPOSE_AND_MAP_PROVEN_NO_GOAL")
PY
python3 "$TMP/compare.py" \
  --intel-json "$RUN_DIR/intel.g07_wslg_sensor_truth.json" \
  --nvidia-json "$RUN_DIR/nvidia.g07_wslg_sensor_truth.json" \
  --intel-renderer "$RUN_DIR/intel.renderer.txt" \
  --nvidia-renderer "$RUN_DIR/nvidia.renderer.txt" \
  --output "$RUN_DIR/independent_axes_ab.json"
echo "D06_GPU_RTF_AB_REPORT=$RUN_DIR/independent_axes_ab.json"
echo "D06_GPU_RTF_PRIVATE_EVIDENCE=$RUN_DIR"
echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
