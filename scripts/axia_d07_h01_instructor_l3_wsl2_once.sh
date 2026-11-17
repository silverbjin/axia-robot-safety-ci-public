#!/usr/bin/env bash
# D07-H01 instructor WSL2 L3: one field session + evidence custody.
# Reuses the exact PUBLIC student main H01 runtime; no private answer,
# new ROS node, moving Goal, cmd_vel, certified E-Stop, or safety-TTL change.
set -Eeuo pipefail
umask 077
PIN="d1a453d42929bbdc423505adf1b9dd76ad7f5b2b"
REPO="https://github.com/silverbjin/axia-robot-safety-student.git"
MODE="${1:---run}"

verify_evidence() {
  python3 - "$1" "$PIN" <<'PY_VERIFY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1])
pin=sys.argv[2]
fault=[]
def need(cond,reason):
    if not cond: fault.append(reason)
def load(path):
    try: return json.loads(path.read_text())
    except Exception as exc:
        fault.append("MISSING_OR_INVALID_"+path.name+":"+type(exc).__name__)
        return {}
native=root/"native"
geom=load(native/"evidence/d07_h01_geometry/d07_h01_geometry.json")
src=native/"source.txt"
need(src.is_file() and ("student_source_sha="+pin) in src.read_text(),
     "EXACT_PINNED_PUBLIC_SOURCE_NOT_PROVEN")
for key in ("real_nav2","real_laser_scan","actual_costmap_obstacle_observed",
            "obstacle_restored_away"):
    need(geom.get(key) is True,"ORIGINAL_PHYSICAL_"+key+"_NOT_PROVEN")
for key in ("goal_sent","certified_estop","motion_admitted"):
    need(geom.get(key) is False,"UNSAFE_OR_UNVERIFIED_"+key)
# Original baseline has motion_admitted=false, not robot_moved.
# Per-stage read-only evidence independently proves robot_moved=false.
p=native/"evidence/d07_h01_geometry/teaching_cycle_evidence.jsonl"
try: rows=[json.loads(s) for s in p.read_text().splitlines() if s.strip()]
except Exception: rows=[]
expected=["free","intrusion","lateral","restored"]
complete=[]
for start in range(0,len(rows)-3,4):
    four=rows[start:start+4]
    if [r.get("stage") for r in four]!=expected: continue
    if len({r.get("cycle") for r in four})!=1: continue
    good=all(
        r.get("real_native_gazebo_pose_ack") is True
        and r.get("real_scan_stamp",0)>0
        and r.get("real_costmap_stamp",0)>0
        and r.get("official_action")=="ComputePathToPose"
        and r.get("path_frame")=="map"
        and r.get("path_pose_count",0)>=3
        and r.get("rviz_path_subscribers",0)>=1
        and r.get("goal_sent") is False
        and r.get("cmd_vel_sent") is False
        and r.get("robot_moved") is False
        and r.get("certified_estop") is False
        for r in four)
    if good: complete.append(four[0]["cycle"])
need(len(complete)>=2, "TWO_COMPLETE_REAL_PHYSICAL_REPEAT_CYCLES_NOT_PROVEN")
teardown=native/"evidence/teardown.txt"
need(teardown.is_file() and "P2_L2_GRACEFUL_TEARDOWN" in teardown.read_text()
     and "FORCED" not in teardown.read_text(), "CLEAN_NATIVE_TEARDOWN_NOT_PROVEN")
teaching=native/"evidence/d07_h01_teaching_loop.log"
teaching_text=teaching.read_text() if teaching.is_file() else ""
need("D07_H01_TEACHING_CTRL_C_STOP OPERATOR" in teaching_text,
     "OPERATOR_CTRL_C_STOP_NOT_PROVEN")
need("D07_H01_TEACHING_BLOCKED_FIRST_BOUNDARY" not in teaching_text,
     "FIRST_TEACHING_RUNTIME_FAILURE")
windows=root/"windows-gazebo-rviz.txt"
need(windows.is_file() and windows.stat().st_size>0,
     "SAME_SESSION_GAZEBO_RVIZ_WINDOWS_NOT_OBSERVED")
print("D07_H01_L3_PINNED_SOURCE="+pin)
print("D07_H01_L3_COMPLETE_PHYSICAL_CYCLES="+str(len(complete)))
if fault:
    print("AXIA_D07_H01_L3_DATA_VERDICT=HOLD "+",".join(fault))
    print("AXIA_MVP_DEMO_ACCEPTED=HOLD")
    raise SystemExit(3)
print("AXIA_D07_H01_L3_DATA_VERDICT=READY_FOR_OWNER_PIXEL_REVIEW")
print("AXIA_D07_H01_L3_WSLG_PIXELS_AUTOMATICALLY_VERIFIED=false")
print("AXIA_MVP_DEMO_ACCEPTED=HOLD")
PY_VERIFY
}

