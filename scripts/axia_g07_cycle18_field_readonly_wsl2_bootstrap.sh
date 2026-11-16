#!/usr/bin/env bash
# One-shot READ-ONLY actual first WSL2 Guard safety violation diagnostic.
# No ROS, no Gazebo, no Goal, NO attempt reset. Existing Owner history kept.
# Pinned public snapshot contains exact CI-GREEN field-v5 preflight.
set -Eeuo pipefail
umask 077
readonly REPO='silverbjin/axia-robot-safety-ci-public'
readonly PIN='1527a5080e2e7d417696aae79aab615c02e49b5d'
readonly TREE='003801443d192ba6e1f6298d55eea08989307d2c'
if [[ "${1:-}" == '--self-check' && "$#" -eq 1 ]];then
  [[ "$PIN" =~ ^[a-f0-9]{40}$ && "$TREE" =~ ^[a-f0-9]{40}$ ]] || exit 3
  bash -n "$0"
  echo AXIA_G07_CYCLE18_FIELD_BOOTSTRAP_STATIC_PASS_NO_ROS_NO_GOAL
  exit 0
fi
[[ "$#" -eq 0 ]] || {
  echo AXIA_G07_CYCLE18_FIELD_BOOTSTRAP_BAD_ARGS_NO_ROS_NO_GOAL >&2;exit 3;
}
for cmd in git bash python3 mktemp;do
  command -v "$cmd" >/dev/null || {
    echo "AXIA_G07_CYCLE18_MISSING_$cmd NO_ROS_NO_GOAL" >&2;exit 3;
  }
done
[[ -d "$HOME" && "$HOME" != / && ! -L "$HOME" ]] || {
  echo AXIA_G07_CYCLE18_FIELD_BAD_HOME_NO_ROS_NO_GOAL >&2;exit 3;
}
if [[ -r /etc/os-release ]];then
  . /etc/os-release
  echo "AXIA_G07_FIELD_OS_COMPATIBILITY distro=${ID:-unknown} version=${VERSION_ID:-unknown} recommended=ubuntu_24.04_jazzy_harmonic; NO_ROS_NO_GOAL"
fi
WORK="$(mktemp -d "$HOME/.axia_g07_field_readonly_XXXXXXXX")"
cleanup() {
  rc=$?
  trap - EXIT INT TERM
  cd "$HOME" 2>/dev/null || cd /
  if [[ "$WORK" == "$HOME"/.axia_g07_field_readonly_* && -d "$WORK" ]];then
    rm -rf -- "$WORK"
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
git -C "$WORK" init -q
git -C "$WORK" remote add origin "https://github.com/$REPO.git"
git -C "$WORK" fetch -q --depth 1 origin "$PIN"
git -C "$WORK" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$PIN" &&
   "$(git -C "$WORK" rev-parse 'HEAD^{tree}')" == "$TREE" ]] || {
  echo AXIA_G07_CYCLE18_FIELD_PUBLIC_PIN_INVALID_NO_ROS_NO_GOAL >&2;exit 3;
}
echo "AXIA_G07_CYCLE18_FIELD_PUBLIC_SHA_TREE_VERIFIED=$PIN"
echo AXIA_G07_CYCLE18_OWNER_FIRST_FAILURE_NOT_GOAL_AUTHORITY
# Exact same preflight called by actual new Owner wrapper, including real
# persistent HOME lock; return code 3 is EXPECTED while safety Hold remains.
bash "$WORK/scripts/axia_g07_cycle18_owner_readonly_preflight.sh"
