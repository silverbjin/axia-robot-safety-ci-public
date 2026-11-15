#!/usr/bin/env bash
# AXIA G07 single final Owner WSL2 entry. Public pinned source, private solution
# remains sealed. This script never supplies the manual YES-P2-G07-GOAL.
set -Eeuo pipefail
umask 077
readonly PUBLIC_REPO='silverbjin/axia-robot-safety-ci-public'
readonly PUBLIC_SOURCE_SHA='3259ad996010de5cead595a2eeb42ff644ca9ad6'
readonly PUBLIC_SOURCE_TREE='967b485d4614d7562524803f07a80a4367420963'
readonly PRIVATE_SOURCE_SHA='db1eec05e01e1db0d0d2e0c05610806ef4e499f9'
readonly P4_CI_GUI_L2_RUN=43685818018
if [[ "${1:-}" == "--self-check" ]];then
  [[ $# == 1 && "$PUBLIC_SOURCE_SHA" =~ ^[0-9a-f]{40}$ &&
     "$PUBLIC_SOURCE_TREE" =~ ^[0-9a-f]{40}$ &&
     "$PRIVATE_SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 3
  echo "AXIA_G07_FINAL_BOOTSTRAP_STATIC_PASS public_sha=$PUBLIC_SOURCE_SHA private_sha=$PRIVATE_SOURCE_SHA ci_l2=$P4_CI_GUI_L2_RUN NO_ROS_NO_GOAL"
  exit 0
fi
[[ $# == 0 ]] || { echo 'AXIA_G07_BOOTSTRAP_UNSUPPORTED_ARGS_NO_GOAL';exit 3; }
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'AXIA_G07_BOOTSTRAP_TTY_REQUIRED_NO_ROS_NO_GOAL' >&2
  exit 3
}
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || {
  echo 'AXIA_G07_BOOTSTRAP_UBUNTU24_REQUIRED_NO_ROS_NO_GOAL';exit 3;
}
grep -qiE '(microsoft|wsl2)' /proc/sys/kernel/osrelease || {
  echo 'AXIA_G07_BOOTSTRAP_WSL2_REQUIRED_NO_ROS_NO_GOAL';exit 3;
}
for cmd in git gh bash python3 mktemp;do
  command -v "$cmd" >/dev/null || {
    echo "AXIA_G07_BOOTSTRAP_MISSING_CMD=$cmd NO_GOAL";exit 3;
  }
done
gh auth status >/dev/null 2>&1 || {
  echo 'AXIA_G07_BOOTSTRAP_PRIVATE_GH_AUTH_REQUIRED_NO_ROS_NO_GOAL';exit 3;
}
[[ -r /opt/ros/jazzy/setup.bash && -n "${DISPLAY:-}" ]] || {
  echo 'AXIA_G07_BOOTSTRAP_ROS_JAZZY_OR_WSLG_MISSING_NO_GOAL';exit 3;
}
WORK="$(mktemp -d "$HOME/.axia_g07_final_checkout_XXXXXXXX")"
cleanup(){
  rc=$?
  trap - EXIT INT TERM
  cd "$HOME" 2>/dev/null || cd /
  if [[ -d "$WORK" && "$WORK" == "$HOME"/.axia_g07_final_checkout_* ]];then
    rm -rf -- "$WORK"
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
git -C "$WORK" init -q
git -C "$WORK" remote add origin "https://github.com/$PUBLIC_REPO.git"
git -C "$WORK" fetch -q --depth 1 origin "$PUBLIC_SOURCE_SHA"
git -C "$WORK" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$PUBLIC_SOURCE_SHA" &&
   "$(git -C "$WORK" rev-parse 'HEAD^{tree}')" == "$PUBLIC_SOURCE_TREE" ]] || {
  echo 'AXIA_G07_BOOTSTRAP_PUBLIC_PIN_OR_TREE_MISMATCH_NO_GOAL';exit 3;
}
OWNER="$WORK/d06/scripts/g07_unified_final_owner_wsl2_once.sh"
[[ -r "$OWNER" ]] && bash -n "$OWNER" || {
  echo 'AXIA_G07_BOOTSTRAP_OWNER_SCRIPT_MISSING_OR_SYNTAX_INVALID_NO_GOAL';exit 3;
}
echo "AXIA_G07_FINAL_PUBLIC_SHA_VERIFIED=$PUBLIC_SOURCE_SHA"
echo "AXIA_G07_FINAL_PRIVATE_SHA_EXPECTED=$PRIVATE_SOURCE_SHA"
echo 'AXIA_G07_CI_GUI_L2_SCOPED_PASS_RUN_43685818018 OWNER_WSLG_NOT_YET_RUN'
echo 'SIMULATION ONLY: one Owner WSL2 Goal still requires manual TTY consent; no certified E-Stop.'
echo 'Any new field timing violation returns to PUBLIC CI RED -> GREEN; no automatic local retry.'
bash "$OWNER"
