#!/usr/bin/env bash
# AXIA G07 Task04 — CI-BLOCKED diagnostic candidate, NOT released for Owner L3.
# Strict Gazebo 2-cycle #44770998324 requires exact 2/2 admission; NO RELEASE until verified.
# --ci-check/--run MUST hold until a DIFFERENT exact successful CI L2 SHA.
# Simulation-only. Manual controlling TTY consent is performed by the
# identical Student scenario runner AFTER real Nav2 and safety node readiness.
# No CI credentials, no second Gazebo server, no global process kill.
set -Eeuo pipefail
umask 077
readonly STUDENT_REPO='silverbjin/axia-robot-safety-student'
readonly STUDENT_SHA='891bf65349cf8dfb203bb8b97ffe0346b3fb8b3f'
readonly REVIEW_REPO='silverbjin/axia-robot-safety-ci-public'
readonly REVIEW_SHA='90e809e858e04adee3c72cee36c5dc7dd9f3d632'
readonly CI_L2_RUN=44770998324
MODE="${1:---run}"
if [[ $# -gt 1 ]];then echo 'AXIA_G07_TASK04_FIRST_FAILURE=BAD_ARGUMENTS' >&2;exit 3;fi
case "$MODE" in
  --self-check|--ci-check|--run) ;;
  *) echo 'AXIA_G07_TASK04_FIRST_FAILURE=BAD_ARGUMENTS' >&2;exit 3 ;;
esac
# RELEASE ADMISSION: an educational visual HOLD cannot authorize a new
# field run. Public CI must have both actual Gazebo Moving Goal matrix jobs
# SUCCESS on the exact candidate Student source, with formal fallback exiting 3.
readonly CI_L2_HEAD='44b5b704be2722f54beec9b7436ab8e705ceec3d'
ci_l2_release_gate() {
  local run_json jobs_json rc=0
  run_json="$(mktemp)" || return 3
  jobs_json="$(mktemp)" || { rm -f -- "$run_json"; return 3; }
  if ! curl -fLsS --retry 2 --max-time 40 \
        "https://api.github.com/repos/$REVIEW_REPO/actions/runs/$CI_L2_RUN" -o "$run_json" \
     || ! curl -fLsS --retry 2 --max-time 40 \
        "https://api.github.com/repos/$REVIEW_REPO/actions/runs/$CI_L2_RUN/jobs?per_page=100" -o "$jobs_json";then
    echo 'AXIA_G07_STABILIZATION_CI_API_UNAVAILABLE_RELEASE_HOLD' >&2
    rc=3
  else
    python3 - "$run_json" "$jobs_json" "$CI_L2_HEAD" "$CI_L2_RUN" <<'PY_RELEASE_GATE' || rc=3
import json,sys
from pathlib import Path
try:
    run=json.loads(Path(sys.argv[1]).read_text())
    jobs=json.loads(Path(sys.argv[2]).read_text())
    allowed=(run.get("id")==int(sys.argv[4]) and
             run.get("head_sha")==sys.argv[3] and
             run.get("event")=="push" and
             run.get("status")=="completed" and
             run.get("conclusion")=="success" and
             run.get("name")=="AXIA G07 FV17 Independent 2-cycle Real Moving Goal Guard TTL L2")
    expected={"one-real-gazebo-moving-gui (1)",
              "one-real-gazebo-moving-gui (2)"}
    actual=[j for j in jobs.get("jobs",[]) if j.get("name") in expected]
    allowed=allowed and len(actual)==2 and {j.get("name") for j in actual}==expected
    allowed=allowed and all(j.get("status")=="completed" and
                            j.get("conclusion")=="success" for j in actual)
except (ValueError,OSError,TypeError,KeyError):
    allowed=False
if not allowed:
    print("AXIA_G07_STABILIZATION_CI_L2=HOLD_NO_NEW_WSL2_MOVING_RELEASE",flush=True)
    sys.exit(3)
print("AXIA_G07_STABILIZATION_CI_L2=PASS_TWO_STRICT_REAL_GAZEBO_GOALS_OWNER_WSL2_NOT_RUN",flush=True)
PY_RELEASE_GATE
  fi
  rm -f -- "$run_json" "$jobs_json"
  return "$rc"
}
if [[ "$MODE" == --self-check ]];then
  echo "AXIA_G07_STABILIZATION_WSL2_BOOTSTRAP_L0_PASS student_sha=$STUDENT_SHA l2_run=$CI_L2_RUN NO_ROS_NO_GAZEBO_NO_GOAL"
  echo 'AXIA_G07_TASK04_NATIVE_WITNESS_CACHE_V1=AVAILABLE_FIRST_WARM_RUN_UNMEASURED'
  echo 'AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi

if [[ "$MODE" == --ci-check ]];then
  ci_l2_release_gate
  exit $?
fi
# Fail closed BEFORE any WSL2/Gazebo/Goal side effect.
ci_l2_release_gate || exit 3

