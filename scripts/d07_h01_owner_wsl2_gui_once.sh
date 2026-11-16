#!/usr/bin/env bash
# AXIA D07-H01 — Owner WSL2 scoped acceptance, actual ROS/Gazebo GUI.
# Fixed verified CI L2 #43793585641. Does not expose private solution code.
set -Eeuo pipefail
umask 077
SOURCE_SHA="0e16c3781cdee603518a653f120a3be352e5f7b2"
INSTRUCTOR="silverbjin/axia-robot-safety-instructor"
BRANCH="feat/d07-h01-gui-rviz-no-goal-20261115"
CI_L2_URL="https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43793585641"
MODE="${1:---run}"
case "$MODE" in --self-check|--doctor|--run) ;; *)
  echo D07_H01_OWNER_USAGE=--self-check\|--doctor\|--run >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo D07_H01_OWNER_BAD_ARGUMENT_COUNT >&2; exit 2; }
[[ "$SOURCE_SHA" =~ ^[a-f0-9]{40}$ ]] || exit 2
if [[ "$MODE" == --self-check ]]; then
  echo "D07_H01_OWNER_PUBLIC_BOOTSTRAP_L0_PASS PRIVATE_SHA=$SOURCE_SHA NO_ROS_NO_GAZEBO_NO_GOAL"
  exit 0
fi

[[ -r /opt/ros/jazzy/setup.bash ]] || {
  echo D07_H01_OWNER_JAZZY_REQUIRED >&2; exit 2;
}
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo D07_H01_OWNER_WSL2_REQUIRED >&2; exit 2;
}
[[ -n "${DISPLAY:-}" ]] || {
  echo D07_H01_OWNER_WSLG_DISPLAY_REQUIRED >&2; exit 2;
}
for cmd in git python3 ros2 gz rviz2 colcon setsid timeout tar sha256sum; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "D07_H01_OWNER_MISSING_EXECUTABLE=$cmd" >&2;exit 2
  fi
done
set +u
source /opt/ros/jazzy/setup.bash
if [[ -n "${AXIA_NAV2_OVERLAY_SETUP:-}" ]]; then
  [[ -r "$AXIA_NAV2_OVERLAY_SETUP" ]] || {
    echo D07_H01_OWNER_SPECIFIED_NAV2_OVERLAY_MISSING >&2; exit 2;
  }
  source "$AXIA_NAV2_OVERLAY_SETUP"
elif [[ -r "$HOME/axia_p1_abc_verification/results/p1-nav2-official-overlay/install/setup.bash" ]]; then
  source "$HOME/axia_p1_abc_verification/results/p1-nav2-official-overlay/install/setup.bash"
fi
set -u
for pkg in nav2_bringup nav2_minimal_tb3_sim ros_gz_sim; do
  if ! ros2 pkg prefix "$pkg" >/dev/null 2>&1; then
    echo "D07_H01_OWNER_MISSING_OFFICIAL_ROS_PACKAGE=$pkg" >&2;exit 2
  fi
done
if [[ "$MODE" == --doctor ]]; then
  echo "D07_H01_OWNER_DOCTOR_PASS_NO_GAZEBO_NO_GOAL PRIVATE_SHA=$SOURCE_SHA"
  echo "D07_H01_OWNER_CI_L2_EVIDENCE=$CI_L2_URL"
  exit 0
fi
if command -v gh >/dev/null 2>&1 && gh auth status -h github.com >/dev/null 2>&1; then
  gh auth setup-git -h github.com >/dev/null 2>&1 || true
fi
export GIT_TERMINAL_PROMPT=0
CACHE="$HOME/.cache/axia/d07_h01_owner/$SOURCE_SHA"
mkdir -p "$(dirname "$CACHE")"
if [[ ! -d "$CACHE/.git" ]]; then
  [[ ! -e "$CACHE" ]] || { echo D07_H01_OWNER_CACHE_NOT_GIT >&2;exit 2; }
  if ! git clone -q --filter=blob:none --no-checkout --single-branch --branch "$BRANCH" "https://github.com/$INSTRUCTOR.git" "$CACHE"; then
    echo D07_H01_OWNER_PRIVATE_CLONE_DENIED_AUTH_OR_NETWORK >&2
    echo 'Authenticate to the private Instructor repository using gh auth login or configured Git credentials.' >&2
    exit 2
  fi
