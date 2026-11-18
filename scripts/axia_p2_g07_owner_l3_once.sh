#!/usr/bin/env bash
# AXIA P2 G07 instructor-only SIMULATION demonstration bootstrap.
# Private source verified at L0+real Gazebo no-Goal L2; Owner L3 is NOT_RUN.
# Requires explicit owner consent in the private runner; never auto-approves.
set -Eeuo pipefail
umask 077

readonly REPO='silverbjin/axia-robot-safety-instructor'
readonly BRANCH='integration/p1-p2-mvp-shell-consent-20261110'
readonly SHA='1216d8589b2a8ac4c7e75aedaa7854eb7b2470b3'

if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# == 1 && "$SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
  printf 'AXIA_P2_G07_OWNER_BOOTSTRAP_L2_PROVEN source_sha=%s G07_L3_NOT_RUN\n' "$SHA"
  exit 0
fi
if [[ $# != 0 ]]; then
  printf 'P2_G07_BLOCKED: no arguments allowed; G07 only\n' >&2
  exit 2
fi
if [[ ! -t 0 || ! -t 1 || ! -r /dev/tty ]]; then
  echo 'P2_G07_BLOCKED: real Owner controlling TTY required' >&2
  exit 2
fi
for tool in gh git bash mktemp; do
  command -v "$tool" >/dev/null || {
    printf 'P2_G07_BLOCKED: missing %s\n' "$tool" >&2
    exit 2
  }
done
gh auth status >/dev/null 2>&1 || {
  echo 'P2_G07_BLOCKED: GitHub private repository authentication required' >&2
  exit 2
}
readonly SRC_ROOT="$(mktemp -d "$HOME/.axia_p2_g07_owner_XXXXXXXX")"
cleanup() {
  local result=$?
  trap - EXIT INT TERM
  cd "$HOME" || cd /
  if [[ -d "$SRC_ROOT" && "$SRC_ROOT" == "$HOME"/.axia_p2_g07_owner_* ]]; then
    rm -rf -- "$SRC_ROOT"
  fi
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

printf 'AXIA_P2_G07_L3_PRIVATE_SOURCE_SHA=%s\n' "$SHA"
if ! gh repo clone "$REPO" "$SRC_ROOT/instructor" -- \
  --single-branch --branch "$BRANCH" --depth 1; then
  echo 'P2_G07_BLOCKED: private clone failure' >&2
  exit 2
fi
if [[ "$(git -C "$SRC_ROOT/instructor" rev-parse HEAD)" != "$SHA" ]]; then
  echo 'P2_G07_BLOCKED: private source SHA mismatch' >&2
  exit 2
fi
if [[ -n "$(git -C "$SRC_ROOT/instructor" status --porcelain)" ]]; then
  echo 'P2_G07_BLOCKED: dirty private source' >&2
  exit 2
fi

export AXIA_P2_OWNER_PINNED_SHA="$SHA"
echo 'SIMULATION ONLY: G07 Owner Goal needs manual approval at the real TTY.'
echo 'Native Contact is not proven. L2 obstacle/LaserScan PASS is NOT L3 acceptance.'
# Preserve all private per-case approval, PID and Guard policies.
bash "$SRC_ROOT/instructor/scripts/p2_owner_l3_wsl2.sh" --case G07