OUT=''
FIRST_FAILURE='NOT_STARTED'
WATCH_PID=''
NUMERICAL='NOT_RUN'
finish() {
  local rc=$?
  trap - EXIT INT TERM
  set +e
  if [[ -n "$WATCH_PID" ]] && kill -0 "$WATCH_PID" 2>/dev/null;then
    kill -TERM "$WATCH_PID" 2>/dev/null
    wait "$WATCH_PID" 2>/dev/null
  fi
  if [[ -n "$OUT" && -d "$OUT" ]];then
    echo "$FIRST_FAILURE" > "$OUT/first_failure.txt"
    if [[ ! -s "$OUT/task04_owner_verdict.json" ]] && command -v python3 >/dev/null 2>&1;then
      python3 - "$OUT/task04_owner_verdict.json" "$FIRST_FAILURE" "$STUDENT_SHA" "$CI_L2_RUN" <<'PY' || true
import json,sys
from pathlib import Path
record={"schema":"axia_g07_task04_owner_l3_local_hold_v1",
        "status":"HOLD","first_failure":sys.argv[2],
        "source_sha":sys.argv[3],"public_ci_native_l2_run":int(sys.argv[4]),
        "owner_moving_l3_accepted":False,"axia_mvp_demo_accepted":False,
        "certified_estop":False}
Path(sys.argv[1]).write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
PY
    fi
    # Candidate-only: derive six allowlisted numeric first-boundary files.
    # This is never a safety/Goal acceptance check and must never replace
    # native original evidence. At any pre-Goal failure, retain HOLD records.
    if [[ -n "${REVIEW_CACHE:-}" && -r "$REVIEW_CACHE/d06/diagnostic/g07_scan_compact_bundle.py" ]];then
      python3 "$REVIEW_CACHE/d06/diagnostic/g07_scan_compact_bundle.py" \\
        --root "$OUT" --student-sha "$STUDENT_SHA" --l2-run "$CI_L2_RUN" \\
        > "$OUT/scan_compact_diagnostic.log" 2>&1 || \\
        echo 'AXIA_G07_SCAN300_COMPACT_RECORDS_HOLD' >&2
    fi
    (
      cd "$OUT"
      find . -type f ! -name SHA256SUMS -print0 | sort -z |
        xargs -0 -r sha256sum > SHA256SUMS
    ) || true
    tar -czf "$OUT.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")" || true
    if [[ -s "$OUT.tar.gz" ]];then
      sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256"
    fi
    # Separate SMALL diagnostic bundle; original 14-topic SQLite/raw tar is retained
    # unchanged and private on the Owner WSL2 host. No source/build/bag in ZIP.
    python3 - "$OUT" "$OUT.diagnostics.zip" <<'PY_DIAGNOSTICS' || echo 'AXIA_G07_TASK04_DIAGNOSTIC_ZIP_BUILD_FAILED'
import hashlib
import sys
import zipfile
from pathlib import Path

root=Path(sys.argv[1])
dest=Path(sys.argv[2])
names=[
    'first_failure.txt','manifest.txt','gui_windows.txt',
    'startup_timing.tsv','native_witness_build_profile.json',
    'domain_selection.json','domain_selection.log',
    'task04_owner_verdict.json','task04_owner_numeric_review.json',
    'task04_mvp_visual_verdict.json',
    'task04_owner_mvp_scope.json','owner_mvp_scope.log',
    'owner_numeric_review.log','owner_parity.json',
    'native/runtime.txt','native/clock_diagnostics.json',
    'native/g07_ci_pregoal/pregoal_baseline.json',
    'native/g07_ci_pregoal/owner_pregoal_l2.json',
    'native/g07_ci_pregoal.log',
    'native/g07_active_cm_native_parameters.json',
    'native/g07_ci_moving/ci_moving_goal_result.json',
    'native/g07_ordered_shutdown.json','native/g07_shutdown_audit.json',
    'native/staged_startup.log','native/g07_ordered_shutdown.log',
    'native/g07_ci_scan_pregoal.json','native/g07_ci_scan_pregoal.log',
    'first_scan_timing_boundary.json','scan_wall_sim_rtf_summary.json',
    'scan_pipeline_first_failure.json','guard_supervisor_first_state_transition.json',
    'native_shutdown_verdict.json','release_scope.json',
    'scan_compact_diagnostic.log',
]
names.extend(str(p.relative_to(root)) for p in
             (root/'native/g07_ci_pregoal').glob('gz_pose_*.log')
             if p.is_file() and not p.is_symlink())
hashes=[]
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,
                     compresslevel=6) as zf:
    for rel in sorted(set(names)):
        if not rel or '..' in Path(rel).parts:
            continue
        path=root/rel
        if not path.is_file() or path.is_symlink():
            continue
        with path.open('rb') as stream:
            total=path.stat().st_size
            if total>65536 and path.suffix=='.log':
                head=stream.read(12000)
                stream.seek(max(0,total-32000))
                payload=head+b'\n[LOG_SNIPPET_MIDDLE_OMITTED]\n'+stream.read()
            elif total<=262144:
                payload=stream.read()
            else:
                continue
        zf.writestr(rel,payload)
        hashes.append(hashlib.sha256(payload).hexdigest()+'  '+rel)
    zf.writestr('SHA256SUMS','\n'.join(hashes)+'\n')
if dest.stat().st_size>8*1024*1024:
    dest.unlink()
    print('AXIA_G07_TASK04_DIAGNOSTIC_BUNDLE_OVER_8MIB_HOLD',flush=True)
    raise SystemExit(3)
print('AXIA_G07_TASK04_DIAGNOSTIC_BUNDLE_WRITTEN',flush=True)
PY_DIAGNOSTICS
    if [[ -s "$OUT.diagnostics.zip" ]];then
      sha256sum "$OUT.diagnostics.zip" > "$OUT.diagnostics.zip.sha256"
      echo "AXIA_G07_TASK04_DIAGNOSTIC_ZIP=$OUT.diagnostics.zip"
      echo "AXIA_G07_TASK04_DIAGNOSTIC_SHA256=$OUT.diagnostics.zip.sha256"
    fi
    echo "AXIA_G07_TASK04_ARCHIVE=$OUT.tar.gz"
    echo "AXIA_G07_TASK04_SHA256=$OUT.tar.gz.sha256"
    echo "AXIA_G07_TASK04_LOCAL_EVIDENCE=$OUT"
  fi
  echo "AXIA_G07_TASK04_FIRST_FAILURE=$FIRST_FAILURE"
  echo "AXIA_G07_TASK04_OWNER_NUMERICAL_CANDIDATE=$NUMERICAL"
  echo 'AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit "$rc"
}
trap finish EXIT
trap 'FIRST_FAILURE=OWNER_INTERRUPT;exit 130' INT
trap 'FIRST_FAILURE=OWNER_TERMINATED;exit 143' TERM
hold() { FIRST_FAILURE="$1";echo "AXIA_G07_TASK04_FIRST_FAILURE=$1" >&2;exit 3; }

