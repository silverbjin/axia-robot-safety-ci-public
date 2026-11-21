#!/usr/bin/env bash
# AXIA D08 public WSL2 no-Goal single session, exact tested source and <=8MiB ZIP.
# This is one bounded Owner first-cycle acceptance TRIAL, not E-Stop certification.
# Mandatory SAME-world YOLO D05 -> first Owner CM B L2 #44834253238 SUCCESS.
# Instructor NVIDIA WSLg L3 is NOT_RUN; this is a SINGLE acceptance trial.
FIELD_RELEASE_READY=1
set -Eeuo pipefail
if [[ $# -gt 0 ]]; then MODE="$1"; else MODE="--run"; fi
case "$MODE" in --self-check|--doctor|--run) ;; *) echo 'D08_OWNER_USAGE=--self-check|--doctor|--run' >&2;exit 2;; esac
RUNTIME_SHA="af841aa09fa780683c191ab3e7b4188883daa5f5"
OWNER_BLOB="1a17ddaab0eac123188e29cf031c819187c4f82d"
EXTRACT_SHA="2b3080510dfee6c9da80cf515da29663f19d27a3"
EXTRACT_BLOB="142c4dcc820a04accdf869b4cc903f62c7977b2c"
REPO="silverbjin/axia-robot-safety-ci-public"
if [[ "$MODE" == --self-check ]]; then
  bash -n "$0"
  for h in "$RUNTIME_SHA" "$OWNER_BLOB" "$EXTRACT_SHA" "$EXTRACT_BLOB"; do
    [[ "$h" =~ ^[0-9a-f]{40}$ ]] || exit 2
  done
  echo D08_OWNER_FULL_PARITY_B_WSL2_WRAPPER_L0_SYNTAX_PASS_NOT_L3
  exit 0
fi
if [[ "$FIELD_RELEASE_READY" != "1" ]]; then
  echo D08_OWNER_FULL_PARITY_B_RELEASE_HOLD_MANDATORY_L2_NOT_YET_GREEN >&2
  exit 2
fi
echo "D08_OWNER_PUBLIC_L2_SCOPE=REAL_GAZEBO_WAFFLE_NAV2_UPSTREAM_YOLO_RGBD_D05_THEN_ONE_OWNER_CM_B"
echo "D08_OWNER_PUBLIC_L2_RUN=https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44834253238"
echo D08_OWNER_WSL2_L3_NOT_PREVERIFIED
ROOT="$HOME/axia_d08_owner_runs"
mkdir -p "$ROOT"
BASH_SRC="$(mktemp --suffix=.sh)"
PY_SRC="$(mktemp --suffix=.py)"
SESSION=""
ARCHIVE_RC=0
collect_latest() {
  local result_rc="$1"
  if [[ -n "$SESSION" ]]; then
    # Owner's pinned compact evidence includes the first D05 Scan source pair.
    local run_dir=""
    run_dir="$(find "$SESSION" -mindepth 1 -maxdepth 1 \
      -type d -name 'run_*' -print | sort | tail -n 1)"
    if [[ -n "$run_dir" ]]; then
      local primary="${run_dir}.diagnostics.zip"
      if [[ -s "$primary" && -s "${primary}.sha256" && ! -L "$primary" ]]; then
        if sha256sum -c "${primary}.sha256" &&
           [[ "$(stat -c '%s' "$primary")" -le 8388608 ]]; then
          echo "D08_OWNER_COMPACT_EVIDENCE_PRIMARY=$primary"
          echo "D08_OWNER_UPLOAD_ONLY_THIS_ZIP=$primary"
          echo "D08_OWNER_UPLOAD_SHA256=$(sha256sum "$primary" | cut -d ' ' -f1)"
          echo "D08_OWNER_RAW_LOCAL_PRESERVED=$SESSION"
          return "$result_rc"
        fi
        ARCHIVE_RC=2
        echo D08_OWNER_PRIMARY_DIAGNOSTICS_HASH_OR_SIZE_HOLD >&2
        return "$result_rc"
      fi
      ARCHIVE_RC=2
      echo D08_OWNER_PRIMARY_DIAGNOSTICS_MISSING_HOLD >&2
    fi
    # Pre-run failures can have no Owner run directory. This fallback
    # must NOT silently convert missing D05 primary proof into a PASS.
    if [[ -s "$PY_SRC" ]]; then
      local archive="$SESSION/D08_LATEST_FIRST_BOUNDARY.zip"
      if python3 "$PY_SRC" --root "$ROOT" --output "$archive" --max-mib 8; then
        echo "D08_OWNER_UPLOAD_ONLY_THIS_ZIP=$archive"
        echo "D08_OWNER_UPLOAD_SHA256=$(sha256sum "$archive" | cut -d ' ' -f1)"
        echo "D08_OWNER_RAW_LOCAL_PRESERVED=$SESSION"
      else
        ARCHIVE_RC=2
        echo D08_OWNER_MINIMAL_DIAGNOSTICS_ZIP_HOLD >&2
      fi
    fi
  fi
  return "$result_rc"
}
on_exit() {
  local rc="$?"
  trap - EXIT
  if [[ "$MODE" == --run ]]; then
    collect_latest "$rc" || rc="$?"
  fi
  rm -f "$BASH_SRC" "$PY_SRC"
  if ((ARCHIVE_RC!=0 && rc==0)); then rc="$ARCHIVE_RC"; fi
  echo "D08_OWNER_WRAPPER_EXIT_RC=$rc"
  exit "$rc"
}
trap on_exit EXIT
curl -fL --retry 3 --connect-timeout 15 --max-time 90 \
  "https://raw.githubusercontent.com/$REPO/$RUNTIME_SHA/d08/scripts/d08_owner_no_goal_bootstrap.sh" \
  -o "$BASH_SRC"
