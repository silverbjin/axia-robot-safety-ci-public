#!/usr/bin/env bash
# AXIA G07 Task04 — exact-public-SHA Owner Moving Goal L3 candidate.
# Simulation-only. Manual controlling TTY consent is performed by the
# identical Student scenario runner AFTER real Nav2 and safety node readiness.
# No CI credentials, no second Gazebo server, no global process kill.
set -Eeuo pipefail
umask 077
readonly STUDENT_REPO='silverbjin/axia-robot-safety-student'
readonly STUDENT_SHA='6579e2eef7e99691da558cd2de1964fd26a04621'
readonly REVIEW_REPO='silverbjin/axia-robot-safety-ci-public'
readonly REVIEW_SHA='71b85c42ea474276fedd9f345521317b8c348b4e'
readonly CI_L2_RUN=44449459417
MODE="${1:---run}"
if [[ $# -gt 1 ]];then echo 'AXIA_G07_TASK04_FIRST_FAILURE=BAD_ARGUMENTS' >&2;exit 3;fi
case "$MODE" in
  --self-check|--run) ;;
  *) echo 'AXIA_G07_TASK04_FIRST_FAILURE=BAD_ARGUMENTS' >&2;exit 3 ;;
esac
if [[ "$MODE" == --self-check ]];then
  echo "AXIA_G07_TASK04_OWNER_MOVING_BOOTSTRAP_L0_PASS student_sha=$STUDENT_SHA l2_run=$CI_L2_RUN NO_ROS_NO_GAZEBO_NO_GOAL"
  echo 'AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi

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
    'task04_owner_verdict.json','task04_owner_numeric_review.json',
    'owner_numeric_review.log','owner_parity.json',
    'native/runtime.txt','native/clock_diagnostics.json',
    'native/g07_ci_pregoal/pregoal_baseline.json',
    'native/g07_ci_pregoal/owner_pregoal_l2.json',
    'native/g07_ci_pregoal.log',
    'native/g07_active_cm_native_parameters.json',
    'native/g07_ci_moving/ci_moving_goal_result.json',
    'native/g07_ordered_shutdown.json','native/g07_shutdown_audit.json',
    'native/staged_startup.log','native/g07_ordered_shutdown.log',
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

owner_consent_first_failure() {
  # The outer wrapper runs after the real ROS runner has exited. Keep the
  # FIRST narrow human-consent failure from its private log instead of the
  # generic NATIVE_RUNNER_FAILED_REVIEW_RAW. Do not parse or log the answer.
  local log="${1:-}"
  [[ -r "$log" ]] || return 0
  awk '
    $1 ~ /^(OWNER_GOAL_CONSENT_TIMEOUT|OWNER_GOAL_CONSENT_EOF_OR_TTY_ERROR|OWNER_GOAL_CONSENT_DENIED|OWNER_GOAL_CONSENT_TTY_UNAVAILABLE)$/ {
      print $1;exit
    }
  ' "$log"
}

# Owner is a real interactive WSL2 process, never a simulated CI actor.
[[ "${GITHUB_ACTIONS:-}" != true ]] || hold CI_AUTHORITY_DENIED
[[ -t 0 && -r /dev/tty ]] || hold OWNER_CONTROLLING_TTY_REQUIRED
grep -Eiq 'microsoft|wsl' /proc/sys/kernel/osrelease || hold WSL2_REQUIRED
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || hold UBUNTU_2404_REQUIRED
[[ -r /opt/ros/jazzy/setup.bash ]] || hold ROS_JAZZY_REQUIRED
[[ -n "${DISPLAY:-}" && -n "${XDG_RUNTIME_DIR:-}" ]] || hold WSLG_GUI_REQUIRED
for cmd in git bash python3 gz glxinfo xwininfo tar sha256sum timeout setsid colcon;do
  command -v "$cmd" >/dev/null 2>&1 || hold "MISSING_COMMAND_$cmd"
done

# Explicit negative CI authority; no GITHUB_ACTIONS spoof or shell auto-reply.
export AXIA_G07_CI_SIM_GOAL_ALLOWED=0
export AXIA_P0_SIM_ONLY=1
export AXIA_P2_G07_PHYSICAL_PREFLIGHT=1
export AXIA_G07_OWNER_STARTUP_PARITY=1
export AXIA_G07_CI_OWNER_BAG_PARITY=1
export AXIA_P2_G07_RELOCATED_OBSTACLE=1
export AXIA_G07_TASK02_SIMPLE_TF_CANDIDATE=1
export AXIA_G07_TASK04_OWNER_MOVING_L3=1
export AXIA_G07_TASK03_ECM_WITNESS=1
export AXIA_NAV2_USE_COMPOSITION=False
unset AXIA_G07_TASK03_FORMAL_CI AXIA_G07_TASK03_POSITIVE_ONLY AXIA_D07_H01_GUI_NO_GOAL AXIA_G07_TASK04_CI_GUI_MOVING || true
unset AXIA_G07_OWNER_COMMON_RUNNER_AUTHORIZED AXIA_P2_OWNER_PINNED_SHA || true
export ROS_DOMAIN_ID="${AXIA_G07_TASK04_DOMAIN_ID:-86}"
[[ "$ROS_DOMAIN_ID" =~ ^[0-9]+$ ]] && ((ROS_DOMAIN_ID<=101)) || hold BAD_ROS_DOMAIN
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_PARTITION="axia_p2_task04_${ROS_DOMAIN_ID}_${BASHPID}_$(date -u +%s)"
[[ "$GZ_PARTITION" =~ ^[A-Za-z0-9_]+$ ]] || hold BAD_GZ_PARTITION
export QT_QPA_PLATFORM=xcb
unset LIBGL_ALWAYS_SOFTWARE || true

