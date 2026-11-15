#!/usr/bin/env bash
# D06 WSL2 classroom: P4 G11 PINNED Owner real G07 + read-only RViz2.
# SIM ONLY, SINGLE MANUAL TTY GOAL. Never changes safety TTL or Guard.
set -Eeuo pipefail
umask 077
readonly P4_PUBLIC_RELEASE_SHA="${AXIA_G07_CYCLE16_PUBLIC_RELEASE_SHA:-}"
readonly P4_OWNER_PRIVATE_SHA='01d45d46b6eb6a05b1bd313d73f1fc3549575545'
readonly P4_OWNER_PRIVATE_TREE='38de92dda3c17221b337f140bbc1b2aecd805da4'
readonly P4_G11_SCRIPT='scripts/axia_g07_cycle16_p4_owner_once.sh'
# The G11 owner release itself sets AXIA_P2_OWNER_PINNED_SHA and collects
# YES-P2-G07-GOAL on a physical TTY. No AXIA_G07_CI_SIM_GOAL_ALLOWED override.
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
SIDECAR="$ROOT/d06/scripts/d06_rviz_sidecar.sh"
MONITOR="$ROOT/d06/live/d06_readonly_monitor.py"
TRIAGE="$ROOT/d06/live/d06_g07_field_triage.py"
GUI_CPU_SELECTOR="$ROOT/d06/live/d06_gui_cpu_plan.py"
FIRST_CM_JOIN="$ROOT/d06/live/d06_guard_cm_first_latch_join.py"
BUNDLE_COLLECTOR="$ROOT/d06/live/g07_owner_evidence_bundle.py"
RVIZ_CONFIG="$ROOT/d06/rviz/d06_safety_bubble.rviz"

self_check() {
  for p in "$ROOT/d06/scripts/g07_shared_gui_clients.sh" "$SIDECAR" "$MONITOR" "$TRIAGE" "$RVIZ_CONFIG" "$GUI_CPU_SELECTOR" "$FIRST_CM_JOIN" "$ROOT/d06/live/g07_cycle16_owner_ci_gate_v4.py" "$BUNDLE_COLLECTOR" "$ROOT/d06/acceptance/g07_cycle16_owner_ci_gate_v3.json"; do
    [[ -s "$p" ]] || { echo "D06_STATIC_BLOCKED_FILE_MISSING=$p";return 2; }
  done
  bash -n "$SIDECAR"
  bash -n "$ROOT/d06/scripts/g07_shared_gui_clients.sh"
  /usr/bin/python3 "$ROOT/d06/live/g07_cycle16_owner_ci_gate_v4.py" --gate "$ROOT/d06/acceptance/g07_cycle16_owner_ci_gate_v3.json" --private-sha "$P4_OWNER_PRIVATE_SHA" --ci-run 43727149856 --private-tree "$P4_OWNER_PRIVATE_TREE"
  /usr/bin/python3 -m py_compile "$MONITOR" "$TRIAGE" "$GUI_CPU_SELECTOR" "$FIRST_CM_JOIN"
  [[ "$P4_OWNER_PRIVATE_SHA" =~ ^[0-9a-f]{40}$ &&
     "$P4_OWNER_PRIVATE_TREE" =~ ^[0-9a-f]{40}$ ]] || return 2
  echo "D06_OWNER_RVIZ_STATIC_PASS private_p4_g07_sha=$P4_OWNER_PRIVATE_SHA GAZEBO_NOT_RUN RVIZ_NOT_RUN"
}
if [[ "$#" -eq 1 && "$1" == --self-check ]];then
  self_check;exit $?
fi
if [[ "$#" -eq 1 && "$1" == --admission-check ]];then
  /usr/bin/python3 "$ROOT/d06/live/g07_cycle16_owner_ci_gate_v4.py" \
    --gate "$ROOT/d06/acceptance/g07_cycle16_owner_ci_gate_v3.json" \
    --private-sha "$P4_OWNER_PRIVATE_SHA" --ci-run 43727149856 --private-tree "$P4_OWNER_PRIVATE_TREE"
  exit $?
