#!/usr/bin/env bash
# AXIA Cycle33 final ONE Owner WSL2/WSLg simulation Goal. No auto-consent.
# Immutable public release, exact sealed private source, real GUI L2 pass.
# Prior Owner first Guard CM TTL breach and all original raw evidence remain preserved.
set -Eeuo pipefail
umask 077
readonly REPO='silverbjin/axia-robot-safety-ci-public'
readonly RELEASE_SHA='f4b05a1d593385445308acd43af57a9faad1c788'
readonly RELEASE_TREE='f4dbe38e071b168baaa7ed1f4cd967ed968978fc'
readonly PRIVATE_SHA='420fd276ec1018f7fcc3f14873693cad02f080b4'
readonly CI_L2_RUN=43824411236
if [[ "${1:-}" == --self-check && $# == 1 ]];then
  [[ "$RELEASE_SHA" =~ ^[a-f0-9]{40}$ && "$RELEASE_TREE" =~ ^[a-f0-9]{40}$ &&
     "$PRIVATE_SHA" =~ ^[a-f0-9]{40}$ ]] || exit 3
  bash -n "$0"
  echo "AXIA_G07_CYCLE33_BOOTSTRAP_STATIC_PASS public_sha=$RELEASE_SHA private_sha=$PRIVATE_SHA ci_l2=$CI_L2_RUN NO_ROS_NO_GOAL OWNER_NOT_RUN"
  exit 0
fi
[[ $# == 0 ]] || { echo AXIA_G07_CYCLE33_BOOTSTRAP_UNSUPPORTED_ARGS_NO_GOAL >&2;exit 3; }
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo AXIA_G07_CYCLE33_TTY_REQUIRED_NO_ROS_NO_GOAL >&2;exit 3;
}
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || {
  echo AXIA_G07_CYCLE33_UBUNTU24_REQUIRED_NO_GOAL >&2;exit 3;
}
grep -qiE '(microsoft|wsl)' /proc/sys/kernel/osrelease || {
  echo AXIA_G07_CYCLE33_WSL2_REQUIRED_NO_GOAL >&2;exit 3;
}
[[ -r /opt/ros/jazzy/setup.bash && -n "${DISPLAY:-}" ]] || {
  echo AXIA_G07_CYCLE33_JAZZY_WSLG_REQUIRED_NO_GOAL >&2;exit 3;
}
for cmd in git gh python3 bash mktemp sha256sum;do
  command -v "$cmd" >/dev/null || {
    echo "AXIA_G07_CYCLE33_MISSING_$cmd NO_ROS_NO_GOAL" >&2;exit 3;
  }
done
gh auth status >/dev/null 2>&1 || {
  echo AXIA_G07_CYCLE33_PRIVATE_GH_AUTH_REQUIRED_NO_GOAL >&2;exit 3;
}
[[ -d "$HOME" && "$HOME" != / && ! -L "$HOME" ]] || {
  echo AXIA_G07_CYCLE33_OWNER_HOME_UNTRUSTED_NO_GOAL >&2;exit 3;
}
WORK="$(mktemp -d "$HOME/.axia_g07_cycle33_checkout_XXXXXXXX")"
cleanup() {
  rc=$?
  trap - EXIT INT TERM
  cd "$HOME" 2>/dev/null || cd /
  if [[ -d "$WORK" && "$WORK" == "$HOME"/.axia_g07_cycle33_checkout_* ]];then
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
  echo AXIA_G07_CYCLE33_PUBLIC_SHA_TREE_INVALID_NO_GOAL >&2;exit 3;
}
GATE="$WORK/d06/acceptance/g07_cycle33_owner_ci_gate_v1.json"
CHECK="$WORK/d06/live/g07_cycle33_owner_ci_gate_v1.py"
OWNER="$WORK/d06/scripts/g07_cycle33_owner_wsl2_once.sh"
for f in "$GATE" "$CHECK" "$OWNER" \
 "$WORK/scripts/axia_g07_cycle33_p4_owner_once.sh";do
  [[ -s "$f" ]] || { echo AXIA_G07_CYCLE33_RELEASE_MISSING_NO_GOAL >&2;exit 3; }
done
bash -n "$OWNER"
bash -n "$WORK/scripts/axia_g07_cycle33_p4_owner_once.sh"
# Historical Owner first Guard 174ms / CM RMW 186ms failure is
# acknowledged in the immutable NEW source/L2 admission receipt. Old locks
# are retained, never reset. Same-source/run lock blocks another attempt.
FIELD_CHECK="$WORK/d06/live/g07_cycle33_owner_ci_gate_v1.py"
if [[ ! -s "$FIELD_CHECK" ]] ||
   ! python3 "$FIELD_CHECK" --home "$HOME" --gate "$GATE" \
     --private-sha "$PRIVATE_SHA" --private-tree "5ca77fb0bedd597b89b791e0931b42ea5a9cbdc9" \
     --ci-run "$CI_L2_RUN";then
  echo AXIA_G07_CYCLE33_OLD_FAILURE_RETAINED_OR_NEW_ATTEMPT_BLOCKED_NO_ROS_NO_GOAL
  exit 3
fi
python3 "$CHECK" --gate "$GATE" --private-sha "$PRIVATE_SHA" --ci-run "$CI_L2_RUN" || {
  echo AXIA_G07_CYCLE33_RELEASE_GATE_HOLD_NO_GOAL >&2;exit 3;
}
echo "AXIA_G07_CYCLE33_PUBLIC_SHA_VERIFIED=$RELEASE_SHA"
echo "AXIA_G07_CYCLE33_PRIVATE_SHA_EXPECTED=$PRIVATE_SHA"
echo "AXIA_G07_CYCLE33_CI_REAL_GUI_L2_PASS_RUN=$CI_L2_RUN"
echo 'SIMULATION ONLY, one Owner WSLg Goal requires physical YES-P2-G07-GOAL TTY consent.'
echo 'Guard hard TTL 150ms and 120ms release margin remain unchanged.'
echo 'Old failures and original evidence are preserved. CI Xvfb is not WSLg acceptance.'
echo AXIA_MVP_DEMO_ACCEPTED=HOLD
export AXIA_G07_CYCLE33_PUBLIC_RELEASE_SHA="$RELEASE_SHA"
bash "$OWNER"