fi
if ! git -C "$CACHE" cat-file -e "$SOURCE_SHA^{commit}" 2>/dev/null; then
  git -C "$CACHE" fetch -q --filter=blob:none origin "$BRANCH" || {
    echo D07_H01_OWNER_PINNED_COMMIT_NOT_FETCHED >&2; exit 2;
  }
fi
git -C "$CACHE" checkout -q --detach "$SOURCE_SHA"
[[ "$(git -C "$CACHE" rev-parse HEAD)" == "$SOURCE_SHA" ]] || {
  echo D07_H01_OWNER_SOURCE_SHA_MISMATCH >&2;exit 2;
}
[[ -z "$(git -C "$CACHE" status --porcelain --untracked-files=no)" ]] || {
  echo D07_H01_OWNER_SOURCE_TREE_DIRTY >&2;exit 2;
}

RUN_ID="d07-h01-$(date -u +%Y%m%dT%H%M%SZ)-$$"
BASE="$HOME/axia_d07_h01_wsl2_acceptance"
OUT="$BASE/$RUN_ID"
mkdir -p "$OUT"
chmod 700 "$OUT"
export ROS_DOMAIN_ID="${AXIA_D07_OWNER_ROS_DOMAIN_ID:-65}"
[[ "$ROS_DOMAIN_ID" =~ ^[0-9]+$ && "$ROS_DOMAIN_ID" -le 101 ]] || {
  echo D07_H01_OWNER_BAD_ROS_DOMAIN_ID >&2;exit 2;
}
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_PARTITION="axia_p2_d07_owner_${ROS_DOMAIN_ID}_$$_$(date +%s)"
export AXIA_P2_SMOKE_RESULTS="$OUT/real-l2"
export AXIA_D07_GUI_EVIDENCE_DIR="$OUT/rviz"
export AXIA_D07_GUI_HOLD_S="${AXIA_D07_OWNER_HOLD_S:-10}"
export AXIA_G07_CI_SIM_GOAL_ALLOWED=0
export AXIA_P0_SIM_ONLY=1
unset GITHUB_ACTIONS
printf 'PRIVATE_SOURCE_SHA=%s\nCI_L2_URL=%s\nROS_DOMAIN_ID=%s\nGZ_PARTITION=%s\n' \
  "$SOURCE_SHA" "$CI_L2_URL" "$ROS_DOMAIN_ID" "$GZ_PARTITION" > "$OUT/runtime.txt"
echo "D07_H01_OWNER_WSL2_START source_sha=$SOURCE_SHA run_id=$RUN_ID no_moving_goal=1"
echo "D07_H01_OWNER_GUI_CHECK=Observe three phases in Gazebo/RViz2; screenshots optional for final visual review"
echo "D07_H01_OWNER_LOG_ROOT=$OUT"

# Exactly one private owner script; all ROS/Gazebo launch children are owned
# and torn down by its original signal-managed p2_no_goal_smoke_ci.sh.
# Do not ever use global pkill or wsl --shutdown.
OWNER=''
cleanup_owned() {
  if [[ -n "$OWNER" ]] && kill -0 "$OWNER" 2>/dev/null; then
    kill -TERM -- "-$OWNER" 2>/dev/null || true
    wait "$OWNER" 2>/dev/null || true
  fi
}
trap cleanup_owned EXIT
setsid timeout --signal=TERM --kill-after=20s 1000s \
  bash -c 'cd "$1"; exec bash scripts/d07_h01_gui_no_goal_once.sh --run' _ "$CACHE" \
  > "$OUT/owner_stdout.log" 2>&1 &
OWNER=$!
RVIZ=0
GAZEBO=0
if command -v xwininfo >/dev/null 2>&1; then
  XWININFO_AVAILABLE=1
else
  XWININFO_AVAILABLE=0
fi
while kill -0 "$OWNER" 2>/dev/null; do
  if (( XWININFO_AVAILABLE )); then
    windows="$(xwininfo -root -tree 2>/dev/null || true)"
    if grep -Eiq 'RViz' <<< "$windows"; then RVIZ=1; fi
    if grep -Eiq 'Gazebo' <<< "$windows"; then GAZEBO=1; fi
  fi
  sleep 2
