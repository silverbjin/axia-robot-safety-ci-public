#!/usr/bin/env bash
# G07 read-only Owner WSL2 forensic preflight. Never dispatches ROS or Goal.
set -Eeuo pipefail
umask 077
readonly PUBLIC_REPO='silverbjin/axia-robot-safety-ci-public'
readonly VERIFIED_L0_SOURCE='6d715227564de0ddab6cee8dfd6e156254f12266'
if [[ "${1:-}" == "--self-check" && $# == 1 ]];then
  [[ "$VERIFIED_L0_SOURCE" =~ ^[0-9a-f]{40}$ ]]
  ! grep -E 'ros2 (action|topic pub)|YES-P2-G07-GOAL' "$0" >/dev/null
  echo AXIA_G07_FIELD_READONLY_BOOTSTRAP_SELF_CHECK_PASS_NO_ROS_NO_GOAL
  exit 0
fi
[[ $# == 0 ]] || { echo AXIA_G07_FIELD_READONLY_UNSUPPORTED_ARGS_NO_GOAL >&2;exit 3; }
for cmd in git bash python3 mktemp;do
  command -v "$cmd" >/dev/null || { echo "AXIA_G07_FIELD_MISSING_CMD=$cmd NO_GOAL" >&2;exit 3; }
done
[[ -d "$HOME" && "$HOME" != / ]] || { echo AXIA_G07_FIELD_HOME_UNAVAILABLE_NO_GOAL >&2;exit 3; }
WORK="$(mktemp -d "$HOME/.axia_g07_field_readonly_XXXXXXXX")"
cleanup(){
  rc=$?
  trap - EXIT
  cd "$HOME" 2>/dev/null || cd /
  if [[ -d "$WORK" && "$WORK" == "$HOME"/.axia_g07_field_readonly_* ]];then
    rm -rf -- "$WORK"
  fi
  exit "$rc"
}
trap cleanup EXIT
git -C "$WORK" init -q
git -C "$WORK" remote add origin "https://github.com/$PUBLIC_REPO.git"
git -C "$WORK" fetch -q --depth 1 origin "$VERIFIED_L0_SOURCE"
git -C "$WORK" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$VERIFIED_L0_SOURCE" ]] || {
  echo AXIA_G07_FIELD_SOURCE_PIN_INVALID_NO_GOAL >&2;exit 3;
}
test -s "$WORK/d06/scripts/g07_owner_field_readonly_preflight_v3.sh"
bash -n "$WORK/d06/scripts/g07_owner_field_readonly_preflight_v3.sh"
echo "AXIA_G07_FIELD_L0_VERIFIED_SOURCE=$VERIFIED_L0_SOURCE"
echo AXIA_G07_FIELD_SAFETY_RECHECK_OWNER_GOAL_NOT_AUTHORIZED
RC=0
bash "$WORK/d06/scripts/g07_owner_field_readonly_preflight_v3.sh" || RC=$?
echo "AXIA_G07_FIELD_READONLY_RESULT_RC=$RC"
echo AXIA_MVP_DEMO_ACCEPTED=HOLD
if (( RC==0 ));then
  echo AXIA_G07_FIELD_UNEXPECTED_OWNER_RELEASE_NOT_PERMITTED >&2
fi
exit 3
