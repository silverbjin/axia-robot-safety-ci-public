#!/usr/bin/env bash
# 2026-11-15 validated *Xvfb* rollback GUI: separate headless Gazebo
# server + gz sim -g + RViz2 (public CI #43727149856). THIS ONLY DIAGNOSES
# OWNER WSLg NO_GOAL; it is NOT a G07/S02 acceptance or certified E-Stop.
set -Eeuo pipefail
umask 077

readonly PRIVATE_SHA="01d45d46b6eb6a05b1bd313d73f1fc3549575545"
readonly OLD_PUBLIC_SHA="70f9d4ece5c405cff0fb2d17843391856f3d8c08"
readonly VISUAL_SHA="0f66059d9110f8e667200bbca22396bd0c78c02e"
readonly CI_WORKFLOW_SHA="fa05a437db3b55d3e5e242322a4b66b7f71ae601"
readonly CI_RUN="43727149856"
readonly SRC_REPO="silverbjin/axia-robot-safety-ci-public"
readonly PRIVATE_REPO="silverbjin/axia-robot-safety-instructor"

stop() { echo "AXIA_G07_ROLLBACK_NO_GOAL_HOLD $*" >&2;exit 3; }
static_check() {
  [[ "$PRIVATE_SHA" =~ ^[a-f0-9]{40}$ && "$OLD_PUBLIC_SHA" =~ ^[a-f0-9]{40}$ &&
     "$VISUAL_SHA" =~ ^[a-f0-9]{40}$ && "$CI_WORKFLOW_SHA" =~ ^[a-f0-9]{40}$ ]] || return 3
  bash -n "$0" || return 3
  echo "AXIA_G07_ROLLBACK_STATIC_PASS_NO_ROS_NO_GOAL old_private=$PRIVATE_SHA"
  echo "AXIA_G07_ROLLBACK_STATIC_GUI_MODE=EXTERNAL_GZ_SIM_G_AND_RVIZ2"
}
[[ $# == 0 || ( $# == 1 && "$1" == --self-check ) ]] || stop UNKNOWN_ARGUMENTS
if [[ $# == 1 ]];then static_check;exit $?;fi

[[ "${GITHUB_ACTIONS:-}" != true ]] || stop OWNER_RENDER_NOT_IN_CI
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || stop UBUNTU24_REQUIRED
grep -Eqi 'wsl|microsoft' /proc/sys/kernel/osrelease || stop WSL2_REQUIRED
[[ -n "${DISPLAY:-}" && -r /opt/ros/jazzy/setup.bash ]] || stop WSLG_AND_JAZZY_REQUIRED
for cmd in gh git ros2 colcon gz rviz2 taskset nice python3 setsid timeout sha256sum tar;do
  command -v "$cmd" >/dev/null || stop "MISSING_$cmd"
done
gh auth status >/dev/null 2>&1 || stop PRIVATE_GH_AUTH_REQUIRED
actual="$(gh api "repos/$SRC_REPO/actions/runs/$CI_RUN" --jq '(.head_sha // "")+" "+(.status // "")+" "+(.conclusion // "")')" ||
  stop PRIOR_CI_PROVENANCE_NOT_AVAILABLE
[[ "$actual" == "$CI_WORKFLOW_SHA completed success" ]] || stop PRIOR_CI_PROVENANCE_MISMATCH
echo "AXIA_G07_ROLLBACK_20261115_CI_DUAL_GUI_PROVENANCE_PASS run=$CI_RUN WSLG_NOT_PROVEN"
static_check

readonly WORK="$(mktemp -d "$HOME/.axia_g07_rollback_source_XXXXXXXX")"
readonly OUT="$(mktemp -d "$HOME/axia_g07_rollback_gui_evidence_XXXXXXXX")"
readonly PRIVATE="$WORK/private"
readonly OLD_PUBLIC="$WORK/legacy_public"
readonly VISUAL="$WORK/visual"
readonly ROLLBACK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
mkdir -m 700 "$OUT/G07" "$OUT/visual"
LAUNCH_PID=''
GUI_PID=''
finish() {
  local final_rc="$?"
  trap - EXIT INT TERM
  set +e
  if [[ -n "$GUI_PID" ]];then
    kill -TERM "$GUI_PID" 2>/dev/null || true
    wait "$GUI_PID" 2>/dev/null || true
  fi
  if [[ -n "$LAUNCH_PID" ]];then
    kill -INT -- "-$LAUNCH_PID" 2>/dev/null || true
    for _ in {1..80};do
      kill -0 "$LAUNCH_PID" 2>/dev/null || break
      sleep .2
    done
    if kill -0 "$LAUNCH_PID" 2>/dev/null;then
      kill -TERM -- "-$LAUNCH_PID" 2>/dev/null || true
    fi
    wait "$LAUNCH_PID" 2>/dev/null || true
  fi
  cd "$HOME" 2>/dev/null || cd /
  # Preserve all raw logs and sidecar diagnostics. Worktree is only sources.
  ( cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 |
      sort -z | xargs -0 -r sha256sum > SHA256SUMS ) || true
  if [[ "$WORK" == "$HOME"/.axia_g07_rollback_source_* ]];then
    rm -rf -- "$WORK"
  fi
  echo "AXIA_G07_ROLLBACK_GUI_EVIDENCE=$OUT"
  echo "AXIA_G07_ROLLBACK_STATUS=NO_GOAL_WSLG_VISUAL_CONFIRMATION_REQUIRED rc=$final_rc"
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit "$final_rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Never execute a mutable main. Four independent exact commits.
git init -q "$OLD_PUBLIC"
git -C "$OLD_PUBLIC" remote add origin "https://github.com/$SRC_REPO.git"
git -C "$OLD_PUBLIC" fetch -q --depth 1 origin "$OLD_PUBLIC_SHA" || stop OLD_GUI_SOURCE_FETCH
git -C "$OLD_PUBLIC" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$OLD_PUBLIC" rev-parse HEAD)" == "$OLD_PUBLIC_SHA" ]] || stop OLD_GUI_SOURCE_PIN
git init -q "$VISUAL"
git -C "$VISUAL" remote add origin "https://github.com/$SRC_REPO.git"
git -C "$VISUAL" fetch -q --depth 1 origin "$VISUAL_SHA" || stop OLD_RVIZ_SOURCE_FETCH
git -C "$VISUAL" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$VISUAL" rev-parse HEAD)" == "$VISUAL_SHA" ]] || stop OLD_RVIZ_SOURCE_PIN

gh repo clone "$PRIVATE_REPO" "$PRIVATE" -- --quiet --no-checkout --filter=blob:none >/dev/null ||
  stop INSTRUCTOR_READ_FAILED
git -C "$PRIVATE" fetch -q --depth 1 origin "$PRIVATE_SHA" || stop INSTRUCTOR_PIN_FETCH_FAILED
git -C "$PRIVATE" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$PRIVATE" rev-parse HEAD)" == "$PRIVATE_SHA" ]] || stop INSTRUCTOR_PIN_MISMATCH
for f in "$OLD_PUBLIC/d06/scripts/g07_shared_gui_clients.sh" \
         "$OLD_PUBLIC/d06/live/d06_gui_cpu_plan.py" \
         "$VISUAL/d06/rviz/d06_safety_bubble.rviz" \
         "$PRIVATE/scripts/p4_g07_shared_runtime.sh" \
         "$PRIVATE/scripts/p2_g07_shared_staged_startup.sh";do
  [[ -s "$f" ]] || stop OLD_SOURCE_INCOMPLETE