# Owner is a real interactive WSL2 process, never a simulated CI actor.
[[ "${GITHUB_ACTIONS:-}" != true ]] || hold CI_AUTHORITY_DENIED
[[ -t 0 && -r /dev/tty ]] || hold OWNER_CONTROLLING_TTY_REQUIRED
grep -Eiq 'microsoft|wsl' /proc/sys/kernel/osrelease || hold WSL2_REQUIRED
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || hold UBUNTU_2404_REQUIRED
[[ -r /opt/ros/jazzy/setup.bash ]] || hold ROS_JAZZY_REQUIRED
[[ -n "${DISPLAY:-}" && -n "${XDG_RUNTIME_DIR:-}" ]] || hold WSLG_GUI_REQUIRED
for cmd in git bash python3 gz glxinfo xwininfo tar sha256sum timeout setsid colcon flock dpkg-query curl;do
  command -v "$cmd" >/dev/null 2>&1 || hold "MISSING_COMMAND_$cmd"
done

# Explicit negative CI authority; no GITHUB_ACTIONS spoof or shell auto-reply.
export AXIA_G07_CI_SIM_GOAL_ALLOWED=0
export AXIA_P0_SIM_ONLY=1
export AXIA_P2_G07_PHYSICAL_PREFLIGHT=1
export AXIA_G07_OWNER_STARTUP_PARITY=1
# Exact Student 4f4d07f6... uses a CI/Owner-separated single-request
# navigation Lifecycle SHUTDOWN on the DDS participant already proven by
# read-only /get_parameters. Owner never spoofs GITHUB_ACTIONS or CI Goal.
unset AXIA_G07_NAV_WARM_PARTICIPANT_CI_AB
export AXIA_G07_NAV_WARM_PARTICIPANT_OWNER=1
export AXIA_G07_CI_OWNER_BAG_PARITY=1
export AXIA_P2_G07_RELOCATED_OBSTACLE=1
export AXIA_G07_TASK02_SIMPLE_TF_CANDIDATE=1
export AXIA_G07_TASK04_OWNER_MOVING_L3=1
# Scan 300ms strict NO_GOAL observation is in the SAME running Gazebo graph.
export AXIA_G07_SCAN_PREFLIGHT_STRICT=1
export AXIA_G07_TASK03_ECM_WITNESS=1
export AXIA_NAV2_USE_COMPOSITION=False
unset AXIA_G07_TASK03_FORMAL_CI AXIA_G07_TASK03_POSITIVE_ONLY AXIA_D07_H01_GUI_NO_GOAL AXIA_G07_TASK04_CI_GUI_MOVING || true
unset AXIA_G07_OWNER_COMMON_RUNNER_AUTHORIZED AXIA_P2_OWNER_PINNED_SHA || true
# Jazzy DDS isolation is chosen AFTER ROS is sourced, by a read-only ROS
# endpoint probe. Do not reuse the stale fixed ROS_DOMAIN_ID=86.
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
# Verified in actual public Jazzy/Harmonic 2-cycle #44697383450:
# Fast DDS 2.14.x healthy Shared Memory port may block ~333ms (#6535).
# Limit this Owner child process tree to official UDPv4 built-in transport;
# never relax CM120 / Guard150 / Scan300 / Clock300 / Odom300 TTL.
# XML transport overrides can reenable SHM; fail closed instead.
[[ -z "${FASTRTPS_DEFAULT_PROFILES_FILE:-}" && -z "${FASTDDS_DEFAULT_PROFILES_FILE:-}" ]] \
  || hold FASTDDS_XML_OVERRIDE_UNVERIFIED_HOLD
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
echo 'AXIA_G07_FASTDDS_BUILTIN_TRANSPORTS=UDPv4 OWNER_SHM_333MS_MITIGATION_CI_FIRST'
export QT_QPA_PLATFORM=xcb
unset LIBGL_ALWAYS_SOFTWARE || true

BASE="$HOME/axia_g07_task04_owner_moving"
mkdir -p "$BASE" && chmod 700 "$BASE"
OUT="$(mktemp -d "$BASE/owner-moving-XXXXXXXX")" || hold EVIDENCE_DIRECTORY_FAILED
chmod 700 "$OUT"
# Domain/partition manifest is written after verified DDS graph preflight.
# Observation only, never a startup gate. Host clock time-to-GUI evidence.
STARTUP_T0_MS="$(date +%s%3N)"
printf 'phase\telapsed_ms\tutc_epoch_ms\n' > "$OUT/startup_timing.tsv"
startup_mark() {
  local now
  now="$(date +%s%3N)"
  printf '%s\t%s\t%s\n' "$1" "$((now-STARTUP_T0_MS))" "$now" >> "$OUT/startup_timing.tsv"
}
startup_mark owner_evidence_ready

set +u
source /opt/ros/jazzy/setup.bash
if [[ -n "${AXIA_NAV2_OVERLAY_SETUP:-}" ]];then
  [[ -r "$AXIA_NAV2_OVERLAY_SETUP" ]] || hold NAV2_OVERLAY_MISSING
  source "$AXIA_NAV2_OVERLAY_SETUP"
elif [[ -r "$HOME/axia_p1_abc_verification/results/p1-nav2-official-overlay/install/setup.bash" ]];then
  source "$HOME/axia_p1_abc_verification/results/p1-nav2-official-overlay/install/setup.bash"
fi
set -u
[[ "${ROS_DISTRO:-}" == jazzy ]] || hold ROS_DISTRO_MISMATCH

