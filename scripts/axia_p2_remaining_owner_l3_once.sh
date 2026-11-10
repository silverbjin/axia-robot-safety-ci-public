#!/usr/bin/env bash
# Two independent cold Owner L3 simulations: G06 then G07 only.
# No unattended Goal or Fault; each child requests its own TTY authorization.
set -Eeuo pipefail
umask 077
readonly REPO='silverbjin/axia-robot-safety-instructor'
readonly BRANCH='integration/p1-p2-mvp-shell-consent-20261110'
readonly SHA='1216d8589b2a8ac4c7e75aedaa7854eb7b2470b3'

if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# == 1 && "$SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
  printf 'AXIA_P2_REMAINING_G06_G07_OWNER_BOOTSTRAP source_sha=%s L3_NOT_RUN\n' "$SHA"
  exit 0
fi
if [[ $# != 0 ]]; then
  echo 'P2_REMAINING_BLOCKED: no arguments permitted' >&2
  exit 2
fi
if [[ ! -t 0 || ! -t 1 || ! -r /dev/tty ]]; then
  echo 'P2_REMAINING_BLOCKED: real Owner controlling TTY required' >&2
  exit 2
fi
for tool in gh git bash mktemp; do
  command -v "$tool" >/dev/null || {
    printf 'P2_REMAINING_BLOCKED: missing %s\n' "$tool" >&2
    exit 2
  }
done
gh auth status >/dev/null 2>&1 || {
  echo 'P2_REMAINING_BLOCKED: private GitHub authentication required' >&2
  exit 2
}
readonly SRC_ROOT="$(mktemp -d "$HOME/.axia_p2_remaining_XXXXXXXX")"
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  cd "$HOME" || cd /
  if [[ -d "$SRC_ROOT" && "$SRC_ROOT" == "$HOME"/.axia_p2_remaining_* ]]; then
    rm -rf -- "$SRC_ROOT"
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
printf 'AXIA_P2_PRIVATE_SOURCE_SHA=%s\n' "$SHA"
if ! gh repo clone "$REPO" "$SRC_ROOT/instructor" -- \
  --single-branch --branch "$BRANCH" --depth 1; then
  echo 'P2_REMAINING_BLOCKED: private clone failure' >&2
  exit 2
fi
[[ "$(git -C "$SRC_ROOT/instructor" rev-parse HEAD)" == "$SHA" ]] || {
  echo 'P2_REMAINING_BLOCKED: exact source SHA mismatch' >&2
  exit 2
}
[[ -z "$(git -C "$SRC_ROOT/instructor" status --porcelain)" ]] || {
  echo 'P2_REMAINING_BLOCKED: dirty private source' >&2
  exit 2
}
export AXIA_P2_OWNER_PINNED_SHA="$SHA"

# Both cases are cold and independently launched by the private runner.
# Failure of the first case stops this wrapper before the second Goal.
for CASE in G06 G07; do
  printf '\nP2_REMAINING_OWNER_START_CASE=%s\n' "$CASE"
  echo 'SIMULATION ONLY: each Goal and each Crash require explicit human TTY approval.'
  bash "$SRC_ROOT/instructor/scripts/p2_owner_l3_wsl2.sh" --case "$CASE" || {
    printf 'P2_REMAINING_OWNER_BLOCKED_CASE=%s; preserved raw evidence under $HOME/axia_p2_private_evidence\n' "$CASE" >&2
    exit 2
  }
  printf 'P2_REMAINING_OWNER_CASE=%s L3_NUMERICAL_CANDIDATE_RAW_REVIEW_REQUIRED\n' "$CASE"
done
echo 'P2_G06_G07_NUMERICAL_CANDIDATES_ONLY: independent raw review required; certified_estop=false.'
