#!/usr/bin/env bash
# AXIA G07 C29 — public bootstrap; private instructor code stays sealed.
# Existing official Nav2/TB3 simulator, ONE physical Gazebo obstacle,
# ONE explicit manual-Goal approval. Does not relax 150ms CM/300ms scan TTL.
# Scope: latest CI real Harmonic L2 success #44008818507, NOT a WSL2 PASS.
set -Eeuo pipefail
umask 077
readonly PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'
readonly PUBLIC_REPO='silverbjin/axia-robot-safety-ci-public'
readonly PRIVATE_SHA='275d68012a6a1cdc5ce466f2581281b9614c4381'
readonly CI_REAL_L2_RUN='44008818507'
readonly CI_WORKFLOW_COMMIT='70de0c1a52f11d194e1f2aa0f1b263db7f75912c'
readonly CI_RUNTIME_IMAGE_DIGEST='sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e'

hold() {
  printf 'AXIA_G07_C29_OWNER_HOLD_NO_GOAL %s\n' "$*" >&2
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false' >&2
  exit 3
}
self_check() {
  [[ "$PRIVATE_SHA" =~ ^[0-9a-f]{40}$ &&
     "$CI_WORKFLOW_COMMIT" =~ ^[0-9a-f]{40}$ &&
     "$CI_REAL_L2_RUN" =~ ^[0-9]+$ ]] || return 3
  bash -n "$0" || return 3
  echo "AXIA_G07_C29_OWNER_STATIC_L0_PASS private_sha=$PRIVATE_SHA ci_l2=$CI_REAL_L2_RUN"
  echo 'NO_ROS_NO_GAZEBO_NO_GOAL OWNER_L3_NOT_RUN'
}
if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# == 1 ]] || exit 3
  self_check; exit $?
fi
[[ $# == 0 ]] || hold 'UNSUPPORTED_ARGUMENTS'
# Never allow a public CI host, non-interactive shell, or script to
# approve a private Owner motion Goal. The existing private runner asks the
# operator to type YES-P2-G07-GOAL once, without any implicit YES.
[[ -t 0 && -t 1 && -r /dev/tty ]] || hold 'CONTROLLING_TTY_REQUIRED'
[[ "${GITHUB_ACTIONS:-false}" != true ]] || hold 'GITHUB_ACTIONS_MUST_NOT_SEND_OWNER_GOAL'
[[ -r /opt/ros/jazzy/setup.bash ]] || hold 'ROS_JAZZY_REQUIRED'
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || hold 'UBUNTU_24_04_REQUIRED'
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || hold 'WSL2_REQUIRED'
for tool in gh git python3 bash mktemp sha256sum tar ros2 colcon gz; do
  command -v "$tool" >/dev/null || hold "MISSING_TOOL_$tool"
done
gh auth status >/dev/null 2>&1 || hold 'GH_AUTH_PRIVATE_REPO_REQUIRED'
self_check || hold 'STATIC_CONTRACT_FAILED'
ci_status="$(gh api "repos/$PUBLIC_REPO/actions/runs/$CI_REAL_L2_RUN" \
  --jq '(.head_sha // "") + " " + (.status // "") + " " + (.conclusion // "")')" \
  || hold 'PUBLIC_GAZEBO_L2_PROOF_UNAVAILABLE'
[[ "$ci_status" == "$CI_WORKFLOW_COMMIT completed success" ]] ||
  hold "PUBLIC_REAL_GAZEBO_L2_NOT_GREEN:$ci_status"
echo "AXIA_G07_C29_REAL_GAZEBO_CI_L2_SCOPED_PASS run=$CI_REAL_L2_RUN"
echo "AXIA_G07_C29_CI_RUNTIME_DIGEST=$CI_RUNTIME_IMAGE_DIGEST"
echo 'AXIA_G07_C29_CI_OWNER_WSL2_KERNEL_WSLG_SCHEDULER_NOT_EQUAL'
echo 'AXIA_G07_C29_PREVIOUS_REAL_CI_CM_171MS_FAIL_ROOT_UNRESOLVED'
# The existing private owner runner captures 14-topic rosbag, native odom,
# Lifecycle ACK, child shutdown, raw original SHA256 and a sealed tar archive.
[[ -d "$HOME" && ! -L "$HOME" && "$HOME" != / ]] || hold 'OWNER_HOME_INVALID'
WORK="$(mktemp -d "$HOME/.axia_g07_c29_checkout_XXXXXXXX")"
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  cd "$HOME" || cd /
  if [[ "$WORK" == "$HOME"/.axia_g07_c29_checkout_* && -d "$WORK" ]]; then
    rm -rf -- "$WORK"
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
gh repo clone "$PRIVATE_REPO" "$WORK/instructor" -- \
    --filter=blob:none --no-checkout --quiet || hold 'PRIVATE_REPO_CLONE_FAILED'
git -C "$WORK/instructor" fetch --quiet --no-tags --depth 1 origin "$PRIVATE_SHA" ||
  hold 'PRIVATE_SOURCE_FETCH_FAILED'
git -C "$WORK/instructor" -c advice.detachedHead=false checkout --quiet --detach "$PRIVATE_SHA" ||
  hold 'PRIVATE_SOURCE_CHECKOUT_FAILED'
[[ "$(git -C "$WORK/instructor" rev-parse HEAD)" == "$PRIVATE_SHA" ]] ||
  hold 'PRIVATE_SOURCE_SHA_MISMATCH'
[[ -z "$(git -C "$WORK/instructor" status --porcelain)" ]] ||
  hold 'PRIVATE_SOURCE_DIRTY'
for p in scripts/p2_owner_l3_wsl2.sh tools/p2_g07_ci_moving_goal.py \
         tools/p2_g07_ci_moving_goal_oracle.py \
         tools/p2_g07_owner_env_parity.py \
         ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_base_guard_policy.py; do
  [[ -s "$WORK/instructor/$p" ]] || hold "PRIVATE_SOURCE_FILE_MISSING:$p"
done
echo "AXIA_G07_C29_OWNER_PRIVATE_SOURCE_VERIFIED=$PRIVATE_SHA"
echo 'SIMULATION ONLY: exactly ONE Owner G07 Goal, requires manual YES-P2-G07-GOAL.'
echo '150ms Guard/CM and 300ms Scan/odom/clock boundaries unchanged.'
echo 'No hardware E-Stop certification or automatic formal safety acceptance.'
export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"
set +e
bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh" --case G07 --mvp-relocated-obstacle
owner_rc=$?
set -e
echo "AXIA_G07_C29_OWNER_PRIVATE_RUNNER_RC=$owner_rc"
echo 'G07_OWNER_RAW_SHA256_ARCHIVE_AND_INDEPENDENT_REVIEW_REQUIRED'
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
exit "$owner_rc"