BASE="$HOME/axia_g07_task04_owner_moving"
mkdir -p "$BASE" && chmod 700 "$BASE"
OUT="$(mktemp -d "$BASE/owner-moving-XXXXXXXX")" || hold EVIDENCE_DIRECTORY_FAILED
chmod 700 "$OUT"
printf 'student_sha=%s\nci_review_sha=%s\nci_l2_run=%s\ndomain=%s\npartition=%s\n' "$STUDENT_SHA" "$REVIEW_SHA" "$CI_L2_RUN" "$ROS_DOMAIN_ID" "$GZ_PARTITION" > "$OUT/manifest.txt"

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

# Read-only native Gazebo8 contact witness, identical source and build path to CI.
cmake -S "$RUNTIME/tools/native_s02_public" -B "$OUT/native_build" -DCMAKE_BUILD_TYPE=Release > "$OUT/native_build_config.log" 2>&1 || hold NATIVE_WITNESS_CONFIG_FAILED
cmake --build "$OUT/native_build" --parallel 2 > "$OUT/native_build.log" 2>&1 || hold NATIVE_WITNESS_BUILD_FAILED
WITNESS="$OUT/native_build/libaxia_g07_s02_ecm_witness.so"
[[ -s "$WITNESS" ]] || hold NATIVE_WITNESS_MISSING
sha256sum "$WITNESS" > "$OUT/native_witness.sha256"
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
    if grep -Eiq RViz <<< "$tree";then rv=1;fi
    if grep -Eiq Gazebo <<< "$tree";then gz=1;fi
    if [[ "$rv" == 1 && "$gz" == 1 ]];then break;fi
    sleep 2
  done
) &
WATCH_PID=$!
echo "AXIA_G07_TASK04_OWNER_MOVING_BEGIN student_sha=$STUDENT_SHA public_l2=$CI_L2_RUN"
echo 'Gazebo and RViz open automatically; one YES-P2-G07-GOAL consent is requested on YOUR /dev/tty only after safety readiness.'
echo 'Original ROS logs and rosbag remain in a PRIVATE HOME evidence directory.'

# Foreground is intentional: controlling TTY must reach the real ROS runner.
# Each Gazebo/Nav2 process and GUI is managed by the original Student shell.
RUNNER_RC=0
(cd "$RUNTIME" && timeout --foreground --signal=TERM --kill-after=25s 1100s bash scripts/p2_no_goal_smoke_ci.sh) > "$OUT/native_runner.log" 2>&1 || RUNNER_RC=$?
if [[ -n "$WATCH_PID" ]] && kill -0 "$WATCH_PID" 2>/dev/null;then
  kill -TERM "$WATCH_PID" 2>/dev/null || true
fi
wait "$WATCH_PID" 2>/dev/null || true
WATCH_PID=''
echo "AXIA_G07_TASK04_OWNER_NATIVE_RUNNER_RC=$RUNNER_RC"
if [[ "$RUNNER_RC" -ne 0 ]];then
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
  # Goal consent is an external physical interaction; its first error may
  # occur AFTER a successful PREGOAL baseline and BEFORE any Goal JSON.
  if [[ "$FIRST_FAILURE" == NATIVE_RUNNER_FAILED_REVIEW_RAW ]];then
    CONSENT_FIRST_FAILURE="$(owner_consent_first_failure "$OUT/native_runner.log")" || CONSENT_FIRST_FAILURE=''
    if [[ -n "$CONSENT_FIRST_FAILURE" ]];then
      FIRST_FAILURE="$CONSENT_FIRST_FAILURE"
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

python3 "$RUNTIME/tools/p2_g07_task04_moving_review.py" --motion-root "$OUT/native" --witness "$OUT/native/s02_ecm_witness.json" --source-sha "$STUDENT_SHA" --gui-windows 2 --output "$OUT/task04_owner_numeric_review.json" > "$OUT/owner_numeric_review.log" 2>&1 || hold NATIVE_NUMERICAL_REVIEW_BLOCKED
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