# Field 99PX1WNS/8ULG28b7: two disjoint /clock sources alternated within
# same ROS_DOMAIN_ID=86, while GZ_PARTITION was already unique. ROS DDS graph
# isolation must be checked BEFORE launching a Gazebo /clock bridge or Goal.
# Exact reviewed helper is pinned to its immutable Git blob and cached.
readonly DOMAIN_HELPER_COMMIT='977d759e751c08d6d3d22b5c9b53e2d114ad58ae'
readonly DOMAIN_HELPER_GIT_BLOB='8c8db2e361216ec34c1d7a5d19e0ddb436af7fa3'
DOMAIN_HELPER_CACHE="$HOME/.cache/axia/g07_task04_domain_helper"
mkdir -p "$DOMAIN_HELPER_CACHE" || hold DOMAIN_HELPER_CACHE_DIRECTORY_FAILED
[[ ! -L "$DOMAIN_HELPER_CACHE" ]] || hold DOMAIN_HELPER_CACHE_SYMLINK_DENIED
DOMAIN_HELPER="$DOMAIN_HELPER_CACHE/$DOMAIN_HELPER_GIT_BLOB.py"
if [[ ! -r "$DOMAIN_HELPER" ]] || [[ "$(git hash-object "$DOMAIN_HELPER" 2>/dev/null)" != "$DOMAIN_HELPER_GIT_BLOB" ]];then
  tmpdomain="$(mktemp "$DOMAIN_HELPER_CACHE/.download-XXXXXXXX")" || hold DOMAIN_HELPER_TEMP_FAILED
  if ! curl -fsSL --retry 3 --max-time 60 \
       "https://raw.githubusercontent.com/$REVIEW_REPO/$DOMAIN_HELPER_COMMIT/scripts/axia_g07_task04_select_free_domain.py" \
       -o "$tmpdomain";then
    rm -f "$tmpdomain";hold DOMAIN_HELPER_DOWNLOAD_FAILED
  fi
  if [[ "$(git hash-object "$tmpdomain")" != "$DOMAIN_HELPER_GIT_BLOB" ]];then
    rm -f "$tmpdomain";hold DOMAIN_HELPER_BLOB_MISMATCH
  fi
  mv "$tmpdomain" "$DOMAIN_HELPER"
  chmod 600 "$DOMAIN_HELPER"
fi
if ! selected_domain="$(python3 "$DOMAIN_HELPER" \
       --output "$OUT/domain_selection.json" \
       --requested "${AXIA_G07_TASK04_DOMAIN_ID:-}" 2>"$OUT/domain_selection.log")";then
  echo 'AXIA_G07_TASK04_FOREIGN_CLOCK_DOMAIN_PROBE_BLOCKED' >&2
  hold FOREIGN_CLOCK_DOMAIN_OR_DISCOVERY_REJECTED
fi
[[ "$selected_domain" =~ ^[0-9]+$ ]] && ((selected_domain<=101)) \
  || hold DOMAIN_PROBE_RETURN_INVALID
export ROS_DOMAIN_ID="$selected_domain"
export GZ_PARTITION="axia_p2_task04_${ROS_DOMAIN_ID}_${BASHPID}_$(date -u +%s)"
[[ "$GZ_PARTITION" =~ ^[A-Za-z0-9_]+$ ]] || hold BAD_GZ_PARTITION
printf 'student_sha=%s\nci_review_sha=%s\nci_l2_run=%s\ndomain=%s\npartition=%s\n' \
 "$STUDENT_SHA" "$REVIEW_SHA" "$CI_L2_RUN" "$ROS_DOMAIN_ID" "$GZ_PARTITION" > "$OUT/manifest.txt"
echo "AXIA_G07_TASK04_ROS_DOMAIN_SELECTED=$ROS_DOMAIN_ID CLOCK_PUBLISHERS_BEFORE_LAUNCH=0"
startup_mark clean_ros_domain_verified

for pkg in nav2_bringup nav2_minimal_tb3_sim ros_gz_sim;do
  ros2 pkg prefix "$pkg" >> "$OUT/official_packages.txt" 2>&1 || hold "OFFICIAL_PACKAGE_$pkg"
done
# Build-only packages, only if missing. Keep installed official ROS/Nav2
# userspace frozen; do not silently upgrade packages or safety components.
if [[ ! -r /usr/include/gz/sim8/gz/sim/System.hh ]] || ! command -v cmake >/dev/null 2>&1 || ! command -v c++ >/dev/null 2>&1;then
  command -v sudo >/dev/null 2>&1 || hold GAZEBO_BUILD_DEPS_SUDO_REQUIRED
  echo 'AXIA_G07_TASK04_BUILD_ONLY_DEPS_INSTALL_REQUESTED'
  sudo apt-get update -qq || hold GAZEBO_BUILD_DEPS_APT_UPDATE_FAILED
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends --no-upgrade cmake g++ libgz-sim8-dev || hold GAZEBO_BUILD_DEPS_INSTALL_FAILED
  [[ -r /usr/include/gz/sim8/gz/sim/System.hh ]] && command -v cmake >/dev/null 2>&1 && command -v c++ >/dev/null 2>&1 || hold GAZEBO_BUILD_DEPS_STILL_MISSING
fi

