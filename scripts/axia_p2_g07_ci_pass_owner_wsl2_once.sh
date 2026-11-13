#!/usr/bin/env bash
# AXIA G07 Owner WSL2 final acceptance bootstrap; SIMULATION ONLY.
# Exact public real Jazzy/Harmonic/Nav2 moving Goal + 14-topic Owner bag + orderly shutdown L2 #43339521667 PASS.
# Instructor source SHA pinned byte-for-byte. Owner L3 NOT RUN here.
# Never auto-answer any Owner TTY consent. No hardware E-Stop certification.
set -Eeuo pipefail
umask 077
readonly PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'
readonly PRIVATE_SHA='eb984b73138e592caa67426eed9c60dde2ca2ebd'
readonly CI_L2_RUN='43339521667'
readonly CI_L2_SCOPE='SHARED_STARTUP_GOAL_OWNER14_BAG_CM_CLEAN_EXIT0'
# CI Docker image is pinned, but WSLg/kernel/GPU scheduling is NOT equivalent.
readonly CI_IMAGE_DIGEST='sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e'
if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# -eq 1 && "$PRIVATE_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
  printf 'AXIA_G07_CI_PASS_OWNER_BOOTSTRAP_STATIC_PASS private_sha=%s ci_l2=%s scope=%s OWNER_L3_NOT_RUN\n' "$PRIVATE_SHA" "$CI_L2_RUN" "$CI_L2_SCOPE"
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
         scripts/p2_g07_shared_staged_startup.sh \
         tools/p2_g07_lifecycle_service.py \
         tools/p2_g07_ci_moving_goal.py \
         tools/p2_g07_ordered_shutdown.py \
         tools/p2_g07_owner_shutdown_audit.py; do
  [[ -f "$WORK/instructor/$f" ]] || {
    echo "AXIA_G07_OWNER_BLOCKED: pinned source missing $f; NO_GOAL" >&2
    exit 2
  }
done
export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"
printf 'AXIA_G07_OWNER_PIN_VERIFIED private_sha=%s ci_l2=%s scope=%s\n' "$PRIVATE_SHA" "$CI_L2_RUN" "$CI_L2_SCOPE"
echo 'SIMULATION ONLY. Public CI L2 PASS != WSL2 Owner L3 acceptance.'
echo 'WSLG_KERNEL_SCHEDULER_NOT_EQUIVALENT: CI offscreen Docker digest does not prove WSLg GUI scheduling.'
printf 'AXIA_G07_CI_IMMUTABLE_RUNTIME_DIGEST=%s OWNER_NATIVE_RUNTIME_L3_NOT_RUN\n' "$CI_IMAGE_DIGEST"
echo 'The separate private Owner harness requires manual YES-P2-G07-GOAL.'
echo 'Never run a physical robot from this script. SW Stop != certified E-Stop.'
echo 'Evidence is saved independently by the private Owner harness.'
bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh" \
  --case G07 --mvp-relocated-obstacle
