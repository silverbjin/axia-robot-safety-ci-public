#!/usr/bin/env bash
# Standalone D3 bootstrap. Retrieve this file from public CI repository even when
# a stale Instructor checkout does not contain the requested D3 scripts.
# Never source from the interactive shell: bash this-file.sh.
set -Eeuo pipefail

BRANCH='feat/d3-intrusion-scan-stop-demo-20261108'
PIN='0be687ee033233fcd53be1190e0b2f9e86730fc9'
REPO='silverbjin/axia-robot-safety-instructor'
EXPECTED_ORIGIN="https://github.com/${REPO}.git"
MODE="${1:---prepare}"
WORK="${HOME}/axia_d3_classroom"
ROOT="$WORK/axia-d3-instructor"
SCRIPT_REL='training/d03/d3_demo/scripts/d3_wsl2_prepare_once.sh'

say() { printf '[AXIA_D3] %s\n' "$*"; }
blocked() { say "[BLOCKED] $*" >&2; exit 2; }

case "$MODE" in
  --prepare|--checkout-only) ;;
  *) blocked 'usage: bash d3_wsl2_bootstrap_safe.sh [--prepare|--checkout-only]' ;;
esac

# Local Git fixture injection is explicitly restricted to --checkout-only tests.
if [[ "${AXIA_D3_TEST_MODE:-0}" == 1 ]]; then
  [[ "$MODE" == --checkout-only ]] || blocked 'test mode may not build or launch ROS'
  EXPECTED_ORIGIN="${AXIA_D3_TEST_REMOTE:?}"
  BRANCH="${AXIA_D3_TEST_BRANCH:?}"
  PIN="${AXIA_D3_TEST_SHA:?}"
  REPO='TEST_ONLY_DO_NOT_USE_GITHUB'
fi
[[ "$PIN" =~ ^[[:xdigit:]]{40}$ ]] || blocked 'invalid expected pinned SHA'
command -v git >/dev/null || blocked 'git unavailable'
if [[ "$REPO" != TEST_ONLY_DO_NOT_USE_GITHUB ]]; then
  command -v gh >/dev/null || blocked 'GitHub CLI missing (install gh)'
  gh auth status >/dev/null 2>&1 || blocked 'GitHub private repository authentication required: gh auth login'
fi
[[ ! -L "$WORK" ]] || blocked 'classroom work directory must not be a symlink'
mkdir -p "$WORK"
[[ -d "$WORK" ]] || blocked 'classroom work path is not a directory'
chmod 700 "$WORK" 2>/dev/null || true

# Normalise a GitHub HTTPS/SSH origin; refuse unexpected repositories.
origin_matches() {
  local p="$1" url
  url="$(git -C "$p" remote get-url origin 2>/dev/null || true)"
  if [[ "$REPO" == TEST_ONLY_DO_NOT_USE_GITHUB ]]; then
    [[ "$url" == "$EXPECTED_ORIGIN" ]]
  else
    case "$url" in
      "https://github.com/$REPO"|"https://github.com/$REPO.git"|"git@github.com:$REPO"|"git@github.com:$REPO.git") return 0;;
      *) return 1;;
    esac
  fi
}

# Reuse only a clean, correct-branch, correct-origin checkout, with expected file.
# A wrong branch / dirty tree / unrelated origin is NEVER overwritten or reset.
can_reuse() {
  local p="$1"
  [[ -d "$p/.git" ]] || return 1
  [[ "$(git -C "$p" branch --show-current 2>/dev/null || true)" == "$BRANCH" ]] || return 1
  [[ -z "$(git -C "$p" status --porcelain --untracked-files=all 2>/dev/null)" ]] || return 1
  origin_matches "$p" || return 1
  [[ -f "$p/$SCRIPT_REL" ]] || return 1
}

choose_destination() {
  if [[ ! -e "$ROOT" && ! -L "$ROOT" ]]; then
    return 0
  fi
  if can_reuse "$ROOT"; then
    return 0
  fi
  local reason='existing checkout not a clean D3 branch or required script missing'
  say "[PRESERVE] $ROOT ($reason)"
  local alt="$WORK/axia-d3-instructor-v2-${PIN:0:8}"
  if [[ ! -e "$alt" && ! -L "$alt" ]] || can_reuse "$alt"; then
    ROOT="$alt"
    return 0
  fi
  ROOT="$WORK/axia-d3-instructor-v2-${PIN:0:8}-$(date -u +%Y%m%dT%H%M%SZ)-$$"
  [[ ! -e "$ROOT" && ! -L "$ROOT" ]] || blocked 'isolated destination collision'
}
choose_destination

if [[ -d "$ROOT/.git" ]]; then
  can_reuse "$ROOT" || blocked "refusing to alter unsafe checkout: $ROOT"
  say "[REUSE] $ROOT"
  # Fetch remote state first; never mutate the checkout when reviewed pin moved.
  git -C "$ROOT" fetch --no-tags origin "refs/heads/$BRANCH:refs/remotes/origin/$BRANCH" || blocked 'git fetch failed'
  REMOTE_SHA="$(git -C "$ROOT" rev-parse "refs/remotes/origin/$BRANCH")"
  [[ "$REMOTE_SHA" == "$PIN" ]] || blocked "PIN_MISMATCH upstream SHA=$REMOTE_SHA expected=$PIN; existing HEAD unchanged"
  git -C "$ROOT" merge --ff-only "refs/remotes/origin/$BRANCH" || blocked 'local feature branch diverged; no force reset performed'