# No second private source: fetch both exact reviewed PUBLIC commits into caches.
export GIT_TERMINAL_PROMPT=0
fetch_pinned() {
  local repo="$1" sha="$2" cache="$3" kind="$4"
  mkdir -p "$(dirname "$cache")"
  if [[ ! -d "$cache/.git" ]];then
    [[ ! -e "$cache" ]] || hold "${kind}_CACHE_NOT_GIT"
    git init -q "$cache" || hold "${kind}_GIT_INIT_FAILED"
    git -C "$cache" remote add origin "https://github.com/$repo.git"
  fi
  [[ "$(git -C "$cache" remote get-url origin)" == "https://github.com/$repo.git" ]] || hold "${kind}_WRONG_ORIGIN"
  git -C "$cache" fetch -q --no-tags --depth 1 origin "$sha" || hold "${kind}_SHA_FETCH_FAILED"
  git -C "$cache" -c advice.detachedHead=false checkout -q --detach FETCH_HEAD || hold "${kind}_CHECKOUT_FAILED"
  [[ "$(git -C "$cache" rev-parse HEAD)" == "$sha" ]] || hold "${kind}_SHA_MISMATCH"
  [[ -z "$(git -C "$cache" status --porcelain --untracked-files=no)" ]] || hold "${kind}_DIRTY_TREE"
  echo "AXIA_G07_TASK04_${kind}_SHA_VERIFIED=$sha"
}
STUDENT_CACHE="$HOME/.cache/axia/g07_task04_moving_student/$STUDENT_SHA"
REVIEW_CACHE="$HOME/.cache/axia/g07_task04_moving_ci/$REVIEW_SHA"
fetch_pinned "$STUDENT_REPO" "$STUDENT_SHA" "$STUDENT_CACHE" STUDENT
fetch_pinned "$REVIEW_REPO" "$REVIEW_SHA" "$REVIEW_CACHE" PUBLIC_CI
startup_mark pinned_source_verified
RUNTIME="$STUDENT_CACHE/block_B/day07/h01_runtime"
[[ -r "$RUNTIME/scripts/p2_no_goal_smoke_ci.sh" && -r "$RUNTIME/tools/p2_g07_task04_moving_review.py" ]] || hold RUNTIME_FILES_MISSING
bash -n "$RUNTIME/scripts/p2_no_goal_smoke_ci.sh" || hold STUDENT_SHELL_SYNTAX
export PYTHONPATH="$REVIEW_CACHE${PYTHONPATH:+:$PYTHONPATH}"

# Verify the exact official 25 Debian versions + five official file digests
# from the previously accepted Owner profile. Never interpret this as L3.
python3 "$RUNTIME/tools/p2_g07_owner_env_parity.py" --mode owner --output "$OUT/owner_parity.json" > "$OUT/owner_parity.log" 2>&1 || hold OWNER_CORE_PARITY_BLOCKED
python3 - "$OUT/owner_parity.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
assert r.get("status")=="CORE_PARITY_PASS" and r.get("mode")=="owner"
assert r.get("checked_packages")==25 and r.get("checked_official_files")==5
assert r.get("wsl_detected") is True
print("AXIA_G07_TASK04_OWNER_CORE_PARITY_25_5_PASS")
PY
startup_mark owner_core_parity_ready

# WSLg D3D12 genuine adapter. No long NO_GOAL demo rerun.
GPU=''
for adapter in NVIDIA Intel;do
  if env -u LIBGL_ALWAYS_SOFTWARE GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME="$adapter" timeout 12s glxinfo -B > "$OUT/glx_$adapter.txt" 2>&1;then
    if grep -Eiq "OpenGL renderer string: D3D12.*$adapter" "$OUT/glx_$adapter.txt";then GPU="$adapter";break;fi
  fi
done
[[ -n "$GPU" ]] || hold WSLG_D3D12_ADAPTER_NOT_VERIFIED
# Publish only the already-GLX-verified GUI adapter. Do NOT set D3D12
# process-globally: Gazebo server and ROS safety/sensor children keep
# their original runtime environment.
export AXIA_G07_TASK04_GUI_D3D12_ADAPTER="$GPU"
unset GALLIUM_DRIVER MESA_D3D12_DEFAULT_ADAPTER_NAME || true
# Real Gazebo software-rendered gpu_lidar: same as verified public CI L2.
# Student runner reasserts this before launching the one Gazebo server;
# only gz sim -g / rviz2 GUI children explicitly opt out for D3D12 GPU.
export LIBGL_ALWAYS_SOFTWARE=1
echo "AXIA_G07_TASK04_WSLG_D3D12_GPU_SELECTED=$GPU"
startup_mark wslg_gpu_verified

# Read-only Gazebo8 contact witness. Cold configure was 116.4s on Owner
# 8ULG28b7 because every evidence run used a NEW CMake build directory.
# Use a private persistent binary cache keyed by the exact pinned source
# and Gazebo/compiler ABI. Never reuse a binary after any of these change.
NATIVE_BUILD_CACHE_ROOT="$HOME/.cache/axia/g07_task04_native_witness"
mkdir -p "$NATIVE_BUILD_CACHE_ROOT" || hold NATIVE_CACHE_CREATE_FAILED
[[ ! -L "$NATIVE_BUILD_CACHE_ROOT" ]] || hold NATIVE_CACHE_SYMLINK_DENIED
NATIVE_ABI_PACKAGES="$(dpkg-query -W -f='${Package}=${Version}\n' \
  libgz-sim8-dev libgz-sim8 libgz-transport13 libgz-msgs10 libsdformat14)" \
    || hold NATIVE_CACHE_ABI_PACKAGES_UNAVAILABLE
