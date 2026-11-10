#!/usr/bin/env bash
# AXIA G07 relocated simulated obstacle: pinned Owner WSL2 entrypoint.
# This public bootstrap contains NO instructor solution, no auto-consent.
set -Eeuo pipefail
umask 077

readonly REPO='silverbjin/axia-robot-safety-instructor'
readonly BRANCH='fix/p2-g07-relocated-obstacle-open-lane-20261111'
readonly PRIVATE_SHA='843338cf3338d15658a5486bd15d1aead8e0096c'

if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# == 1 && "$PRIVATE_SHA" =~ ^[a-f0-9]{40}$ ]] || exit 2
  echo "AXIA_P2_G07_RELOCATED_PUBLIC_BOOTSTRAP_STATIC_PASS private_sha=$PRIVATE_SHA GAZEBO_NOT_RUN L3_NOT_RUN"
  exit 0
fi
if [[ $# != 0 ]]; then
  echo 'P2_G07_RELOCATED_BLOCKED: run without arguments; --self-check is static only' >&2
  exit 2
fi
if [[ ! -t 0 || ! -t 1 || ! -r /dev/tty ]]; then
  echo 'P2_G07_RELOCATED_BLOCKED OWNER_CONTROLLING_TTY_REQUIRED_GOAL_NOT_SENT' >&2
  exit 2
fi
for bin in gh git bash mktemp; do
  command -v "$bin" >/dev/null || {
    echo "P2_G07_RELOCATED_BLOCKED MISSING_DEPENDENCY_$bin" >&2
    exit 2
  }
done
if ! gh auth status >/dev/null 2>&1; then
  echo 'P2_G07_RELOCATED_BLOCKED PRIVATE_GITHUB_AUTH_REQUIRED' >&2
  exit 2
fi

WORK="$(mktemp -d "$HOME/.axia_p2_g07_reloc_owner_XXXXXXXX")"
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  cd "$HOME" || cd /
  case "$WORK" in
    "$HOME"/.axia_p2_g07_reloc_owner_*)
      if [[ -d "$WORK" ]]; then rm -rf -- "$WORK"; fi ;;
  esac
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if ! gh repo clone "$REPO" "$WORK/instructor" -- \
   --single-branch --branch "$BRANCH" --depth 1 --quiet; then
  echo 'P2_G07_RELOCATED_BLOCKED PRIVATE_BRANCH_FETCH_FAILED' >&2
  exit 2
fi
CURRENT_SHA="$(git -C "$WORK/instructor" rev-parse HEAD)"
if [[ "$CURRENT_SHA" != "$PRIVATE_SHA" ]] ||
   [[ -n "$(git -C "$WORK/instructor" status --porcelain)" ]]; then
  echo 'P2_G07_RELOCATED_BLOCKED EXACT_SOURCE_SHA_OR_WORKTREE_MISMATCH' >&2
  exit 2
fi
export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"
printf 'AXIA_P2_G07_RELOCATED_OWNER_PIN_VERIFIED private_sha=%s GAZEBO_NOT_RUN L3_NOT_RUN\n' "$PRIVATE_SHA"
echo 'SIMULATION ONLY: typed Owner approval YES-P2-G07-GOAL will be requested by the private Owner harness.'
echo 'Original static TB3 world/map and CM safety zones are unchanged.'
echo 'This is ONE G07 moving-Goal rehearsal; no G05/G06 crash injection, no certified hardware E-Stop.'
bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh" --case G07 --mvp-relocated-obstacle
