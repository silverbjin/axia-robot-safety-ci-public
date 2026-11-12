#!/usr/bin/env bash
# AXIA G07 Owner WSL2 final acceptance bootstrap; SIMULATION ONLY.
# Previous exact-source moving Goal L2 #43186070186 PASS at Instructor 9f12d758.\n# New exact-source NO-GOAL real shutdown L2 #43234191360 PASS at Instructor 21d658fa.\n# WSL2 GUI after-Goal shutdown remains Owner L3 NOT RUN. No certified E-Stop.
# Instructor source SHA pinned byte-for-byte. Owner L3 NOT RUN here.
# Never auto-answer any Owner TTY consent. No hardware E-Stop certification.
set -Eeuo pipefail
umask 077
readonly PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'
readonly PRIVATE_SHA='21d658fac03396c9f30798237a820e187ecb447c'
readonly CI_L2_RUN='43186070186'
readonly CI_L2_SOURCE_SHA='9f12d7581e07752a53e3b3acd2d5c45ad7d87fa7'
readonly CI_SHUTDOWN_L2_RUN='43234191360'
if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# -eq 1 && "$PRIVATE_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
  printf 'AXIA_G07_CI_PASS_OWNER_BOOTSTRAP_STATIC_PASS private_sha=%s moving_l2_baseline=%s moving_l2_source=%s shutdown_l2_exact=%s OWNER_L3_NOT_RUN\n' "$PRIVATE_SHA" "$CI_L2_RUN" "$CI_L2_SOURCE_SHA" "$CI_SHUTDOWN_L2_RUN"
  exit 0
fi
[[ $# -eq 0 ]] || { echo 'AXIA_G07_OWNER_BLOCKED: no arguments supported' >&2; exit 2; }
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'AXIA_G07_OWNER_BLOCKED: real controlling TTY required; NO_GOAL' >&2
  exit 2
}
for binary in gh git bash mktemp sha256sum; do
  command -v "$binary" >/dev/null || { echo "AXIA_G07_OWNER_BLOCKED: missing $binary" >&2; exit 2; }
done
gh auth status >/dev/null 2>&1 || {
  echo 'AXIA_G07_OWNER_BLOCKED: authenticate private GitHub with gh auth login' >&2
  exit 2
}
readonly WORK="$(mktemp -d "$HOME/.axia_g07_ci_pass_owner_XXXXXXXX")"
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  cd "$HOME" || cd /
  case "$WORK" in
    "$HOME"/.axia_g07_ci_pass_owner_*)
      [[ ! -d "$WORK" ]] || rm -rf -- "$WORK" ;;
    *) echo 'AXIA_G07_OWNER_BLOCKED: unsafe cleanup path' >&2; rc=2 ;;
  esac
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
# Detached SHA fetch prevents branch-tip movement from silently changing code.
gh repo clone "$PRIVATE_REPO" "$WORK/instructor" -- \
  --filter=blob:none --no-checkout --quiet
git -C "$WORK/instructor" fetch --no-tags --depth 1 origin "$PRIVATE_SHA"
git -C "$WORK/instructor" -c advice.detachedHead=false checkout --detach "$PRIVATE_SHA"
readonly ACTUAL="$(git -C "$WORK/instructor" rev-parse HEAD)"
[[ "$ACTUAL" == "$PRIVATE_SHA" ]] && \
[[ -z "$(git -C "$WORK/instructor" status --porcelain)" ]] || {
  echo 'AXIA_G07_OWNER_BLOCKED: source SHA mismatch/dirty checkout; NO_GOAL' >&2
  exit 2
}
for f in scripts/p2_owner_l3_wsl2.sh tools/p2_g07_owner_env_parity.py \
         tools/p2_g07_ci_moving_goal.py \\
         tools/p2_g07_ordered_shutdown.py \\
         tools/p2_g07_owner_shutdown_audit.py; do
  [[ -f "$WORK/instructor/$f" ]] || {
    echo "AXIA_G07_OWNER_BLOCKED: pinned source missing $f; NO_GOAL" >&2
    exit 2
  }
done
export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"
printf 'AXIA_G07_OWNER_PIN_VERIFIED private_sha=%s moving_l2_baseline=%s moving_l2_source=%s shutdown_l2_exact=%s\n' "$PRIVATE_SHA" "$CI_L2_RUN" "$CI_L2_SOURCE_SHA" "$CI_SHUTDOWN_L2_RUN"
echo 'SIMULATION ONLY. Public CI L2 PASS != WSL2 Owner L3 acceptance.'
echo 'The separate private Owner harness requires manual YES-P2-G07-GOAL.'
echo 'Never run a physical robot from this script. SW Stop != certified E-Stop.'
echo 'Evidence is saved independently by the private Owner harness.'
bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh" \
  --case G07 --mvp-relocated-obstacle
