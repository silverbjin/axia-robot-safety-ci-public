#!/usr/bin/env bash
# D06 classroom: reuse exact G07 Task04 native CI GREEN and its existing
# Student shared Owner one-Goal TTY launcher. No new Goal/CM/Guard implementation.
# Owner L3 is never auto-accepted; real Owner raw review is still required.
set -Eeuo pipefail
umask 077
readonly PUBLIC_REPO='silverbjin/axia-robot-safety-ci-public'
readonly STUDENT_SHA='01752add2e30c90c4d3286ef3a450f97746ecb55'
readonly TASK03_GAZEBO_L2_RUN='44223320904'
readonly TASK03_GAZEBO_L2_HEAD='6bc8b0711ab056e63e100f3eede2c5f06cdf3856'
readonly TASK04_GUI_L2_RUN='44238643061'
readonly TASK04_GUI_L2_HEAD='5bb0cd72086f2f1a057f382649b773fff106f1f9'
readonly TASK04_GUI_SCRIPT='scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh'
readonly TASK04_GUI_SCRIPT_BLOB='a15cf37e1a1d2a0253029c0a1dd8e2530e307c25'
readonly TASK04_MOVING_L2_RUN='44249348860'
readonly TASK04_MOVING_L2_HEAD='6b98a18fa7abc80401a129f715ace7703ab54286'
readonly TASK04_MOVING_STUDENT_SHA='1129cd8804954fd6481d1b6b4ebf0e0b98c68c3c'
readonly TASK04_MOVING_RUNTIME_SCRIPT_BLOB='daa04c5c6555a1cb9e851db8a31a57699821782a'
readonly TASK04_MOVING_GOAL_ENGINE_BLOB='33664dacebb0a36818d13870c27176ac0923ae4c'
readonly TASK04_MOVING_SHUTDOWN_BLOB='ff81c749b0441fee11745a29bf6fe3f7d242720c'

hold() {
  echo "D06_G07_CLASSROOM_HOLD=$1" >&2
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false' >&2
  exit 3
}

usage() {
  echo 'D06_G07_CLASSROOM_USAGE --self-check|--ci-status|--doctor|--gui-only|--live' >&2
  exit 2
}

(( $# == 1 )) || usage
mode="$1"
case "$mode" in
  --self-check|--ci-status|--doctor|--gui-only|--live) ;;
  *) usage;;
esac

self_check() {
  [[ "$STUDENT_SHA" =~ ^[0-9a-f]{40}$ &&
     "$TASK03_GAZEBO_L2_HEAD" =~ ^[0-9a-f]{40}$ &&
     "$TASK04_GUI_L2_HEAD" =~ ^[0-9a-f]{40}$ &&
     "$TASK04_GUI_SCRIPT_BLOB" =~ ^[0-9a-f]{40}$ ]] || hold INVALID_SOURCE_PIN
  [[ "$TASK04_MOVING_STUDENT_SHA" =~ ^[0-9a-f]{40}$ &&
     "$TASK04_MOVING_L2_HEAD" =~ ^[0-9a-f]{40}$ &&
     "$TASK04_MOVING_RUNTIME_SCRIPT_BLOB" =~ ^[0-9a-f]{40}$ &&
     "$TASK04_MOVING_GOAL_ENGINE_BLOB" =~ ^[0-9a-f]{40}$ &&
     "$TASK04_MOVING_SHUTDOWN_BLOB" =~ ^[0-9a-f]{40}$ ]] || hold INVALID_OWNER_PIN
  [[ "$TASK03_GAZEBO_L2_RUN" =~ ^[0-9]+$ &&
     "$TASK04_GUI_L2_RUN" =~ ^[0-9]+$ &&
     "$TASK04_MOVING_L2_RUN" =~ ^[0-9]+$ ]] || hold INVALID_RUN_PIN
  echo "D06_G07_CLASSROOM_STATIC_PASS NO_ROS_NO_GOAL student=$STUDENT_SHA"
  echo "D06_G07_CLASSROOM_REUSED_MOVING_CI=$TASK03_GAZEBO_L2_RUN"
  echo "D06_G07_CLASSROOM_REUSED_GUI_CI=$TASK04_GUI_L2_RUN"
  echo "D06_G07_CLASSROOM_REUSED_SAME_SESSION_NATIVE_CI=$TASK04_MOVING_L2_RUN"
  echo "D06_G07_CLASSROOM_PINNED_OWNER_SOURCE=$TASK04_MOVING_STUDENT_SHA"
  echo 'D06_G07_CLASSROOM_OWNER_MOVING_L3=NOT_RUN'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
}