NATIVE_BUILD_CACHE_KEY="$(
  {
    printf 'student=%s\nsource=%s\narch=%s\n' "$STUDENT_SHA" \
      "$RUNTIME/tools/native_s02_public" "$(uname -m)"
    sha256sum "$RUNTIME/tools/native_s02_public/CMakeLists.txt" \
              "$RUNTIME/tools/native_s02_public/s02_witness.cc"
    printf '%s\n' "$NATIVE_ABI_PACKAGES"
    c++ -dumpfullversion -dumpversion
    cmake --version
  } | sha256sum | cut -d ' ' -f1
)"
[[ "$NATIVE_BUILD_CACHE_KEY" =~ ^[0-9a-f]{64}$ ]] || hold NATIVE_CACHE_KEY_INVALID
NATIVE_BUILD_DIR="$NATIVE_BUILD_CACHE_ROOT/$NATIVE_BUILD_CACHE_KEY"
mkdir -p "$NATIVE_BUILD_DIR" || hold NATIVE_CACHE_DIRECTORY_FAILED
[[ ! -L "$NATIVE_BUILD_DIR" ]] || hold NATIVE_CACHE_BUILD_SYMLINK_DENIED
# One cache writer. Never lock, clean, or signal any other Gazebo instance.
exec {NATIVE_CACHE_LOCK_FD}> "$NATIVE_BUILD_DIR/.build.lock"
flock -x "$NATIVE_CACHE_LOCK_FD" || hold NATIVE_CACHE_LOCK_FAILED
NATIVE_T0_MS="$(date +%s%3N)"
NATIVE_BUILD_CACHE_STATUS=MISS
CACHED_WITNESS="$NATIVE_BUILD_DIR/libaxia_g07_s02_ecm_witness.so"
if [[ -s "$CACHED_WITNESS" && -f "$NATIVE_BUILD_DIR/.witness.sha256" ]] \
   && (cd "$NATIVE_BUILD_DIR" && sha256sum --status -c .witness.sha256); then
  NATIVE_BUILD_CACHE_STATUS=HIT
  printf '%s\n' 'AXIA_G07_NATIVE_WITNESS_CONFIG_REUSED_SAME_PINNED_ABI' > "$OUT/native_build_config.log"
  printf '%s\n' 'AXIA_G07_NATIVE_WITNESS_COMPILE_REUSED_SAME_PINNED_ABI' > "$OUT/native_build.log"
else
  # Missing/corrupted binary cannot become a stale cache HIT.
  rm -f "$CACHED_WITNESS" "$NATIVE_BUILD_DIR/.witness.sha256"
  cmake -S "$RUNTIME/tools/native_s02_public" -B "$NATIVE_BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release > "$OUT/native_build_config.log" 2>&1 \
      || hold NATIVE_WITNESS_CONFIG_FAILED
  cmake --build "$NATIVE_BUILD_DIR" --parallel 2 > "$OUT/native_build.log" 2>&1 \
      || hold NATIVE_WITNESS_BUILD_FAILED
  [[ -s "$CACHED_WITNESS" ]] || hold NATIVE_WITNESS_MISSING
  (cd "$NATIVE_BUILD_DIR" && sha256sum libaxia_g07_s02_ecm_witness.so > .witness.sha256) \
      || hold NATIVE_CACHE_CHECKSUM_WRITE_FAILED
fi
NATIVE_T1_MS="$(date +%s%3N)"
mkdir -p "$OUT/native_build"
# Keep the *per-run* evidence binary and its SHA, not the shared CMake cache.
cp "$CACHED_WITNESS" "$OUT/native_build/libaxia_g07_s02_ecm_witness.so" \
  || hold NATIVE_WITNESS_COPY_FAILED
WITNESS="$OUT/native_build/libaxia_g07_s02_ecm_witness.so"
[[ -s "$WITNESS" ]] || hold NATIVE_WITNESS_MISSING
sha256sum "$WITNESS" > "$OUT/native_witness.sha256"
NATIVE_SHA256="$(sha256sum "$WITNESS" | cut -d ' ' -f1)"
python3 - "$OUT/native_witness_build_profile.json" "$STUDENT_SHA" \
  "$NATIVE_BUILD_CACHE_STATUS" "$NATIVE_BUILD_CACHE_KEY" \
  "$((NATIVE_T1_MS-NATIVE_T0_MS))" "$NATIVE_SHA256" <<'PY_CACHE_PROFILE'
import json,sys
from pathlib import Path
record=dict(schema="axia.g07.owner.native_witness_build_cache_v1",
            pinned_student_sha=sys.argv[2],cache_status=sys.argv[3],
            abi_cache_key=sys.argv[4],
            build_phase_wall_sec=round(int(sys.argv[5])/1000,3),
            output_binary_sha256=sys.argv[6],
            safety_ttl_changed=False,goal_sent=False)
Path(sys.argv[1]).write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
PY_CACHE_PROFILE
flock -u "$NATIVE_CACHE_LOCK_FD"
exec {NATIVE_CACHE_LOCK_FD}>&-
echo "AXIA_G07_NATIVE_WITNESS_CACHE_STATUS=$NATIVE_BUILD_CACHE_STATUS"
echo "AXIA_G07_NATIVE_WITNESS_CACHE_WALL_SEC=$((NATIVE_T1_MS-NATIVE_T0_MS))ms"
startup_mark native_witness_ready
export GZ_SIM_SYSTEM_PLUGIN_PATH="$OUT/native_build${GZ_SIM_SYSTEM_PLUGIN_PATH:+:$GZ_SIM_SYSTEM_PLUGIN_PATH}"
export AXIA_G07_TASK03_WITNESS_SHA256="$(sha256sum "$WITNESS" | cut -d ' ' -f1)"
export AXIA_P2_SMOKE_RESULTS="$OUT/native"
export AXIA_G07_TASK03_WITNESS_REPORT="$OUT/native/s02_ecm_witness.json"
export AXIA_G07_TASK04_EXPECTED_STUDENT_SHA="$STUDENT_SHA"
mkdir -p "$OUT/native"