[[ "$(git hash-object "$BASH_SRC")" == "$OWNER_BLOB" ]] ||
  { echo D08_OWNER_PINNED_BOOTSTRAP_HASH_MISMATCH >&2; exit 2; }
curl -fL --retry 3 --connect-timeout 15 --max-time 90 \
  "https://raw.githubusercontent.com/$REPO/$EXTRACT_SHA/d08/scripts/d08_latest_owner_evidence_once.py" \
  -o "$PY_SRC"
[[ "$(git hash-object "$PY_SRC")" == "$EXTRACT_BLOB" ]] ||
  { echo D08_OWNER_PINNED_EXTRACTOR_HASH_MISMATCH >&2; exit 2; }
bash -n "$BASH_SRC"
python3 -m py_compile "$PY_SRC"
bash "$BASH_SRC" --self-check
export AXIA_D08_PUBLIC_SHA="$RUNTIME_SHA"
# The successful real L2 #44834253238 ran CycloneDDS after actual
# FastDDS map_server/change_state response timeout #44831417211.
# Only the selected Owner child process tree uses Cyclone. Do not change
# official Nav2/CM/Guard QoS, timeouts or safety boundaries.
if [[ ! -r /opt/ros/jazzy/setup.bash ]]; then
  echo D08_OWNER_ROS_JAZZY_REQUIRED >&2
  exit 2
fi
if [[ "$MODE" == --run ]] && ! dpkg-query -W -f='${Status}' \
        ros-jazzy-rmw-cyclonedds-cpp 2>/dev/null | \
        grep -Fq 'install ok installed'; then
  echo D08_OWNER_CYCLONE_RMW_INSTALL_OFFICIAL_MISSING
  sudo -v
  sudo apt-get update -qq -o APT::Update::Error-Mode=any -o Acquire::Retries=1
  sudo apt-get install -y -qq --no-install-recommends \
    ros-jazzy-rmw-cyclonedds-cpp
fi
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
set +u
source /opt/ros/jazzy/setup.bash
set -u
if ! /usr/bin/python3 -c 'import rclpy; x=rclpy.get_rmw_implementation_identifier(); assert x=="rmw_cyclonedds_cpp",x'; then
  echo D08_OWNER_CYCLONE_RMW_NOT_PROVEN_HOLD >&2
  exit 2
fi
echo D08_OWNER_SELECTED_RMW=rmw_cyclonedds_cpp
export AXIA_D08_TAKE_DISPATCH_PROBE=1
export AXIA_D08_CM_SERVICE_PROBE_MODE=isolated_process
export AXIA_D08_OWNER_FIRST_CYCLE_ONLY=1
export AXIA_D08_TRACE_CAPTURE_MAX_S=180
echo "D08_OWNER_EXACT_RUNTIME_SHA=$RUNTIME_SHA"
echo "D08_OWNER_TAKE_DISPATCH_PROBE=1"
echo "D08_OWNER_CM_SERVICE_QUERY=ISOLATED_OS_PROCESS_DIAGNOSTIC_NOT_CERTIFIED"
echo "D08_OWNER_ONE_FIRST_CYCLE_AUTO_STOP=1"
if [[ "$MODE" == --doctor ]]; then
  bash "$BASH_SRC" --doctor
  echo D08_OWNER_DOCTOR_ONLY_NOT_L3_PASS
  exit 0
fi
SESSION="$ROOT/once_$(date -u +%Y%m%dT%H%M%SZ)_$$"
mkdir -p "$SESSION"
export AXIA_D08_OWNER_EVIDENCE_ROOT="$SESSION"
echo "D08_OWNER_SINGLE_SESSION=$SESSION"
echo D08_OWNER_NO_GOAL_GUI_RUN_BEGIN_AUTO_STOP_AFTER_FIRST_REAL_OWNER_CYCLE
bash "$BASH_SRC" --doctor
set +e
bash "$BASH_SRC" --run 2>&1 | tee "$SESSION/owner_console.log"
RUN_RC=$?
set -e
echo "D08_OWNER_RUNTIME_EXIT_RC=$RUN_RC"
exit "$RUN_RC"
