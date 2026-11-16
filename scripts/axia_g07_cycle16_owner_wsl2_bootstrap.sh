#!/usr/bin/env bash
# AXIA Cycle16 final ONE Owner WSL2/WSLg simulation Goal. No auto-consent.
# Immutable public release, exact sealed private source, real GUI L2 pass.
# Existing bc270... field failure and all prior raw evidence preserved.
set -Eeuo pipefail
umask 077
readonly REPO='silverbjin/axia-robot-safety-ci-public'
readonly RELEASE_SHA='dd425003b9a8c6891330744f33330f6a206eb2e8'
readonly RELEASE_TREE='bdf887e169127f3ebb704aef885cacd926d3b554'
readonly PRIVATE_SHA='01d45d46b6eb6a05b1bd313d73f1fc3549575545'
readonly CI_L2_RUN=43727149856
if [[ "${1:-}" == --self-check && $# == 1 ]];then
  [[ "$RELEASE_SHA" =~ ^[a-f0-9]{40}$ && "$RELEASE_TREE" =~ ^[a-f0-9]{40}$ &&
     "$PRIVATE_SHA" =~ ^[a-f0-9]{40}$ ]] || exit 3
  bash -n "$0"
  echo "AXIA_G07_CYCLE16_BOOTSTRAP_STATIC_PASS public_sha=$RELEASE_SHA private_sha=$PRIVATE_SHA ci_l2=$CI_L2_RUN NO_ROS_NO_GOAL OWNER_NOT_RUN"
  exit 0
fi
[[ $# == 0 ]] || { echo AXIA_G07_CYCLE16_BOOTSTRAP_UNSUPPORTED_ARGS_NO_GOAL >&2;exit 3; }
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo AXIA_G07_CYCLE16_TTY_REQUIRED_NO_ROS_NO_GOAL >&2;exit 3;
}
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || {
  echo AXIA_G07_CYCLE16_UBUNTU24_REQUIRED_NO_GOAL >&2;exit 3;
}
grep -qiE '(microsoft|wsl)' /proc/sys/kernel/osrelease || {
  echo AXIA_G07_CYCLE16_WSL2_REQUIRED_NO_GOAL >&2;exit 3;
}
[[ -r /opt/ros/jazzy/setup.bash && -n "${DISPLAY:-}" ]] || {
  echo AXIA_G07_CYCLE16_JAZZY_WSLG_REQUIRED_NO_GOAL >&2;exit 3;
}
for cmd in git gh python3 bash mktemp sha256sum;do
  command -v "$cmd" >/dev/null || {
    echo "AXIA_G07_CYCLE16_MISSING_$cmd NO_ROS_NO_GOAL" >&2;exit 3;
  }
done
gh auth status >/dev/null 2>&1 || {
  echo AXIA_G07_CYCLE16_PRIVATE_GH_AUTH_REQUIRED_NO_GOAL >&2;exit 3;
}
[[ -d "$HOME" && "$HOME" != / && ! -L "$HOME" ]] || {
  echo AXIA_G07_CYCLE16_OWNER_HOME_UNTRUSTED_NO_GOAL >&2;exit 3;
}
WORK="$(mktemp -d "$HOME/.axia_g07_cycle16_checkout_XXXXXXXX")"
cleanup() {
  rc=$?
  trap - EXIT INT TERM
  cd "$HOME" 2>/dev/null || cd /
  if [[ -d "$WORK" && "$WORK" == "$HOME"/.axia_g07_cycle16_checkout_* ]];then
    rm -rf -- "$WORK"
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
git -C "$WORK" init -q
git -C "$WORK" remote add origin "https://github.com/$REPO.git"
git -C "$WORK" fetch --quiet --depth 1 origin "$RELEASE_SHA"
git -C "$WORK" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$RELEASE_SHA" &&
   "$(git -C "$WORK" rev-parse 'HEAD^{tree}')" == "$RELEASE_TREE" ]] || {
  echo AXIA_G07_CYCLE16_PUBLIC_SHA_TREE_INVALID_NO_GOAL >&2;exit 3;
}
GATE="$WORK/d06/acceptance/g07_cycle16_owner_ci_gate_v3.json"
CHECK="$WORK/d06/live/g07_cycle16_owner_ci_gate_v4.py"
OWNER="$WORK/d06/scripts/g07_cycle16_owner_wsl2_once.sh"
for f in "$GATE" "$CHECK" "$OWNER" \
 "$WORK/scripts/axia_g07_cycle16_p4_owner_once.sh";do
  [[ -s "$f" ]] || { echo AXIA_G07_CYCLE16_RELEASE_MISSING_NO_GOAL >&2;exit 3; }
done
bash -n "$OWNER"
bash -n "$WORK/scripts/axia_g07_cycle16_p4_owner_once.sh"
# Never print the OLD CI-only manual_attempt_allowed=true message before
# checking the exact historical Owner field failure. The fixed bootstrap
# is a new checkout version; the immutable old bootstrap cannot be edited.
FIELD_CHECK="$WORK/d06/live/g07_cycle18_field_owner_admission_v5.py"
FIELD_RECORD="$WORK/d06/tests/fixtures/g07_cycle17_wsl2_guard_174ms_rmw_186ms_sanitized.json"
if [[ ! -s "$FIELD_CHECK" || ! -s "$FIELD_RECORD" ]] ||
   ! python3 "$FIELD_CHECK" --home "$HOME" --ci-gate "$GATE" \
     --field-evidence "$FIELD_RECORD";then
  echo AXIA_G07_CYCLE18_FIELD_PREVIOUS_GOAL_CM_TTL_BREACH_HOLD_NO_ROS_NO_GOAL
  exit 3
fi
python3 "$CHECK" --gate "$GATE" --private-sha "$PRIVATE_SHA" --ci-run "$CI_L2_RUN" || {
  echo AXIA_G07_CYCLE16_RELEASE_GATE_HOLD_NO_GOAL >&2;exit 3;
}
echo "AXIA_G07_CYCLE16_PUBLIC_SHA_VERIFIED=$RELEASE_SHA"
echo "AXIA_G07_CYCLE16_PRIVATE_SHA_EXPECTED=$PRIVATE_SHA"
echo "AXIA_G07_CYCLE16_CI_REAL_GUI_L2_PASS_RUN=$CI_L2_RUN"
echo 'SIMULATION ONLY, one Owner WSLg Goal requires physical YES-P2-G07-GOAL TTY consent.'
echo 'Guard hard TTL 150ms and 120ms release margin remain unchanged.'
echo 'Old failures and original evidence are preserved. CI Xvfb is not WSLg acceptance.'
echo AXIA_MVP_DEMO_ACCEPTED=HOLD
export AXIA_G07_CYCLE16_PUBLIC_RELEASE_SHA="$RELEASE_SHA"
bash "$OWNER"