else
  [[ ! -e "$ROOT" && ! -L "$ROOT" ]] || blocked "destination exists; refusing overwrite: $ROOT"
  say "[CLONE] isolated checkout $ROOT"
  if [[ "$REPO" == TEST_ONLY_DO_NOT_USE_GITHUB ]]; then
    git clone --quiet --branch "$BRANCH" --single-branch "$EXPECTED_ORIGIN" "$ROOT" || blocked 'fixture clone failed'
  else
    gh repo clone "$REPO" "$ROOT" -- --branch "$BRANCH" --single-branch || blocked 'private D3 branch clone failed'
  fi
fi

ACTUAL="$(git -C "$ROOT" rev-parse HEAD)"
[[ "$ACTUAL" == "$PIN" ]] || blocked "PIN_MISMATCH checkout SHA=$ACTUAL expected=$PIN"
[[ "$(git -C "$ROOT" branch --show-current)" == "$BRANCH" ]] || blocked 'wrong active branch'
[[ -f "$ROOT/$SCRIPT_REL" ]] || blocked "required D3 script missing at pinned SHA: $SCRIPT_REL"

# Root selection is durable across terminal tabs; alternate checkout is supported.
# Always source this generated env in subsequent instructor terminals.
ENVFILE="$WORK/d3_checkout.env"
[[ ! -L "$ENVFILE" ]] || blocked 'checkout environment path is symlinked; refusing overwrite'
LOCAL="$WORK/axia-d3-prepare.sh"
[[ ! -L "$LOCAL" ]] || blocked 'persistent launcher path is symlinked; refusing overwrite'
umask 077
{
  printf 'export AXIA_D3_REPO_ROOT=%q\n' "$ROOT"
  printf 'export AXIA_D3_BRANCH=%q\n' "$BRANCH"
  printf 'export AXIA_D3_PIN=%q\n' "$PIN"
} > "$ENVFILE"
SELF="$(readlink -f -- "$0")"
if [[ "$SELF" != "$LOCAL" ]]; then
  install -m 700 "$SELF" "$LOCAL"
fi
say "[SOURCE_PIN_VERIFIED] branch=$BRANCH sha=$ACTUAL"
say "[ROOT] $ROOT"
say "[ENV] $ENVFILE"
say "[RETRY] bash '$LOCAL' (never run set -e in interactive terminal)"

if [[ "$MODE" == --checkout-only ]]; then
  say '[READY] D3_SOURCE_PINNED_ONLY (ROS/GAZEBO NOT_RUN)'
  exit 0
fi

# Preflight and build reuse existing instructor sources, but do not call the old
# d3_wsl2_prepare_once.sh, which hardcodes the legacy checkout location.
[[ "$(uname -s)" == Linux ]] && grep -qi microsoft /proc/version || blocked 'WSL2 Ubuntu required'
source /etc/os-release
[[ "${ID:-}" == ubuntu && "${VERSION_ID:-}" == 24.04 ]] || blocked 'Ubuntu 24.04 required'
[[ -f /opt/ros/jazzy/setup.bash ]] || blocked 'ROS 2 Jazzy setup missing'
command -v colcon >/dev/null || blocked 'colcon missing'
set +u
source /opt/ros/jazzy/setup.bash
set -u
command -v gz >/dev/null || blocked 'Gazebo Harmonic gz CLI missing'
for pkg in nav2_bringup nav2_minimal_tb3_sim ros_gz_sim; do
  ros2 pkg prefix "$pkg" >/dev/null || blocked "ROS package missing: $pkg"
done
cd "$ROOT"
colcon build --base-paths ros2_ws/src --symlink-install \
  --packages-select axia_safety_supervisor axia_fault_injector axia_scenario_verifier axia_d3_demo \
  || blocked 'D3 colcon build failed'
set +u
source install/setup.bash
set -u
ros2 pkg prefix axia_d3_demo >/dev/null || blocked 'D3 ROS package not indexed after build'
ros2 pkg executables axia_d3_demo || blocked 'D3 console scripts absent'
bash training/d03/d3_demo/scripts/d3_session.sh --init || blocked 'D3 session setup failed'
# preflight checks the branch relative to THIS script; fallback checkout supported.
bash training/d03/d3_demo/scripts/run_d3_instructor.sh --preflight || blocked 'D3 ROS preflight failed'
say '[READY] D3_V2_SOURCE_BUILD_SESSION_PREFLIGHT (GUI/MOTION/FAULT NOT_RUN)'
say '[NEXT] source "$HOME/axia_d3_classroom/d3_checkout.env"; cd "$AXIA_D3_REPO_ROOT"'
say '[NEXT] Gazebo Terminal A: bash training/d03/d3_demo/scripts/run_d3_instructor.sh --launch'
say '[NEXT] After actual world selection, Terminal B: run_d3_preview.sh -> approved P1 Goal -> run_d3_live_scene.sh'
