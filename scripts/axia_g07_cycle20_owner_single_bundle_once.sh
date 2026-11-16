#!/usr/bin/env bash
# AXIA G07 Cycle20: ONE sanitized existing-original diagnostic .tar.gz.
# Same immutable Python implementation is exercised by Ubuntu24 public CI.
# NO ROS, Gazebo, Goal, cmd_vel, privileged writes, previous lock modification.
set -Eeuo pipefail
umask 077
readonly REPO="silverbjin/axia-robot-safety-ci-public"
readonly PIN="6fe251c833f95f5484b79aa0f4c98bf9d6b76d7b"
readonly PIN_TREE="f6adcd1141b29f8c94f980a18f5d1e04cbe67c2a"
readonly OWNER_RUN="p2-l3-owner-A9IwJNZJ"
readonly ORIGINAL_SHA="c2557e3269c5cb3f56d1842f8d39bcdc5d6ab0055180911fc492a5bc84a1f672"
if [[ "${1:-}" == --self-check && $# -eq 1 ]];then
  bash -n "$0"
  [[ "$PIN" =~ ^[a-f0-9]{40}$ && "$PIN_TREE" =~ ^[a-f0-9]{40}$ &&
     "$ORIGINAL_SHA" =~ ^[a-f0-9]{64}$ ]] || exit 3
  echo AXIA_G07_CYCLE20_SINGLE_BUNDLE_SELF_CHECK_PASS_NO_ROS_NO_GOAL
  exit 0
fi
[[ $# == 0 ]] || {
  echo AXIA_G07_CYCLE20_UNSUPPORTED_ARGS_NO_ROS_NO_GOAL >&2
  exit 3
}
for cmd in git python3 sha256sum mktemp bash;do
  command -v "$cmd" >/dev/null || {
    echo "AXIA_G07_CYCLE20_MISSING_$cmd NO_ROS_NO_GOAL" >&2;exit 3;
  }
done
[[ -d "$HOME" && "$HOME" != / && ! -L "$HOME" ]] || {
  echo AXIA_G07_CYCLE20_UNTRUSTED_HOME_NO_ROS_NO_GOAL >&2;exit 3;
}
readonly ORIGINAL="$HOME/axia_p2_private_evidence/$OWNER_RUN.tar.gz"
readonly CUSTODY="$HOME/.axia_p4_g11_session_custody/objects/c2/$ORIGINAL_SHA"
if [[ -f "$ORIGINAL" && ! -L "$ORIGINAL" ]];then
  ARCHIVE="$ORIGINAL"
elif [[ -f "$CUSTODY" && ! -L "$CUSTODY" ]];then
  ARCHIVE="$CUSTODY"
else
  echo AXIA_G07_CYCLE20_ORIGINAL_ARCHIVE_MISSING_NO_ROS_NO_GOAL >&2
  echo AXIA_MVP_DEMO_ACCEPTED=HOLD
  exit 3
fi
[[ "$(sha256sum -- "$ARCHIVE" | cut -d' ' -f1)" == "$ORIGINAL_SHA" ]] || {
  echo AXIA_G07_CYCLE20_ORIGINAL_SHA_MISMATCH_NO_ROS_NO_GOAL >&2
  echo AXIA_MVP_DEMO_ACCEPTED=HOLD
  exit 3
}
echo AXIA_G07_CYCLE20_ORIGINAL_SHA256_VERIFIED_NO_ROS_NO_GOAL
WORK="$(mktemp -d "$HOME/.axia_g07_cycle20_source_XXXXXXXX")"
cleanup(){
  code=$?
  trap - EXIT INT TERM
  cd "$HOME" 2>/dev/null || cd /
  if [[ -d "$WORK" && "$WORK" == "$HOME"/.axia_g07_cycle20_source_* ]];then
    rm -rf -- "$WORK"
  fi
  exit "$code"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
git -C "$WORK" init -q
git -C "$WORK" remote add origin "https://github.com/$REPO.git"
git -C "$WORK" fetch -q --depth 1 origin "$PIN"
git -C "$WORK" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$PIN" &&
   "$(git -C "$WORK" rev-parse 'HEAD^{tree}')" == "$PIN_TREE" ]] || {
  echo AXIA_G07_CYCLE20_PUBLIC_SOURCE_SHA_TREE_MISMATCH_NO_ROS_NO_GOAL >&2;exit 3;
}
echo AXIA_G07_CYCLE20_PUBLIC_SOURCE_SHA_TREE_VERIFIED_NO_ROS_NO_GOAL
export PYTHONDONTWRITEBYTECODE=1
python3 "$WORK/d06/live/g07_cycle20_single_bundle.py" \
  --archive "$ARCHIVE" --expected-sha256 "$ORIGINAL_SHA" \
  --out-dir "$HOME/.axia_g07_owner_single_evidence_bundles"
echo AXIA_G07_CYCLE20_OWNER_ONE_ARCHIVE_ONLY_PRIVATE_RAW_PRESERVED
echo AXIA_MVP_DEMO_ACCEPTED=HOLD