# Read-only WSLg X11 window observer; automatically exits on both windows.
(
  rv=0;gz=0
  trap 'printf "rviz=%s\ngazebo=%s\n" "$rv" "$gz" > "$OUT/gui_windows.txt"' EXIT
  for ((i=0;i<360;i++));do
    tree="$(timeout 3s xwininfo -root -tree 2>/dev/null || true)"
    if [[ "$rv" == 0 ]] && grep -Eiq RViz <<< "$tree";then
      rv=1
      startup_mark first_rviz_window_detected
    fi
    if [[ "$gz" == 0 ]] && grep -Eiq Gazebo <<< "$tree";then
      gz=1
      startup_mark first_gazebo_window_detected
    fi
    if [[ "$rv" == 1 && "$gz" == 1 ]];then break;fi
    sleep 2
  done
) &
WATCH_PID=$!
startup_mark owner_runner_start
echo "AXIA_G07_TASK04_OWNER_MOVING_BEGIN student_sha=$STUDENT_SHA public_l2=$CI_L2_RUN"
echo 'Gazebo and RViz open automatically; one YES-P2-G07-GOAL consent is requested on YOUR /dev/tty only after safety readiness.'
echo 'Original ROS logs and rosbag remain in a PRIVATE HOME evidence directory.'

# Foreground is intentional: controlling TTY must reach the real ROS runner.
# Each Gazebo/Nav2 process and GUI is managed by the original Student shell.
RUNNER_RC=0
(cd "$RUNTIME" && timeout --foreground --signal=TERM --kill-after=25s 1100s bash scripts/p2_no_goal_smoke_ci.sh) > "$OUT/native_runner.log" 2>&1 || RUNNER_RC=$?
startup_mark owner_runner_completed
if [[ -n "$WATCH_PID" ]] && kill -0 "$WATCH_PID" 2>/dev/null;then
  kill -TERM "$WATCH_PID" 2>/dev/null || true
fi
wait "$WATCH_PID" 2>/dev/null || true
WATCH_PID=''
echo "AXIA_G07_TASK04_OWNER_NATIVE_RUNNER_RC=$RUNNER_RC"
if [[ "$RUNNER_RC" -ne 0 ]];then
  # Educational MVP scope: a real physical CLEAR/SLOW/STOP + exact UUID
  # cancel may have completed while the unrelated localization lifecycle ACK
  # timed out during cleanup. All original artifacts and formal HOLD remain.
  RV=0;GZ=0
  grep -Fxq 'rviz=1' "$OUT/gui_windows.txt" && RV=1 || true
  grep -Fxq 'gazebo=1' "$OUT/gui_windows.txt" && GZ=1 || true
  if [[ "$RV" == 1 && "$GZ" == 1 ]] \
     && python3 "$REVIEW_CACHE/scripts/axia_g07_mvp_visual_verdict.py" \
       --motion "$OUT/native/g07_ci_moving/ci_moving_goal_result.json" \
       --shutdown "$OUT/native/g07_ordered_shutdown.json" \
       --gui-windows 2 --source-sha "$STUDENT_SHA" \
       --output "$OUT/task04_mvp_visual_verdict.json"; then
    python3 - "$OUT/task04_mvp_visual_verdict.json" "$OUT/task04_owner_verdict.json" "$STUDENT_SHA" "$CI_L2_RUN" <<'PY_MVP'
import json,sys
from pathlib import Path
v=json.loads(Path(sys.argv[1]).read_text())
assert v["status"]=="MVP_OWNER_NUMERICAL_CANDIDATE_FORMAL_SHUTDOWN_HOLD"
result={"schema":"axia_g07_task04_owner_mvp_visual_candidate_v1",
        "status":"MVP_PHYSICAL_DEMO_CANDIDATE_FORMAL_SHUTDOWN_HOLD",
        "source_sha":sys.argv[3], "public_ci_moving_source_run":int(sys.argv[4]),
        "physical_clear_slow_stop_cancel":True,
        "localization_shutdown_ack":False,
        "visual_content_verified":False, "owner_moving_l3_accepted":False,
        "axia_mvp_demo_accepted":False,"certified_estop":False}
Path(sys.argv[2]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
PY_MVP
    FIRST_FAILURE='FORMAL_LOCALIZATION_SHUTDOWN_TIMEOUT_AFTER_DEMO'
    NUMERICAL='MVP_PHYSICAL_DEMO_CANDIDATE_VISUAL_REVIEW_PENDING'
    echo 'AXIA_G07_TASK04_OWNER_MVP_CLEAR_SLOW_STOP_GOAL_CANCEL_CANDIDATE'
    echo 'AXIA_G07_TASK04_OWNER_FORMAL_SHUTDOWN_HOLD VISUAL_REVIEW_PENDING CERTIFIED_ESTOP=false'
    exit 0
  fi
  FIRST_FAILURE='NATIVE_RUNNER_FAILED_REVIEW_RAW'
  # Preserve the FIRST upstream safety failure instead of masking it with
  # the outer shell exception. The source wrote this file before raise.
  ORIGINAL_FIRST_FAILURE=''
  if [[ -s "$OUT/native/g07_ci_pregoal/pregoal_baseline.json" ]];then
    ORIGINAL_FIRST_FAILURE="$(python3 - "$OUT/native/g07_ci_pregoal/pregoal_baseline.json" <<'PY_FIRST'
import json,sys
try:
    with open(sys.argv[1],encoding="utf-8") as f:
        record=json.load(f)
    if record.get("status")=="BLOCKED":
        print(record.get("first_failure",""))
except (OSError,ValueError,TypeError):
    pass
PY_FIRST
)" || ORIGINAL_FIRST_FAILURE=''
    if [[ "$ORIGINAL_FIRST_FAILURE" =~ ^OWNER_PREGOAL_[A-Z0-9_]+$ ]];then
      FIRST_FAILURE="$ORIGINAL_FIRST_FAILURE"
      echo "AXIA_G07_TASK04_UPSTREAM_FIRST_FAILURE=$FIRST_FAILURE"
    fi
  fi
  [[ ! -r "$OUT/native/g07_ci_moving/ci_moving_goal_result.json" ]] || cp "$OUT/native/g07_ci_moving/ci_moving_goal_result.json" "$OUT/first_native_goal_result.json"
  hold "$FIRST_FAILURE"