check_run() {
  local id="$1" sha="$2" scope="$3" actual
  actual="$(gh api "repos/$PUBLIC_REPO/actions/runs/$id" \
    --jq '(.head_sha // "")+" "+(.status // "")+" "+(.conclusion // "")')" ||
    hold "${scope}_CI_PROVENANCE_UNAVAILABLE"
  [[ "$actual" == "$sha completed success" ]] ||
    hold "${scope}_CI_SOURCE_OR_CONCLUSION_MISMATCH"
  echo "D06_G07_CLASSROOM_${scope}_HISTORICAL_CI_PASS run=$id head=$sha"
}


# G07 Task04 Student runtime already owns the SAME native CI/Owner Goal engine.
# Only its existing --owner-launch-pid + controlling-TTY path may send motion.
# This D06 wrapper never publishes /cmd_vel, never forges GitHub Actions, and
# never overrides a Guard latch or accepts an unreviewed Owner L3 run.
run_verified_owner() {
  [[ "${GITHUB_ACTIONS:-}" != true && -t 0 && -t 1 && -r /dev/tty ]] ||
    hold D06_G07_OWNER_REAL_TTY_REQUIRED_NO_GOAL
  [[ -r /proc/sys/kernel/osrelease ]] &&
    grep -Eiq 'microsoft|wsl' /proc/sys/kernel/osrelease ||
    hold D06_G07_OWNER_WSL2_REQUIRED_NO_GOAL
  source /etc/os-release
  [[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] ||
    hold D06_G07_UBUNTU_2404_REQUIRED_NO_GOAL
  [[ -r /opt/ros/jazzy/setup.bash && -n "${DISPLAY:-}" &&
     -n "${XDG_RUNTIME_DIR:-}" ]] ||
    hold D06_G07_WSLG_JAZZY_REQUIRED_NO_GOAL
  for cmd in git bash python3 gz cmake c++ colcon ros2 rviz2 xwininfo \
             glxinfo timeout sha256sum tar; do
    command -v "$cmd" >/dev/null 2>&1 || hold "OWNER_MISSING_$cmd"
  done
  [[ -r /usr/include/gz/sim8/gz/sim/System.hh ]] ||
    hold G07_NATIVE_ECM_CONTACT_DEV_HEADERS_REQUIRED_NO_GOAL
  [[ "${AXIA_G07_CI_SIM_GOAL_ALLOWED:-0}" != 1 ]] ||
    hold OWNER_CI_GOAL_AUTHORITY_OVERLAP_NO_GOAL
  # EXIT trap runs after this function returns, so archive variables MUST
  # outlive local scope. Never lose a WSL2 first-failure evidence bundle.
  D06_OWNER_BASE="$HOME/axia_d06_g07_owner_evidence"
  mkdir -p "$D06_OWNER_BASE"
  chmod 700 "$D06_OWNER_BASE"
  local src runtime build binary run_rc=0
  D06_OWNER_OUT="$(mktemp -d "$D06_OWNER_BASE/d06-moving-XXXXXXXX")" ||
    hold OWNER_EVIDENCE_ROOT
  local out="$D06_OWNER_OUT" base="$D06_OWNER_BASE"
  chmod 700 "$out"
  finish_owner() {
    local rc=$?
    trap - EXIT INT TERM
    set +e
    if [[ -n "${D06_OWNER_OUT:-}" && -d "$D06_OWNER_OUT" ]];then
      if ! (cd "$D06_OWNER_OUT" && find . -type f ! -name SHA256SUMS -print0 |
         sort -z | xargs -0 -r sha256sum > SHA256SUMS);then
        echo 'D06_G07_OWNER_CUSTODY_SUMS_INCOMPLETE' >&2
        rc=3
      fi
      if tar -czf "$D06_OWNER_OUT.tar.gz" -C "$D06_OWNER_BASE" "$(basename "$D06_OWNER_OUT")" &&
         [[ -s "$D06_OWNER_OUT.tar.gz" ]] &&
         sha256sum "$D06_OWNER_OUT.tar.gz" > "$D06_OWNER_OUT.tar.gz.sha256";then
        echo "D06_G07_OWNER_RAW_ARCHIVE=$D06_OWNER_OUT.tar.gz"
        echo "D06_G07_OWNER_RAW_SHA256=$D06_OWNER_OUT.tar.gz.sha256"
      else
        echo 'D06_G07_OWNER_CUSTODY_ARCHIVE_UNVERIFIED_HOLD' >&2
        rc=3
      fi
    fi
    if [[ "$rc" == 0 ]];then
      echo 'D06_G07_OWNER_L3=RAW_REVIEW_REQUIRED_NOT_ACCEPTED'
    else
      echo 'D06_G07_OWNER_L3=HOLD_FAILED_OR_BLOCKED'
    fi
    echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
    exit "$rc"
  }
  trap finish_owner EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  echo "D06_G07_SAME_SESSION_NATIVE_L2_PIN=$TASK04_MOVING_L2_RUN" > "$out/source_manifest.txt"
  echo "G07_TASK04_WORKFLOW_SHA=$TASK04_MOVING_L2_HEAD" >> "$out/source_manifest.txt"
  echo "G07_TASK04_STUDENT_SHA=$TASK04_MOVING_STUDENT_SHA" >> "$out/source_manifest.txt"
  set +u
  source /opt/ros/jazzy/setup.bash
  if [[ -n "${AXIA_NAV2_OVERLAY_SETUP:-}" ]];then
    [[ -r "$AXIA_NAV2_OVERLAY_SETUP" ]] ||
      hold NAV2_EXPLICIT_OVERLAY_ABSENT_NO_GOAL
    source "$AXIA_NAV2_OVERLAY_SETUP"
  elif [[ -r "$HOME/axia_p1_abc_verification/results/p1-nav2-official-overlay/install/setup.bash" ]];then
    source "$HOME/axia_p1_abc_verification/results/p1-nav2-official-overlay/install/setup.bash"
  fi
  set -u
  [[ "${ROS_DISTRO:-}" == jazzy ]] || hold ROS_JAZZY_VERSION_MISMATCH_NO_GOAL
  for pkg in nav2_bringup nav2_minimal_tb3_sim ros_gz_sim;do
    ros2 pkg prefix "$pkg" >> "$out/official_packages.txt" 2>&1 ||
      hold "MISSING_OFFICIAL_PACKAGE_$pkg"
  done
  timeout 12s glxinfo -B > "$out/wslg_glxinfo.txt" 2>&1 ||
    hold WSLG_GLX_RENDER_UNAVAILABLE_NO_GOAL
  grep -Eiq 'D3D12' "$out/wslg_glxinfo.txt" ||
    hold WSLG_D3D12_RENDERER_NOT_VERIFIED_NO_GOAL

  src="$(mktemp -d "$HOME/.cache_axia_d06_g07_source_XXXXXXXX")" ||
    hold G07_SOURCE_TEMP_UNAVAILABLE
  git init -q "$src"
  git -C "$src" remote add origin 'https://github.com/silverbjin/axia-robot-safety-student.git'
  GIT_TERMINAL_PROMPT=0 git -C "$src" fetch -q --no-tags --depth 1 origin "$TASK04_MOVING_STUDENT_SHA" ||
    hold G07_OWNER_SOURCE_FETCH_FAIL
  git -C "$src" -c advice.detachedHead=false checkout -q --detach FETCH_HEAD ||
    hold G07_OWNER_SOURCE_CHECKOUT_FAIL
  [[ "$(git -C "$src" rev-parse HEAD)" == "$TASK04_MOVING_STUDENT_SHA" ]] ||
    hold G07_OWNER_SOURCE_SHA_MISMATCH
  runtime="$src/block_B/day07/h01_runtime"
  [[ "$(git hash-object "$runtime/scripts/p2_no_goal_smoke_ci.sh")" == "$TASK04_MOVING_RUNTIME_SCRIPT_BLOB" &&
     "$(git hash-object "$runtime/tools/p2_g07_ci_moving_goal.py")" == "$TASK04_MOVING_GOAL_ENGINE_BLOB" &&
     "$(git hash-object "$runtime/tools/p2_g07_ordered_shutdown.py")" == "$TASK04_MOVING_SHUTDOWN_BLOB" ]] ||
    hold G07_OWNER_RUNTIME_BLOB_MISMATCH
  bash -n "$runtime/scripts/p2_no_goal_smoke_ci.sh" ||
    hold G07_OWNER_RUNTIME_SYNTAX_NO_GOAL

  build="$src/native_witness_build"
  cmake -S "$runtime/tools/native_s02_public" -B "$build" -DCMAKE_BUILD_TYPE=Release \
    > "$out/native_build.log" 2>&1 ||
    hold G07_NATIVE_ECM_CMAKE_FAILED_NO_GOAL
  cmake --build "$build" --parallel 2 >> "$out/native_build.log" 2>&1 ||
    hold G07_NATIVE_ECM_BUILD_FAILED_NO_GOAL
  binary="$build/libaxia_g07_s02_ecm_witness.so"
  [[ -s "$binary" ]] || hold G07_NATIVE_ECM_WITNESS_ABSENT_NO_GOAL
  sha256sum "$binary" > "$out/native_witness.sha256"
  export GZ_SIM_SYSTEM_PLUGIN_PATH="$build${GZ_SIM_SYSTEM_PLUGIN_PATH:+:$GZ_SIM_SYSTEM_PLUGIN_PATH}"
  export AXIA_G07_TASK03_WITNESS_SHA256
  AXIA_G07_TASK03_WITNESS_SHA256="$(sha256sum "$binary" | cut -d' ' -f1)"
  export AXIA_P2_SMOKE_RESULTS="$out/native"
  export AXIA_G07_TASK03_WITNESS_REPORT="$out/native/s02_ecm_witness.json"
  export AXIA_P0_SIM_ONLY=1 AXIA_P2_G07_PHYSICAL_PREFLIGHT=1
  export AXIA_G07_OWNER_STARTUP_PARITY=1 AXIA_G07_CI_OWNER_BAG_PARITY=1
  # The pinned Student script interprets this historical flag as CI-only:
  # it calls p2_g07_owner_env_parity.py --mode ci and explicitly rejects
  # microsoft-standard-WSL2. The Owner path checks --mode owner below,
  # including ALL SAME 25 packages and 5 official file hashes.
  # No ROS, CM, Guard, TF or safety TTL checks are skipped.
  export AXIA_P2_G07_OWNER_PARITY_CHECK=0
  export AXIA_G07_TASK02_SIMPLE_TF_CANDIDATE=1
  export AXIA_G07_TASK03_ECM_WITNESS=1
  export AXIA_G07_TASK04_OWNER_MOVING_L3=1
  export AXIA_G07_TASK04_EXPECTED_STUDENT_SHA="$TASK04_MOVING_STUDENT_SHA"
  export AXIA_G07_CI_SIM_GOAL_ALLOWED=0 AXIA_G07_TASK04_CI_GUI_MOVING=0
  export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
  export ROS_DOMAIN_ID="${AXIA_D06_ROS_DOMAIN_ID:-94}"
  [[ "$ROS_DOMAIN_ID" =~ ^[0-9]+$ ]] && (( ROS_DOMAIN_ID>=1 && ROS_DOMAIN_ID<=101 )) ||
    hold D06_ROS_DOMAIN_INVALID_NO_GOAL
  export GZ_PARTITION="axia_p2_d06_${BASHPID}_$(date -u +%s)"
  [[ "$GZ_PARTITION" =~ ^[a-zA-Z0-9_]+$ ]] ||
    hold D06_GZ_PARTITION_INVALID_NO_GOAL
  unset AXIA_G07_TASK03_FORMAL_CI AXIA_G07_TASK03_POSITIVE_ONLY \
        AXIA_D07_H01_GUI_NO_GOAL AXIA_D07_H01_TEACHING_LOOP \
        AXIA_P3_S01_CI_GOAL_ALLOWED AXIA_P3_S03_CI_COMPOUND_ALLOWED \
        AXIA_P3_S04_CI_PNU_ALLOWED AXIA_P3_S05_CI_GOAL_ALLOWED || true
  export QT_QPA_PLATFORM=xcb
  unset LIBGL_ALWAYS_SOFTWARE || true
  python3 "$runtime/tools/p2_g07_owner_env_parity.py" --mode owner \
    --output "$out/owner_parity.json" > "$out/owner_parity.log" 2>&1 ||
    hold D06_G07_OWNER_25_5_PARITY_FAILED_NO_GOAL
  # Preserve kernel distinction: PASS here does NOT mean WSL2 scheduler or
  # WSLg GPU timing is equivalent to the native public Linux CI machine.
  python3 - "$out/owner_parity.json" <<'PY' ||
    hold D06_G07_OWNER_CORE_PARITY_REPORT_INVALID_NO_GOAL
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
assert (r.get("status")=="CORE_PARITY_PASS" and r.get("mode")=="owner"
        and r.get("wsl_detected") is True
        and r.get("checked_packages")==25
        and r.get("checked_official_files")==5
        and r.get("mismatch")=={})
print("D06_G07_OWNER_CORE_PARITY_PASS_PACKAGES25_FILES5_WSL2")
PY
  echo "D06_G07_OWNER_PIN_VERIFIED=$TASK04_MOVING_STUDENT_SHA"
  echo 'D06_G07_OWNER_REAL_GAZEBO_RVIZ_MOVING_CANDIDATE_START'
  echo 'D06_G07_OWNER_CONSENT_IS_MANUAL_TTY_ONLY=YES-P2-G07-GOAL'
  # The ORIGINAL verified G07 shell takes TTY consent and checks three
  # owned Supervisor / CM / Guard PIDs. Do not pipe a consent token.
  cd "$runtime"
  set +e
  bash scripts/p2_no_goal_smoke_ci.sh > "$out/owner_run.log" 2>&1
  run_rc=$?
  set -e
  cd "$HOME" || cd /
  if [[ "$run_rc" != 0 ]];then
    tail -n 75 "$out/owner_run.log" >&2 || true
    hold "D06_G07_OWNER_RUNTIME_BLOCKED_RC_$run_rc"
  fi
  # No automatic Owner L3 approval; keep exactly the original raw signals.
  python3 - "$runtime" "$out/native" "$out/owner_readonly_gate.json" <<'PY'
import json,sys
from pathlib import Path
runtime,root,output=map(Path,sys.argv[1:])
sys.path.insert(0,str(runtime/"tools"))
from p2_g07_task03_contract import audit_bag_14,audit_guard_internal_cm_age
def load(name):
    return json.loads((root/name).read_text())
r=load("g07_ci_moving/ci_moving_goal_result.json")
s=load("g07_ordered_shutdown.json")
a=load("g07_shutdown_audit.json")
w=load("s02_ecm_witness.json")
bag=audit_bag_14(root/"rosbag2")
rows=[json.loads(line) for line in
      (root/"g07_ci_moving/actual_ros_events.jsonl").read_text().splitlines()]
goals=[row for row in rows if row.get("kind")=="owner_goal_published"]
ends=[row for row in rows if row.get("kind")=="task03_motion_window_end"]
guard=(audit_guard_internal_cm_age(rows,goal_start=goals[0]["t"],
                                  window_end=ends[0]["t"])
       if len(goals)==len(ends)==1 else {"status":"HOLD"})
checks={
 "manual_pid_tty_owner_admitted":r.get("owner_authority_verified") is True,
 "numeric_candidate_only":r.get("status")=="NUMERICAL_CANDIDATE",
 "no_guard_latch":r.get("guard_latched") is False,
 "guard_internal_cm_age_150ms":guard.get("status")=="GUARD_NATIVE_CM_AGE_TTL150_PASS",
 "one_real_goal_window":len(goals)==len(ends)==1,
 "first_timing_violation_none":r.get("first_timing_violation") is None,
 "actual_movement":r.get("observed_odom_moved_m",0)>.05,
 "stopped_dwell_1s":r.get("odom_stopped_dwell_sec",0)>=1,
 "exact_goal_canceled":r.get("goal_cancel_ack") is True and r.get("goal_cancel_status")==5,
 "navigation_ack":s.get("navigation_ack") is True,
 "localization_ack":s.get("localization_ack") is True,
 "cm_child_clean_exit":a.get("cm_exit_code")==0,
 "native_contact0":w.get("sensor_found") is True and w.get("report_complete") is True and w.get("positive_contacts")==0 and w.get("missing_iterations")==0 and type(w.get("observed_iterations")) is int and w["observed_iterations"]>=20,
 "bag_sqlite14":bag.get("status")=="ACTUAL_SQLITE_14_TOPIC_CUSTODY_PASS",
 "cm_observer_120ms":0<r.get("max_cm_interval_sec",999)<=.12,
 "guard_observer_150ms":0<r.get("max_guard_interval_sec",999)<=.15,
 "scan_300ms":0<r.get("max_scan_interval_sec",999)<=.30
}
result={"status":"OWNER_NUMERICAL_CANDIDATE_REVIEW_REQUIRED" if all(checks.values()) else "HOLD",
        "first_failure":next((k for k,v in checks.items() if not v),"NONE"),
        "checks":checks,"owner_l3_accepted":False,"certified_estop":False,
        "exact_source_sha":r.get("source_sha")}
output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print("D06_G07_OWNER_READONLY_FIRST_FAILURE="+result["first_failure"])
print("D06_G07_OWNER_READONLY_STATUS="+result["status"])
if result["status"]=="HOLD":raise SystemExit(3)
PY
  echo 'D06_G07_OWNER_SAME_SOURCE_NUMERICAL_CANDIDATE_RAW_REVIEW_REQUIRED'
  echo 'D06_G07_WSLG_REAL_GUI_PIXELS_AND_RMW_SOURCE_RAW_REVIEW_PENDING'
}

self_check >/dev/null || hold SELF_CHECK_FAILED
if [[ "$mode" == --self-check ]];then
  self_check
  exit 0
fi
if [[ "$mode" == --live ]];then
  [[ "${GITHUB_ACTIONS:-}" != true && -t 0 && -t 1 && -r /dev/tty ]] ||
    hold D06_G07_OWNER_REAL_TTY_REQUIRED_NO_GOAL
fi
[[ "${GITHUB_ACTIONS:-}" != true || "$mode" == --ci-status ]] ||
  hold D06_G07_CLASSROOM_OWNER_WSL2_ONLY
command -v gh >/dev/null 2>&1 || hold GH_CLI_REQUIRED
check_run "$TASK03_GAZEBO_L2_RUN" "$TASK03_GAZEBO_L2_HEAD" TASK03_MOVING
check_run "$TASK04_GUI_L2_RUN" "$TASK04_GUI_L2_HEAD" TASK04_GUI
check_run "$TASK04_MOVING_L2_RUN" "$TASK04_MOVING_L2_HEAD" TASK04_MOVING
if [[ "$mode" == --ci-status ]];then
  echo 'D06_G07_CLASSROOM_CI_REUSE_PROVENANCE_PASS TASK04_NATIVE_MOVING_GUI_L2_SCOPED'
  echo 'D06_G07_CLASSROOM_VERIFICATION_ONLY_NO_GAZEBO_NO_RVIZ'
  echo 'D06_G07_CLASSROOM_GUI_ACTION=--gui-only D06_G07_CLASSROOM_MOVING_ACTION=--live_MANUAL_TTY_OWNER_CANDIDATE'
  echo 'D06_G07_CLASSROOM_OWNER_MOVING_L3=NOT_RUN'
  exit 0
fi
if [[ "$mode" == --live ]];then
  run_verified_owner
  exit $?
fi
# Actual GUI modes are for an interactive WSL2 Owner only; no Actions,
# CI Goal permission spoofing, private Instructor checkout or fake approval.
[[ "${GITHUB_ACTIONS:-}" != true ]] || hold D06_G07_CLASSROOM_OWNER_WSL2_ONLY
[[ -r /proc/sys/kernel/osrelease ]] &&
 grep -Eiq 'microsoft|wsl' /proc/sys/kernel/osrelease ||
 hold D06_G07_CLASSROOM_OWNER_WSL2_ONLY
[[ -t 0 && -r /dev/tty ]] || hold OWNER_TERMINAL_REQUIRED
for cmd in curl git bash;do
  command -v "$cmd" >/dev/null 2>&1 || hold "MISSING_$cmd"
done
script="$(mktemp --suffix=.sh)" || hold TEMPFILE_UNAVAILABLE
trap 'rm -f -- "$script"' EXIT
curl -fLsS --retry 3 --retry-delay 2 --max-time 90 \
  "https://raw.githubusercontent.com/$PUBLIC_REPO/$TASK04_GUI_L2_HEAD/$TASK04_GUI_SCRIPT" \
  -o "$script" || hold TASK04_PIN_DOWNLOAD_FAILED
[[ "$(git hash-object "$script")" == "$TASK04_GUI_SCRIPT_BLOB" ]] ||
  hold TASK04_DOWNLOADED_BLOB_MISMATCH
bash -n "$script" || hold TASK04_SCRIPT_SYNTAX
if [[ "$mode" == --doctor ]];then
  bash "$script" --doctor
  echo 'D06_G07_CLASSROOM_OWNER_DOCTOR_COMPLETE NO_GOAL'
else
  echo 'D06_G07_CLASSROOM_GUI_ONLY_START NO_MOVING_GOAL'
  bash "$script" --run
  echo 'D06_G07_CLASSROOM_GUI_ONLY_COMPLETE_OWNER_MOVING_NOT_RUN'
fi