done
# Exact old sidecar: both distinct native commands, never Cycle36 toggle.
grep -Fq 'nice -n 19 gz sim -g' "$OLD_PUBLIC/d06/scripts/g07_shared_gui_clients.sh" ||
  stop OLD_GZ_CLIENT_MISSING
! grep -Fq 'AXIA_G07_CYCLE36_INTEGRATED_GUI' "$OLD_PUBLIC/d06/scripts/g07_shared_gui_clients.sh" ||
  stop CYCLE36_SOURCE_LEAKED
[[ "$(grep -c 'nice -n 19 rviz2' "$OLD_PUBLIC/d06/scripts/g07_shared_gui_clients.sh")" -eq 1 ]] ||
  stop OLD_RVIZ_CLIENT_MISSING

set +u;source /opt/ros/jazzy/setup.bash;set -u
export ROS_DOMAIN_ID="$((55 + RANDOM % 90))"
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_PARTITION="axia_p2_g07_rollback_$$_$RANDOM"
export AXIA_P0_SIM_ONLY=1
export AXIA_G07_UNIFIED_GUI_SIDECAR=1
unset AXIA_G07_CYCLE36_INTEGRATED_GUI || true
unset QT_QPA_PLATFORM || true
printf 'ROS_DOMAIN_ID=%s\nGZ_PARTITION=%s\n' "$ROS_DOMAIN_ID" "$GZ_PARTITION" > "$OUT/G07/session.env"
echo "AXIA_G07_ROLLBACK_GAZEBO_HEADLESS_SERVER_SEPARATE_GZ_GUI_AND_RVIZ_NO_GOAL"
echo "AXIA_G07_ROLLBACK_DOMAIN=$ROS_DOMAIN_ID"
cd "$PRIVATE"
colcon build --base-paths ros2_ws/src --packages-select \
  axia_safety_supervisor axia_fault_injector axia_scenario_verifier \
  --event-handlers console_direct+ > "$OUT/build.log" 2>&1 || stop COLCON_BUILD_BLOCKED
set +u;source install/setup.bash;set -u
for pkg in nav2_bringup nav2_minimal_tb3_sim ros_gz_sim;do
  ros2 pkg prefix "$pkg" >/dev/null || stop "ROS_PKG_MISSING_$pkg"
done