fi
[[ "$#" -eq 0 ]] || { echo 'D06_USAGE --self-check or no arguments' >&2;exit 2; }
# Admission receipt is source-locked to this exact public checkout. Fail
# BEFORE private download, ROS startup, TTY consent or any real Goal.
# The receipt is NOT an Owner acceptance verdict; only CI preflight admission.
GATE="$ROOT/d06/acceptance/g07_cycle16_owner_ci_gate_v3.json"
GATE_VERIFY="$ROOT/d06/live/g07_cycle16_owner_ci_gate_v4.py"
if ! /usr/bin/python3 "$GATE_VERIFY" --gate "$GATE" --private-sha "$P4_OWNER_PRIVATE_SHA" --ci-run 43727149856 --private-tree "$P4_OWNER_PRIVATE_TREE";then
  echo 'AXIA_G07_FINAL_OWNER_BLOCKED_CI_GUI_L2_OR_PIN_MISMATCH_NO_ROS_NO_GOAL'
  exit 3
fi
echo 'ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY previous_Gazebo_RViz_Xvfb_L2_passed actual_WSLg_not_run'
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'AXIA_G07_FINAL_OWNER_TTY_REQUIRED_NO_ROS_NO_GOAL' >&2;exit 2;
}
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || {
  echo 'D06_BLOCKED_UBUNTU_24_04_REQUIRED';exit 2;
}
grep -qiE '(microsoft|wsl)' /proc/sys/kernel/osrelease || {
  echo 'D06_BLOCKED_WSL2_REQUIRED';exit 2;
}
[[ -f /opt/ros/jazzy/setup.bash && -n "${DISPLAY:-}" ]] || {
  echo 'D06_BLOCKED_ROS_JAZZY_OR_WSLG_DISPLAY_MISSING';exit 2;
}
for c in git gh bash ros2 gz colcon setsid taskset timeout python3;do
  command -v "$c" >/dev/null || { echo "D06_BLOCKED_MISSING_CMD=$c";exit 2; }
done
gh auth status >/dev/null 2>&1 || {
  echo 'D06_BLOCKED_GITHUB_PRIVATE_AUTH';exit 2;
}
set +u
source /opt/ros/jazzy/setup.bash
set -u
if ! command -v rviz2 >/dev/null 2>&1;then
  echo 'D06_INSTALL_OFFICIAL_RVIZ_ONLY'
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    ros-jazzy-rviz2 ros-jazzy-visualization-msgs ros-jazzy-nav-msgs ros-jazzy-nav2-msgs
fi
for p in rviz2 visualization_msgs nav_msgs nav2_msgs;do
  ros2 pkg prefix "$p" >/dev/null || {
    echo "D06_BLOCKED_OFFICIAL_PACKAGE=$p";exit 2;
  }
