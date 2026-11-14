#!/usr/bin/env bash
# Public zero-Goal bootstrap: pinned protected Instructor checkout on Owner WSL2.
# No ROS/Gazebo/Goal, no safety-state changes, no main merge or Student release.
set -Eeuo pipefail
umask 077
PRIVATE_SHA="04c13b63839e68822cba95a876106dbd0b13f227"
if [[ ! -r /proc/sys/kernel/osrelease ]] ||
   ! grep -Eqi '(microsoft|wsl2)' /proc/sys/kernel/osrelease; then
  echo 'AXIA_G11_BOOTSTRAP_BLOCKED_WSL2_REQUIRED' >&2; exit 2
fi
for command_name in gh git python3 flock bash; do
  command -v "$command_name" >/dev/null || {
    echo "AXIA_G11_BOOTSTRAP_BLOCKED_REQUIRED_$command_name" >&2
    exit 2
  }
done
gh auth status >/dev/null 2>&1 || {
  echo 'AXIA_G11_BOOTSTRAP_BLOCKED_PRIVATE_GH_AUTH_REQUIRED' >&2
  exit 2
}
WORK="$(mktemp -d)"
trap 'rm -rf -- "$WORK"' EXIT
gh repo clone silverbjin/axia-robot-safety-instructor "$WORK/instructor" \
  -- --quiet --no-checkout --filter=blob:none >/dev/null
git -C "$WORK/instructor" fetch --quiet --depth 1 origin "$PRIVATE_SHA"
git -C "$WORK/instructor" -c advice.detachedHead=false checkout \
  --quiet --detach FETCH_HEAD
ACTUAL="$(git -C "$WORK/instructor" rev-parse HEAD)"
[[ "$ACTUAL" == "$PRIVATE_SHA" ]] || {
  echo 'AXIA_G11_BOOTSTRAP_BLOCKED_PRIVATE_SOURCE_SHA_MISMATCH' >&2; exit 2
}
echo "AXIA_G11_PRIVATE_PINNED_SOURCE_VERIFIED sha=$PRIVATE_SHA"
AXIA_G11_PRIVATE_SOURCE_SHA="$PRIVATE_SHA" \
  bash "$WORK/instructor/scripts/p4_g11_owner_custody_once.sh"
echo 'AXIA_G11_OWNER_LOCAL_CUSTODY_BOOTSTRAP_COMPLETE_NO_GAZEBO'