WORLD="$(ros2 pkg prefix nav2_minimal_tb3_sim)/share/nav2_minimal_tb3_sim/worlds/tb3_sandbox.sdf.xacro"
WAFFLE="$(ros2 pkg prefix nav2_minimal_tb3_sim)/share/nav2_minimal_tb3_sim/urdf/gz_waffle.sdf.xacro"
python3 tools/p2_l3_world_overlay.py --source "$WORLD" \
  --output "$OUT/G07/g07_world.sdf.xacro" \
  --manifest "$OUT/G07/g07_world_manifest.json" > "$OUT/world.log" 2>&1 ||
    stop WORLD_OVERLAY_FAILED
python3 tools/p2_g07_demo_lidar_overlay.py --source "$WAFFLE" \
  --output "$OUT/G07/g07_demo_waffle.sdf.xacro" \
  --manifest "$OUT/G07/g07_demo_waffle_manifest.json" > "$OUT/waffle.log" 2>&1 ||
    stop WAFFLE_OVERLAY_FAILED

source scripts/p4_g07_shared_runtime.sh
LAUNCH="$PRIVATE/ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p2.launch.py"
axia_g07_shared_launch owner-gui "$LAUNCH" "$OUT/G07/g07_world.sdf.xacro" \
  "$OUT/G07/g07_demo_waffle.sdf.xacro" "$OUT/G07/launch.log" ||
    stop OFFICIAL_GAZEBO_LAUNCH_FAILED
LAUNCH_PID="$AXIA_G07_SHARED_LAUNCH_PID"
[[ "$(axia_g07_shared_headless_mode owner-gui)" == True ]] ||
  stop OLD_SEPARATED_HEADLESS_NOT_RESTORED
export AXIA_G07_OWNER_STARTUP_PARITY=1
if ! timeout --signal=TERM --kill-after=5s 480s \
   bash scripts/p2_g07_shared_staged_startup.sh \
     "$OUT/G07/startup_verdict.json" "$OUT/G07/initialpose.json" \
     > "$OUT/G07/staged_startup.log" 2>&1;then
  stop OFFICIAL_NAV2_STAGED_NO_GOAL_FAILED
fi
python3 - "$OUT/G07/startup_verdict.json" <<'PY' || stop NAV2_NOT_READY_NO_GOAL
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
assert d.get("status")=="SMOKE_READY"
assert d.get("goal_sent") is False and d.get("fault_injected") is False
PY
echo AXIA_G07_ROLLBACK_OFFICIAL_NAV2_STARTUP_READY_NO_GOAL

# ORIGINAL separate GUI, actual old command unchanged, WSLg candidate only.
bash "$OLD_PUBLIC/d06/scripts/g07_shared_gui_clients.sh" owner \
 "$OUT/visual" "$VISUAL" "$OLD_PUBLIC" > "$OUT/visual/sidecar.log" 2>&1 &
GUI_PID=$!
for _ in {1..100};do
  [[ -s "$OUT/visual/display_attestation.json" ]] && break
  kill -0 "$GUI_PID" 2>/dev/null || stop DUAL_GUI_SIDECAR_EXITED_EARLY
  sleep .4
done
[[ -s "$OUT/visual/display_attestation.json" ]] ||
  stop DUAL_GUI_START_NOT_ATTESTED
python3 - "$OUT/visual/display_attestation.json" <<'PY' || stop DUAL_GUI_RECEIPT_INVALID
import json,sys
v=json.load(open(sys.argv[1],encoding="utf-8"))
assert v.get("schema")=="axia.g07.shared_gui_display_client_v2"
assert v.get("headless_server_required") is True
assert v.get("display")=="WSLg_candidate"
assert v.get("wslg_verified") is False
PY
echo AXIA_G07_ROLLBACK_OLD_TWO_GUI_PROCESSES_LAUNCHED_WSLG_RENDER_NOT_PROVEN

# Exact first Owner pregoal failure root boundary, without moving fixture.
PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 \
 "$ROLLBACK/d06/live/g07_precycle36_readonly_preclear_probe.py" \
 --seconds 12 --output "$OUT/initial_scan_before_fixture.json" \
 > "$OUT/initial_scan_before_fixture.log" 2>&1 || true
cat "$OUT/initial_scan_before_fixture.log" || true

# Observe original two windows. The screenshot/pixel check is Owner-only.
hold_sec="${AXIA_G07_GUI_OBSERVE_SEC:-90}"
[[ "$hold_sec" =~ ^[0-9]{1,3}$ ]] || stop INVALID_GUI_OBSERVE_SECONDS
(( hold_sec >= 30 && hold_sec <= 180 )) || stop GUI_OBSERVE_SECONDS_OUT_OF_RANGE
echo "AXIA_G07_ROLLBACK_KEEP_GAZEBO_AND_RVIZ_ON_SCREEN seconds=$hold_sec"
echo 'No Nav2 Goal will be sent. Check both windows visually.'
sleep "$hold_sec"
kill -0 "$GUI_PID" 2>/dev/null || stop GUI_SIDECAR_NOT_ALIVE_AT_END
echo AXIA_G07_ROLLBACK_NO_GOAL_TWO_GUI_CLIENTS_ALIVE_WSLG_PIXELS_UNVERIFIED
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
