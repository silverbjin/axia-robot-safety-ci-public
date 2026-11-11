#!/usr/bin/env bash
# P2 G07 EDUCATIONAL SIMULATION ONLY: exactly one Owner-approved moving Goal.
# Built from raw WSL2 failure c2RmrBlU. No Instructor solution in public repo.
# The private runner verifies CI-matched core packages and official source SHA
# before launching Gazebo; Goal still requires manually typed Owner TTY consent.
set -Eeuo pipefail
umask 077
readonly PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'
readonly PRIVATE_BRANCH='fix/p2-g07-cm-slowdown-delayed-direction-20261111'
readonly PRIVATE_SHA='a15dbd7b2fb962d5d006c4944faac933bf4b19ca'

if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# == 1 && "$PRIVATE_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
  printf 'AXIA_G07_PREPOSITIONED_BOOTSTRAP_STATIC_OK private_sha=%s OWNER_L3_NOT_RUN\n' "$PRIVATE_SHA"
  exit 0
fi
[[ $# == 0 ]] || { echo 'AXIA_G07_OWNER_BLOCKED: arguments forbidden' >&2; exit 2; }
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'AXIA_G07_OWNER_BLOCKED: controlling TTY required NO_GOAL' >&2
  exit 2
}
for x in gh git bash mktemp; do
  command -v "$x" >/dev/null || { echo "AXIA_G07_OWNER_BLOCKED: missing $x" >&2;exit 2; }
done
gh auth status >/dev/null 2>&1 || {
  echo 'AXIA_G07_OWNER_BLOCKED: private GitHub authentication required' >&2
  exit 2
}

WORK="$(mktemp -d "$HOME/.axia_g07_pregoal_owner_XXXXXXXX")"
cleanup() {
  local code=$?
  trap - EXIT INT TERM
  cd "$HOME" || cd /
  case "$WORK" in
    "$HOME"/.axia_g07_pregoal_owner_*)
      if [[ -d "$WORK" ]]; then rm -rf -- "$WORK"; fi ;;
  esac
  exit "$code"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

gh repo clone "$PRIVATE_REPO" "$WORK/instructor" -- \
  --single-branch --branch "$PRIVATE_BRANCH" --depth 1 --quiet
ACTUAL="$(git -C "$WORK/instructor" rev-parse HEAD)"
if [[ "$ACTUAL" != "$PRIVATE_SHA" ]] ||
   [[ -n "$(git -C "$WORK/instructor" status --porcelain)" ]]; then
  echo 'AXIA_G07_OWNER_BLOCKED: unreviewed SHA or dirty private checkout' >&2
  exit 2
fi
for f in tools/p2_g07_owner_prepositioned.py tools/p2_g07_owner_env_parity.py \
         scripts/p2_owner_l3_wsl2.sh; do
  [[ -f "$WORK/instructor/$f" ]] || {
    echo "AXIA_G07_OWNER_BLOCKED: required file missing: $f" >&2
    exit 2
  }
done
export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"
printf 'AXIA_G07_OWNER_PREPOSITIONED_PIN_VERIFIED private_sha=%s\n' "$PRIVATE_SHA"
echo 'Owner L3 is NOT RUN. Environment parity check runs first and BLOCKS on drift.'
echo 'The actual physical G07 obstacle is prepositioned before Goal.'
echo 'After approval, ROS/Gazebo observations are required for MOVING slow+stop.'
echo 'SIMULATION ONLY: expect manual YES-P2-G07-GOAL from the private harness.'
echo 'SW Stop is not certified hardware E-Stop. No G05/G06 Crash is requested.'
bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh" \
  --case G07 --mvp-relocated-obstacle