fi
RV=0;GZ=0
grep -Fxq 'rviz=1' "$OUT/gui_windows.txt" && RV=1 || true
grep -Fxq 'gazebo=1' "$OUT/gui_windows.txt" && GZ=1 || true
[[ "$RV" == 1 && "$GZ" == 1 ]] || hold MOVING_GUI_WINDOWS_MISSING
echo 'AXIA_G07_TASK04_OWNER_WSLG_GAZEBO_RVIZ_WINDOWS_PASS'

# Strict formal numeric verifier ALWAYS runs first. FV17z53O showed a
# REAL, completed physical Goal but original Owner/CI evidence profiles
# disagreed; after parity repair, a cross-topic RMW wall-clock regression may
# still be a FORMAL HOLD. Never replace that raw fact with a safety PASS.
OWNER_REVIEW_RC=0
python3 "$RUNTIME/tools/p2_g07_task04_moving_review.py" --motion-root "$OUT/native" --witness "$OUT/native/s02_ecm_witness.json" --source-sha "$STUDENT_SHA" --gui-windows 2 --output "$OUT/task04_owner_numeric_review.json" > "$OUT/owner_numeric_review.log" 2>&1 || OWNER_REVIEW_RC=$?
if [[ "$OWNER_REVIEW_RC" -ne 0 ]];then
  # Only the actual RMW timebase HOLD may qualify as a *classroom* demo
  # candidate, and only if every other physical/safety test is truly PASS.
  # Missing real Guard internal CM TTL, CM callback violation, invalid Goal,
  # nav shutdown failure, or any other HOLD remains a hard block.
  if python3 "$REVIEW_CACHE/scripts/axia_g07_task04_owner_demo_scope.py" \
       --numeric "$OUT/task04_owner_numeric_review.json" \
       --output "$OUT/task04_owner_mvp_scope.json" \
       > "$OUT/owner_mvp_scope.log" 2>&1;then
    python3 - "$OUT/task04_owner_mvp_scope.json" "$OUT/task04_owner_verdict.json" "$STUDENT_SHA" "$CI_L2_RUN" <<'PY_TIMEBASE'
import json,sys
from pathlib import Path
scope=json.loads(Path(sys.argv[1]).read_text())
assert scope["status"]=="MVP_OWNER_PHYSICAL_NUMERICAL_CANDIDATE_FORMAL_TIMEBASE_HOLD"
assert scope["formal_first_hold"]=="cm_source_and_observer_120ms"
assert scope["formal_safety_timing_accepted"] is False
assert scope["guard_actual_internal_cm_age_under_150ms"] is True
assert scope["owner_wsl2_l3_accepted"] is False
assert scope["axia_mvp_demo_accepted"] is False
assert scope["certified_estop"] is False
assert scope["source_sha"]==sys.argv[3]
v={"schema":"axia.g07.task04.owner_scoped_review_pending_v1",
   "status":"HOLD_RAW_REVIEW_AND_VISUAL_PENDING",
   "owner_moving_numeric_candidate":"DEMO_SCOPED_FORMAL_RMW_TIMEBASE_HOLD",
   "source_sha":sys.argv[3],"public_ci_native_l2_run":int(sys.argv[4]),
   "first_failure":"FORMAL_RMW_TIMEBASE_HOLD",
   "formal_first_hold":scope["formal_first_hold"],
   "original_numeric_first_failure":scope["first_failure_preserved"],
   "formal_safety_timing_accepted":False,
   "owner_moving_l3_accepted":False,"axia_mvp_demo_accepted":False,
   "visual_content_verified":False,"certified_estop":False}
Path(sys.argv[2]).write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
print("AXIA_G07_TASK04_OWNER_FORMAL_RMW_TIMEBASE_HOLD "
      "PHYSICAL_GOAL_CANDIDATE_ONLY CERTIFIED_ESTOP=false")
PY_TIMEBASE
    FIRST_FAILURE='FORMAL_RMW_TIMEBASE_HOLD_ONLY'
    NUMERICAL='PHYSICAL_DEMO_CANDIDATE_FORMAL_RMW_HOLD'
    exit 0
  fi
  hold NATIVE_NUMERICAL_REVIEW_BLOCKED
fi
python3 - "$OUT/task04_owner_numeric_review.json" "$OUT/task04_owner_verdict.json" "$STUDENT_SHA" "$CI_L2_RUN" <<'PY'
import json,sys
from pathlib import Path
data=json.loads(Path(sys.argv[1]).read_text())
expected="TASK04_OWNER_WSL2_NUMERICAL_CANDIDATE_REVIEW_PENDING"
assert data.get("status")==expected and data.get("first_failure")=="NONE"
assert all(data.get("checks",{}).values()) and data.get("scenario_scope")=="owner"
v={"schema":"axia_g07_task04_owner_l3_local_review_pending_v1",
   "status":"HOLD_RAW_REVIEW_AND_VISUAL_PENDING",
   "owner_moving_numeric_candidate":"PASS_SCOPED",
   "formal_safety_timing_accepted":False,
   "source_sha":sys.argv[3],"public_ci_native_l2_run":int(sys.argv[4]),
   "first_failure":"NONE","native_checks":data["checks"],
   "numerical_review":"task04_owner_numeric_review.json",
   "gui_windows_detected":True,"visual_content_verified":False,
   "owner_moving_l3_accepted":False,"axia_mvp_demo_accepted":False,
   "certified_estop":False}
Path(sys.argv[2]).write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
print("AXIA_G07_TASK04_OWNER_SINGLE_NATIVE_NUMERICAL_CANDIDATE_PASS_SCOPED")
print("AXIA_G07_TASK04_OWNER_VISUAL_AND_RAW_REVIEW_PENDING")
PY
FIRST_FAILURE='NONE'
NUMERICAL='PASS_SCOPED_RAW_REVIEW_PENDING'
exit 0