done
set +e
wait "$OWNER"
RC=$?
set -e
OWNER=''
echo "D07_H01_OWNER_RUNTIME_RC=$RC RVIZ_X11=$RVIZ GAZEBO_X11=$GAZEBO XWININFO_AVAILABLE=$XWININFO_AVAILABLE"
{
  printf 'runtime_rc=%s\nrviz_window=%s\ngazebo_window=%s\nxwininfo_available=%s\n' \
    "$RC" "$RVIZ" "$GAZEBO" "$XWININFO_AVAILABLE"
} > "$OUT/window-verdict.txt"

if [[ "$RC" == 0 ]]; then
  set +e
  python3 - "$OUT" "$CACHE" "$SOURCE_SHA" "$RVIZ" "$GAZEBO" <<'PY'
import json,sys
from pathlib import Path
out,repo,sha=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]
rviz,gazebo=int(sys.argv[4]),int(sys.argv[5])
sys.path.insert(0,str(repo/"tools"))
from d07_h01_path_visual import assess_gui_stages
root=out/"real-l2"
geometry=json.loads((root/"d07_h01_geometry"/"d07_h01_geometry.json").read_text())
phase_lines=(root/"d07_h01_geometry"/"phase_evidence.jsonl").read_text().splitlines()
phases=[json.loads(row) for row in phase_lines]
assert geometry.get("source_sha")==sha
assert geometry.get("goal_sent") is False
assert geometry.get("real_nav2") is True
assert geometry.get("real_laser_scan") is True
assert geometry.get("actual_costmap_obstacle_observed") is True
assert geometry.get("route_oracle",{}).get("geometry_ready") is True
assert geometry.get("obstacle_restored_away") is True
assert geometry.get("certified_estop") is False
assert geometry.get("formal_accepted") is False
verdict=assess_gui_stages(phases,source_sha=sha,actual_ros=True,
    actual_gazebo=geometry.get("obstacle_pose_native_ack") is True,
    rviz_window=rviz==1)
report={
    "schema":"axia_d07_h01_owner_wsl2_local_l3_verdict_v1",
    "source_sha":sha,"actual_ros":True,"actual_gazebo":True,
    "gazebo_window_detected":gazebo==1,"rviz_window_detected":rviz==1,
    "phases":phases,"gui_evidence":verdict,
    "moving_goal_admitted":False,"certified_estop":False,
    "user_visual_content_verified":False,
    "owner_l3_automated_candidate":verdict.get("ready") is True and gazebo==1,
    "formal_user_visual_acceptance":"PENDING_USER_CONFIRMATION"}
(out/"owner-local-verdict.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print("D07_H01_OWNER_PHASES",json.dumps(
    [{"stage":p["stage"],"pose_count":p["pose_count"],
      "path_stamp":p["source_header_stamp"],
      "rviz_subscriber":p["rviz_subscription_count"]} for p in phases],sort_keys=True))
print("D07_H01_OWNER_LOCAL_EVIDENCE",json.dumps({
    "ready":report["owner_l3_automated_candidate"],
    "gazebo_window_detected":report["gazebo_window_detected"],
    "rviz_window_detected":report["rviz_window_detected"],
    "user_visual_content_verified":False,"source_sha":sha},sort_keys=True))
assert report["owner_l3_automated_candidate"] is True,verdict
print("D07_H01_OWNER_WSL2_AUTOMATED_L3_CANDIDATE_PASS_VISUAL_CONFIRMATION_PENDING")
PY
  REVIEW_RC=$?
  set -e
else
  REVIEW_RC=2
fi
ARCHIVE="$BASE/$RUN_ID.tar.gz"
tar -czf "$ARCHIVE" -C "$BASE" "$RUN_ID"
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
if [[ "$RC" != 0 || "$REVIEW_RC" != 0 ]];then
  echo "D07_H01_OWNER_WSL2_HOLD first_terminal_rc=$RC evidence_rc=$REVIEW_RC"
  echo "D07_H01_OWNER_LOG_TAIL_BEGIN"
  tail -n 65 "$OUT/owner_stdout.log" || true
  echo "D07_H01_OWNER_LOG_TAIL_END"
  echo "D07_H01_OWNER_EVIDENCE_ARCHIVE=$ARCHIVE"
  exit 2
fi
echo "D07_H01_OWNER_EVIDENCE_ARCHIVE=$ARCHIVE"
echo "D07_H01_OWNER_WSL2_AUTOMATED_CANDIDATE_PASS_USER_GUI_VISUAL_REVIEW_PENDING"
echo "D07_H01_OWNER_MOVING_GOAL_CONTACT_AND_SAFETY_TTLS_NOT_ACCEPTED"