done
self_check
OUT="$(mktemp -d "$HOME/axia_d06_gazebo_rviz_owner_XXXXXXXX")"
chmod 700 "$OUT"
MARKER="$OUT/owner-start.marker"
SIDECAR_PID=''
OWNER_RC=125
cleanup() {
  rc=$?
  trap - EXIT INT TERM
  set +e
  if [[ "$SIDECAR_PID" =~ ^[0-9]+$ ]];then
    kill -TERM "$SIDECAR_PID" 2>/dev/null || true
    wait "$SIDECAR_PID" 2>/dev/null || true
  fi
  mapfile -d '' -t runs < <(
    find "$HOME/axia_p2_private_evidence" -mindepth 2 -maxdepth 2 \
      -type f -name summary.json -newer "$MARKER" -print0 2>/dev/null
  )
  if (( ${#runs[@]} == 1 ));then
    owner_root="$(dirname "${runs[0]}")"
    echo "D06_G07_OWNER_ORIGINAL=$owner_root"
    if [[ -f "$owner_root/source.sha" &&
          "$(cat "$owner_root/source.sha")" == "$P4_OWNER_PRIVATE_SHA" ]];then
      /usr/bin/python3 -u "$TRIAGE" \
        --live-result "$owner_root/G07/live/ci_moving_goal_result.json" \
        --output "$OUT/first_failure_triage.json" \
        > "$OUT/first_failure_triage.log" 2>&1 || true
      cat "$OUT/first_failure_triage.log" 2>/dev/null || true
      # The first CM source gap may complete only AFTER the Guard latch.
      # Preserve native Guard semantics and post-latch RMW source/receive.
      # Never publish original events; emit only sanitized joined interval.
      /usr/bin/python3 -u "$FIRST_CM_JOIN" \
        --events "$owner_root/G07/live/actual_ros_events.jsonl" \
        --live-result "$owner_root/G07/live/ci_moving_goal_result.json" \
        --output "$OUT/joined_first_cm_guard.json" \
        > "$OUT/joined_first_cm_guard.log" 2>&1 || true
      cat "$OUT/joined_first_cm_guard.log" 2>/dev/null || true
    else
      echo 'D06_G07_POSTRUN_TRIAGE_SOURCE_MISMATCH_OR_MISSING'
      if [[ "$rc" == 0 ]];then rc=3;fi
    fi
  else
    echo "D06_G07_POSTRUN_TRIAGE_RUN_AMBIGUOUS count=${#runs[@]}"
    if [[ "$rc" == 0 ]];then rc=3;fi
  fi
  if grep -Fq 'D06_RVIZ_STARTED' "$OUT/sidecar.log" 2>/dev/null;then
    echo 'D06_RVIZ_PROCESS_STARTED WSLG_VISUAL_CONFIRMATION_NOT_AUTOMATED'
  else
    echo 'D06_RVIZ_NOT_CONFIRMED'
    if [[ "$rc" == 0 ]];then rc=3;fi
  fi
  if grep -Fq 'D06_RVIZ_SIDECAR_EXITED_BEFORE_OWNER_COMPLETION' \
       "$OUT/sidecar.log" 2>/dev/null;then
    echo 'D06_RVIZ_EARLY_EXIT_BLOCKED'
    if [[ "$rc" == 0 ]];then rc=3;fi
  fi
  echo 'D06_RVIZ_DIAGNOSTICS (exact original sidecar log follows):'
  tail -n 35 "$OUT/sidecar.log" 2>/dev/null || true
  (cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 |
    sort -z | xargs -0 -r sha256sum > SHA256SUMS)
  # ALWAYS collect on exit, including GUARD_LATCH, pre-Goal startup failure,
  # incomplete rosbag, and shutdown errors. No private evidence upload.
  bundle_args=(--home "$HOME" --gui-root "$OUT" --status-code "$rc")
  [[ -z "${owner_root:-}" ]] || bundle_args+=(--owner-root "$owner_root")
  if /usr/bin/python3 "$BUNDLE_COLLECTOR" "${bundle_args[@]}";then
    echo 'AXIA_G07_OWNER_SUPPORT_BUNDLE_CAPTURE_COMPLETE_PRIVATE_ONLY'
  else
    echo 'AXIA_G07_OWNER_SUPPORT_BUNDLE_CAPTURE_FAILED_RETAIN_ALL_ORIGINALS'
    if [[ "$rc" == 0 ]];then rc=3;fi
  fi
  echo "D06_GUI_EVIDENCE=$OUT"
  echo "D06_GUI_OWNER_WRAPPER_RC=$rc P4_G11_OWNER_RC=$OWNER_RC"
  echo 'AXIA_G07_OWNER_WSLG_NOT_CI_VERIFIED: screenshot_and_Original_RAW_review_required'
  echo AXIA_MVP_DEMO_ACCEPTED=HOLD
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
# No second Git clone or mutable branch: the bootstrap pins this exact
# public release commit, and this script runs ONLY from that checkout.
# Previous v2 release and historical failed Owner lock remain untouched.
[[ "$P4_PUBLIC_RELEASE_SHA" =~ ^[a-f0-9]{40}$ &&
   "$(git -C "$ROOT" rev-parse HEAD)" == "$P4_PUBLIC_RELEASE_SHA" ]] || {
  echo 'AXIA_G07_CYCLE16_PUBLIC_IMMUTABLE_PIN_MISMATCH_NO_GOAL';exit 3;
}
RELEASE="$ROOT/$P4_G11_SCRIPT"
[[ -s "$RELEASE" ]] && bash -n "$RELEASE" || {
  echo AXIA_G07_CYCLE16_PINNED_P4_RUNNER_MISSING_NO_GOAL;exit 3;
}
grep -Fq "$P4_OWNER_PRIVATE_SHA" "$RELEASE" &&
grep -Fq "$P4_OWNER_PRIVATE_TREE" "$RELEASE" || {
  echo AXIA_G07_CYCLE16_P4_PRIVATE_PIN_OR_TREE_MISMATCH_NO_GOAL;exit 3;
}
# Authoritative Actions run provenance is verified live, not inferred from
# a JSON fixture. This check is BEFORE Owner attempt reservation and Goal.
CI_RECEIPT="$(gh api repos/silverbjin/axia-robot-safety-ci-public/actions/runs/43727149856 \
  --jq '(.head_sha // "")+" "+(.conclusion // "")+" "+(.status // "")')" || {
  echo AXIA_G07_CYCLE16_CI_API_UNAVAILABLE_HOLD_NO_GOAL;exit 3;
}
[[ "$CI_RECEIPT" == 'fa05a437db3b55d3e5e242322a4b66b7f71ae601 success completed' ]] || {
  echo AXIA_G07_CYCLE16_REAL_GUI_L2_CI_PROVENANCE_INVALID_HOLD_NO_GOAL;exit 3;
}
echo AXIA_G07_CYCLE16_REAL_GUI_L2_CI_RUN_SUCCESS_VERIFIED_NO_GOAL
# Exact new source+CI run defines ONE candidate; old failed attempts of
# different SHAs stay present and are NEVER deleted or retried.
ATTEMPT_ROOT="$HOME/.axia_g07_final_owner_attempts"
mkdir -p "$ATTEMPT_ROOT"
chmod 700 "$ATTEMPT_ROOT"
ATTEMPT_NAME="$P4_OWNER_PRIVATE_SHA-43727149856"
if ! mkdir -m 700 "$ATTEMPT_ROOT/$ATTEMPT_NAME" 2>/dev/null;then
  echo 'AXIA_G07_FINAL_OWNER_REPEAT_BLOCKED_CI_FIRST_REVIEW_REQUIRED_NO_GOAL' >&2
  exit 3
fi
printf 'private_sha=%s\nci_run=%s\n' "$P4_OWNER_PRIVATE_SHA" 43727149856 > "$ATTEMPT_ROOT/$ATTEMPT_NAME/source.txt"
echo 'G07_OWNER_FINAL_SINGLE_ATTEMPT_RESERVED; manual TTY Goal still required'
# Same sole external Gazebo -g, RViz2 and read-only Marker observer
# process implementation as CI, not the legacy embedded Gazebo GUI.
# Private P4 shared launch must honor this BEFORE any moving Goal.
export AXIA_G07_UNIFIED_GUI_SIDECAR=1
export AXIA_G07_GUI_READY_ATTESTATION_PATH="$OUT/display_attestation.json"
touch "$MARKER"
bash "$SIDECAR" "$MARKER" "$OUT" "$P4_OWNER_PRIVATE_SHA" \
  > "$OUT/sidecar.log" 2>&1 & SIDECAR_PID=$!
echo 'D06_G07_P4_OWNER_REUSE_G11_RMW_SOURCE_PROVENANCE NO_SAFETY_RUNTIME_MODIFICATION'
echo 'SIMULATION ONLY. A single moving Goal requires manual YES-P2-G07-GOAL.'
echo 'RViz educational read-only display; NOT actual CollisionMonitorState or E-Stop.'
echo 'Safety TTL 150ms unchanged. Any first Guard latch stops the trial.'
# This release (not this D06 wrapper) owns the ONLY actual Owner Goal.
# The current G11 release writes raw custody and first RMW publication diagnostics
# even when G07 BLOCKED. It never uploads private originals to PUBLIC CI.
if bash "$RELEASE";then
  OWNER_RC=0
else
  OWNER_RC=$?
fi
if (( OWNER_RC != 0 ));then exit "$OWNER_RC";fi
# The real Owner 7-channel intervals must independently meet the CI release
# headroom; never infer WSLg timing from Actions/Xvfb.
if ! python3 - "$owner_root/G07/live/ci_moving_goal_result.json" <<'PY'
import json,math,sys
from pathlib import Path
try:
    j=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    limits={"max_source_interval_sec":.12,"max_cm_interval_sec":.12,
            "max_guard_interval_sec":.12,"max_supervisor_fsm_interval_sec":.12,
            "max_scan_interval_sec":.24,"max_odom_interval_sec":.24,
            "max_clock_interval_sec":.24}
    assert j.get("first_guard_latch") is None
    assert j.get("guard_latched") is False
    assert j.get("status")=="NUMERICAL_CANDIDATE"
    for key,limit in limits.items():
        n=j.get(key)
        assert type(n) in (int,float) and math.isfinite(n) and 0<=n<limit, key
    print("AXIA_G07_CYCLE16_OWNER_120MS_7_CHANNEL_NUMERICAL_CANDIDATE_RAW_REVIEW_REQUIRED")
except (OSError,ValueError,TypeError,KeyError,AssertionError) as e:
    print("AXIA_G07_CYCLE16_OWNER_RELEASE_MARGIN_HOLD "+str(e),file=sys.stderr)
    raise SystemExit(3)
PY
then
  echo AXIA_G07_CYCLE16_OWNER_7_CHANNEL_RELEASE_MARGIN_UNVERIFIED_HOLD
  exit 3
fi
