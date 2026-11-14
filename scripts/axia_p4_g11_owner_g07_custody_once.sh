#!/usr/bin/env bash
# AXIA P4 G11 WSL2 Owner: one existing P2 G07 GUI Goal + original RAW custody.
# NEVER executes in public CI. Manual YES-P2-G07-GOAL remains mandatory.
# No implicit consent, private SHA immutable, no raw or answer uploads.
set -Eeuo pipefail
umask 077
PRIVATE_SHA="50caa38134d002935b6bcd022645a1e8a1d49cef"
if [[ ! -t 0 || ! -t 1 || ! -r /dev/tty ]]; then
  echo 'AXIA_G11_OWNER_G07_BLOCKED_INTERACTIVE_TTY_REQUIRED' >&2; exit 2
fi
if [[ ! -r /proc/sys/kernel/osrelease ]] ||
   ! grep -Eqi '(microsoft|wsl2)' /proc/sys/kernel/osrelease; then
  echo 'AXIA_G11_OWNER_G07_BLOCKED_WSL2_REQUIRED' >&2;exit 2
fi
for command_name in git gh python3 bash; do
  command -v "$command_name" >/dev/null || {
    echo "AXIA_G11_OWNER_G07_BLOCKED_MISSING_$command_name" >&2;exit 2
  }
done
gh auth status >/dev/null 2>&1 || {
  echo 'AXIA_G11_OWNER_G07_BLOCKED_PRIVATE_GH_AUTH_REQUIRED' >&2;exit 2
}
WORK="$(mktemp -d)"
trap 'rm -rf -- "$WORK"' EXIT
gh repo clone silverbjin/axia-robot-safety-instructor "$WORK/instructor" \
  -- --quiet --no-checkout --filter=blob:none >/dev/null
git -C "$WORK/instructor" fetch --quiet --depth 1 origin "$PRIVATE_SHA"
git -C "$WORK/instructor" -c advice.detachedHead=false checkout \
  --quiet --detach FETCH_HEAD
test "$(git -C "$WORK/instructor" rev-parse HEAD)" = "$PRIVATE_SHA" || {
  echo 'AXIA_G11_OWNER_G07_BLOCKED_SOURCE_SHA_MISMATCH' >&2;exit 2
}
echo "AXIA_G11_OWNER_G07_PRIVATE_SOURCE_LOCK_VERIFIED sha=$PRIVATE_SHA"
echo 'AXIA_G11_OWNER_G07_ACTUAL_GAZEBO_GOAL_NOT_YET_RUN'
echo 'SIMULATION ONLY: original Owner human Goal consent is required.'
echo 'Post-run SHA256 archive custody is mandatory, not acceptance.'
AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA" \
AXIA_G11_RUN_CUSTODY_REQUIRED=1 \
  bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh" \
    --case G07 --mvp-relocated-obstacle
echo 'AXIA_G11_OWNER_G07_RAW_ARCHIVE_CUSTODY_WRAPPER_EXIT_0_FORMAL_G11_HOLD'
