#!/usr/bin/env bash
# One bounded GPU A/B experiment, exactly 1 NO_GOAL session per adapter.
set -Eeuo pipefail
umask 077
MODE=--compare
if [[ $# -gt 0 ]]; then MODE="$1";fi
[[ $# -le 1 && ( "$MODE" == --compare || "$MODE" == --nvidia-only || "$MODE" == --self-check ) ]] || exit 2
# Reuse the D08 Owner-proven NVIDIA WSLg profile as one isolated
# NO_GOAL diagnostic; do not repeat the historically failed Intel run.
adapters=(NVIDIA Intel)
if [[ "$MODE" == --nvidia-only ]];then
  adapters=(NVIDIA)
  echo 'D06_GPU_RTF_NVIDIA_ONLY_NO_GOAL OWNER_L3_NOT_ACCEPTED'
fi
readonly OWNER_SHA='b711562c4c7f4c229b6a4079f74c3a912ca8b5e7'
readonly OWNER_BLOB='3ec8925d13e9357ffeb45e3d75e5f862b54e931a'
readonly ANALYZER_SHA='615bcd81b8f74a478daa2baeaf9f27ca02c94f11'
readonly ANALYZER_BLOB='171aad7ce8abe97c93a42f19787042619c06b65e'
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
for gpu in "${adapters[@]}";do
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
for gpu in "${adapters[@]}";do
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
  if grep -Eiq 'exit code -11|SIGSEGV|Segmentation fault|Traceback' "$RUN_DIR/$lc.launch.log";then
    echo "D06_GPU_RTF_NATIVE_SHUTDOWN_SEGV_HOLD=$gpu" >&2
    if [[ "$gpu" == NVIDIA ]];then
      echo D06_GPU_RTF_NVIDIA_SHUTDOWN_CRASH_ABORT_SECOND_RUN >&2
    fi
    exit 3
  fi
done
# A single NVIDIA session tests only the D08-proven adapter choice.
# It does NOT prove Intel-vs-NVIDIA causality, CM120/Guard150 or Moving L3.
if [[ "$MODE" == --nvidia-only ]];then
  python3 - "$RUN_DIR/nvidia.g07_wslg_sensor_truth.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
m=r.get('metrics',{})
raw=m.get('raw',{})
safety=m.get('safety',{})
rtf=r.get('rtf_diagnostics',{})
checks={
 'no_goal':r.get('goal_sent') is False and r.get('fixture_moved') is False,
 'source_clock_rtf_measured':isinstance(rtf.get('ros_clock_rtf'),(float,int)) and rtf['ros_clock_rtf']>0,
 'raw_300ms':0 < raw.get('max_receipt_gap_sec',999) <= .3,
 'safety_300ms':0 < safety.get('max_receipt_gap_sec',999) <= .3,
 'front_clear':safety.get('front_median_m',0)>.75,
 'side_clear':safety.get('side_median_m',0)>1.20,
 'every_safety_scan_clear':safety.get('count',0)>=20 and safety.get('count')==safety.get('clear_count'),
 'native_report_candidate':r.get('status')=='NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE',
}
print('D06_GPU_RTF_NVIDIA_ONLY_FIRST_BLOCK='+next((k for k,v in checks.items() if not v),'NONE'))
print('D06_GPU_RTF_NVIDIA_ONLY_NO_GOAL_CHECKS='+json.dumps(checks,sort_keys=True))
print('D06_GPU_RTF_NVIDIA_SENSOR_CANDIDATE_NOT_ACCEPTED')
if not all(checks.values()):raise SystemExit(3)
PY
  echo "D06_GPU_RTF_NVIDIA_NO_GOAL_EVIDENCE=$RUN_DIR"
  echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
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