case "$MODE" in
  --self-check)
    [[ $# -eq 1 ]] || exit 2
    bash -n "$0"
    [[ "$PIN" =~ ^[a-f0-9]{40}$ ]]
    echo "AXIA_D07_H01_INSTRUCTOR_L3_WRAPPER_L0_PASS WSL2_NOT_RUN GAZEBO_NOT_RUN"
    exit 0
    ;;
  --verify)
    [[ $# -eq 2 ]] || exit 2
    verify_evidence "$2"
    exit $?
    ;;
  --run)
    [[ $# -le 1 ]] || exit 2
    ;;
  --rqt)
    [[ $# -eq 1 ]] || exit 2
    [[ -r /opt/ros/jazzy/setup.bash ]] || exit 3
    set +u
    source /opt/ros/jazzy/setup.bash
    set -u
    [[ "${ROS_DISTRO:-}" == jazzy ]] || exit 3
    [[ -n "${DISPLAY:-}" ]] || exit 3
    export ROS_DOMAIN_ID=95
    export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
    echo "AXIA_D07_H01_L3_RQT_INDEPENDENT_TERMINAL ROS_DOMAIN_ID=95"
    exec ros2 run rqt_graph rqt_graph
    ;;
  *)
    echo "USAGE: bash $0 --self-check|--verify EVIDENCE_DIR|--run|--rqt" >&2
    exit 2
    ;;
esac

[[ "${GITHUB_ACTIONS:-}" != true ]] || {
  echo AXIA_D07_H01_L3_REQUIRES_OWNER_WSL2_NOT_PUBLIC_CI >&2
  exit 3
}
[[ -r /opt/ros/jazzy/setup.bash ]] || {
  echo AXIA_D07_H01_L3_JAZZY_MISSING >&2; exit 3;
}
grep -Eqi 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo AXIA_D07_H01_L3_WSL2_REQUIRED >&2; exit 3;
}
[[ -n "${DISPLAY:-}" ]] || {
  echo AXIA_D07_H01_L3_WSLG_DISPLAY_REQUIRED >&2; exit 3;
}
set +u
source /opt/ros/jazzy/setup.bash
set -u
[[ "${ROS_DISTRO:-}" == jazzy ]] || exit 3
for bin in git ros2 gz rviz2 python3 tar sha256sum setsid timeout; do
  command -v "$bin" >/dev/null || {
    echo "AXIA_D07_H01_L3_MISSING_TOOL=$bin" >&2; exit 3;
  }
done
for unsafe in AXIA_G07_CI_SIM_GOAL_ALLOWED AXIA_P3_S01_CI_GOAL_ALLOWED \
              AXIA_P3_S03_CI_COMPOUND_ALLOWED AXIA_P3_S04_CI_PNU_ALLOWED \
              AXIA_P3_S05_CI_GOAL_ALLOWED; do
  [[ "${!unsafe:-0}" != 1 ]] || {
    echo "AXIA_D07_H01_L3_MOVING_GOAL_FLAG_DENIED=$unsafe" >&2; exit 3;
  }
done
PARENT="$HOME/axia_d07_h01_instructor_l3"
mkdir -p "$PARENT"
OUT="$(mktemp -d "$PARENT/session-$(date +%Y%m%d)-XXXXXXXX")"
chmod 700 "$OUT"
SRC="$OUT/source"
WATCH_PID=""
RUN_RC=99
STOP_SIGNAL="NONE"
PHASE="PREFLIGHT"
ARCHIVE="$OUT.tar.gz"

finish() {
  local entry_rc="$1"
  trap - EXIT INT TERM
  set +e
  if [[ -n "$WATCH_PID" ]]; then
    kill "$WATCH_PID" 2>/dev/null || true
    wait "$WATCH_PID" 2>/dev/null || true
  fi
  # rqt_graph is owned by a separate terminal, never killed by this run.
  printf 'phase=%s\nentry_rc=%s\nrunner_rc=%s\noperator_signal=%s\nsource_pin=%s\n' \
    "$PHASE" "$entry_rc" "$RUN_RC" "$STOP_SIGNAL" "$PIN" > "$OUT/exit_status.txt"
  verify_evidence "$OUT" > "$OUT/l3_structural_verdict.txt" 2>&1
  local check_rc=$?
  printf 'verifier_rc=%s\n' "$check_rc" >> "$OUT/exit_status.txt"
  # All owned GUI writers have now exited. Source clone is excluded from
  # archive; the closed real Gazebo/Nav2/ROS evidence and field logs remain.
  (
    cd "$OUT" || exit 1
    find . -path './source' -prune -o -type f ! -name SHA256SUMS -print0 |
      sort -z | xargs -0 -r sha256sum > SHA256SUMS
    sha256sum -c SHA256SUMS > sha256_check.txt
  )
  tar --exclude='./source' -czf "$ARCHIVE" -C "$OUT" .
  sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
  echo "AXIA_D07_H01_L3_EVIDENCE_DIR=$OUT"
  echo "AXIA_D07_H01_L3_EVIDENCE_ARCHIVE=$ARCHIVE"
  echo "AXIA_D07_H01_L3_ARCHIVE_SHA256_FILE=$ARCHIVE.sha256"
  cat "$OUT/l3_structural_verdict.txt"
  echo "AXIA_D07_H01_L3_VISUAL_ACCEPTANCE=HOLD_USER_SCREEN_REVIEW_REQUIRED"
  echo "AXIA_MVP_DEMO_ACCEPTED=HOLD"
  # Preserve runtime failure status, not the data-only HOLD verdict.
  if [[ "$RUN_RC" != 99 && "$RUN_RC" != 0 && "$RUN_RC" != 130 ]]; then
    exit "$RUN_RC"
  fi
  if [[ "$check_rc" -ne 0 ]]; then
    exit "$check_rc"
  fi
  exit "$entry_rc"
}
trap 'finish "$?"' EXIT
trap 'STOP_SIGNAL=INT' INT
trap 'STOP_SIGNAL=TERM; exit 143' TERM

export ROS_DOMAIN_ID=95
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_PARTITION="axia_p2_d07_l3_95_$$_$(date +%s)"
export AXIA_D07_STUDENT_PHASE_HOLD_S=15
export AXIA_D07_STUDENT_LIVE_EVIDENCE="$OUT/native"
export AXIA_G07_CI_SIM_GOAL_ALLOWED=0
unset AXIA_D07_H01_TEACHING_MAX_CYCLES
unset AXIA_D07_H01_CI_SOFTWARE_GUI
echo "AXIA_D07_H01_L3_SOURCE_PIN=$PIN" | tee "$OUT/preflight.log"
echo "ROS_DOMAIN_ID=$ROS_DOMAIN_ID GZ_PARTITION=$GZ_PARTITION DISPLAY=$DISPLAY" >> "$OUT/preflight.log"
if command -v glxinfo >/dev/null; then
  timeout 10s glxinfo -B > "$OUT/gpu_glxinfo.txt" 2>&1 || true
else
  echo "GLXINFO_NOT_INSTALLED_GPU_ACCELERATION_NOT_VERIFIED" > "$OUT/gpu_glxinfo.txt"
fi

PHASE="PINNED_SOURCE_CLONE"
git clone --quiet --no-checkout "$REPO" "$SRC" >> "$OUT/preflight.log" 2>&1
git -C "$SRC" checkout --quiet --detach "$PIN" >> "$OUT/preflight.log" 2>&1
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]] || {
  echo AXIA_D07_H01_L3_SOURCE_MISMATCH >&2;exit 3;
}
RUNNER="$SRC/block_B/day07/run_d07_h01_gazebo_rviz_student_once.sh"
PHASE="STATIC_AND_DOCTOR"
bash "$RUNNER" --self-check >> "$OUT/preflight.log" 2>&1
bash "$RUNNER" --doctor >> "$OUT/preflight.log" 2>&1
echo AXIA_D07_H01_L3_PUBLIC_PIN_AND_DOCTOR_PASS

PHASE="REAL_WSLG_GUI_NO_GOAL"
# Only Gazebo and RViz are run-owned. rqt_graph is launched separately
# from a second terminal using --rqt and remains independently stoppable.
(
  # Window enumeration only; it neither subscribes to ROS nor affects TTL.
  for _ in $(seq 1 210); do
    command -v xwininfo >/dev/null || break
    xwininfo -root -tree > "$OUT/windows-last.txt" 2>/dev/null || true
    if grep -Eiq 'Gazebo' "$OUT/windows-last.txt" &&
       grep -Eiq 'RViz' "$OUT/windows-last.txt"; then
      cp "$OUT/windows-last.txt" "$OUT/windows-gazebo-rviz.txt"
      # Best-effort per-window XWD; still requires owner pixel review.
      if command -v xwd >/dev/null; then
        for app in Gazebo RViz; do
          id="$(grep -im1 "$app" "$OUT/windows-last.txt" | awk '{print $1}')"
          if [[ "$id" =~ ^0x[0-9a-fA-F]+$ ]]; then
            timeout 8s xwd -silent -id "$id" -out "$OUT/window_$app.xwd" \
              2>/dev/null || true
          fi
        done
      fi
      break
    fi
    sleep 3
  done
) &
WATCH_PID=$!

echo "AXIA_D07_H01_L3_RUNNING: Observe Gazebo and RViz; launch rqt_graph manually from a separate terminal."
echo "AXIA_D07_H01_L3_RUNNING: After >=2 full Free/Intrusion/Lateral/Restored cycles, press Ctrl+C ONCE here."
echo "AXIA_D07_H01_L3_RUNNING: Terminal B: source Jazzy; export ROS_DOMAIN_ID=95 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST; ros2 run rqt_graph rqt_graph."
set +e
bash "$RUNNER" --run
RUN_RC=$?
set -e
PHASE="POST_RUNTIME_EVIDENCE"
printf '%s\n' "$RUN_RC" > "$OUT/runner_rc.txt"
echo "AXIA_D07_H01_L3_RUNNER_RC=$RUN_RC (130 may be operator Ctrl+C, never success by itself)"
if [[ "$RUN_RC" != 0 && "$RUN_RC" != 130 ]]; then exit "$RUN_RC"; fi
