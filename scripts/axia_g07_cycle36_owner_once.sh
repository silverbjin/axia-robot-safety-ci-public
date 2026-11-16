#!/usr/bin/env bash
# AXIA G07 Cycle36 one Owner WSL2/WSLg moving-Goal FINAL candidate.
# Exact public Xvfb real-Gazebo L2 PASS; ONE manual physical TTY Goal only.
# Owner outcome is a numerical/raw-review candidate, NOT formal acceptance.
# This script NEVER modifies a safety TTL, grants automatic consent,
# repeats a prior failed SHA+CI trial or uploads private originals.
set -Eeuo pipefail
umask 077
readonly PRIVATE_SHA='2b59c1a74513ac5a5b80c5bd424001a625c07617'
readonly PRIVATE_TREE='5e0a464e97a9d3104303052e2bfaa68f8f0bb1ec'
readonly PUBLIC_VISUAL_SHA='132d8c64def534061d3467f3e1a339fbb44e3e68'
readonly PUBLIC_VISUAL_TREE='e285470ef153202fcc7b3e178a0720249bd12870'
readonly CI_WORKFLOW_SHA='8bacc46801d7150bb35e3d0f6656afbe91c2ff9d'
readonly CI_L2_RUN='43863443121'
readonly PUBLIC_REPO='silverbjin/axia-robot-safety-ci-public'
readonly PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'

hold() {
  echo "AXIA_G07_CYCLE36_OWNER_HOLD_NO_GOAL $*" >&2
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false' >&2
  exit 3
}

self_check() {
  for sha in "$PRIVATE_SHA" "$PRIVATE_TREE" "$PUBLIC_VISUAL_SHA" "$PUBLIC_VISUAL_TREE" "$CI_WORKFLOW_SHA";do
    [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || return 3
  done
  [[ "$CI_L2_RUN" =~ ^[0-9]+$ ]] || return 3
  bash -n "$0" || return 3
  echo "AXIA_G07_CYCLE36_OWNER_BOOTSTRAP_STATIC_PASS private_sha=$PRIVATE_SHA public_visual_sha=$PUBLIC_VISUAL_SHA ci_l2=$CI_L2_RUN NO_ROS_NO_GOAL OWNER_NOT_RUN"
}
if [[ "$#" == 1 && "$1" == --self-check ]];then
  self_check; exit $?
fi

verify_real_l2() {
  command -v gh >/dev/null || hold 'GH_CLI_MISSING'
  gh auth status >/dev/null 2>&1 || hold 'PRIVATE_GH_AUTH_REQUIRED'
  local actual
  actual="$(gh api "repos/$PUBLIC_REPO/actions/runs/$CI_L2_RUN" --jq '(.head_sha // "")+" "+(.status // "")+" "+(.conclusion // "")')" ||
    hold 'PUBLIC_ACTIONS_PROVENANCE_UNAVAILABLE'
  [[ "$actual" == "$CI_WORKFLOW_SHA completed success" ]] ||
    hold "REAL_GAZEBO_L2_PROVENANCE_MISMATCH $actual"
  echo "AXIA_G07_CYCLE36_REAL_GAZEBO_L2_PROVENANCE_VERIFIED run=$CI_L2_RUN source=$PRIVATE_SHA"
}
if [[ "$#" == 1 && "$1" == --admission-check ]];then
  self_check || exit 3
  verify_real_l2
  echo 'AXIA_G07_CYCLE36_ADMISSION_L0_PASS_NO_ROS_NO_GOAL OWNER_L3_NOT_RUN'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
[[ "$#" == 0 ]] || hold 'UNSUPPORTED_ARGUMENTS'
[[ -t 0 && -t 1 && -r /dev/tty ]] || hold 'CONTROLLING_TTY_REQUIRED'
[[ "${GITHUB_ACTIONS:-}" != true ]] || hold 'OWNER_NOT_ALLOWED_IN_PUBLIC_CI'
self_check || hold 'SCRIPT_STATIC_INVALID'
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || hold 'UBUNTU_24_04_REQUIRED'
grep -qiE '(wsl|microsoft)' /proc/sys/kernel/osrelease || hold 'WSL2_REQUIRED'
[[ -n "${DISPLAY:-}" && -r /opt/ros/jazzy/setup.bash ]] || hold 'WSLG_AND_JAZZY_REQUIRED'
for command_name in bash git gh python3 colcon ros2 gz rviz2 setsid taskset timeout sha256sum tar mktemp;do
  command -v "$command_name" >/dev/null || hold "COMMAND_MISSING_$command_name"
done
verify_real_l2

[[ -d "$HOME" && "$HOME" != / && ! -L "$HOME" ]] || hold 'OWNER_HOME_INVALID'
readonly WORK="$(mktemp -d "$HOME/.axia_g07_cycle36_checkout_XXXXXXXX")"
readonly OUT="$(mktemp -d "$HOME/axia_g07_cycle36_owner_XXXXXXXX")"
readonly PRIVATE="$WORK/instructor"
readonly PUBLIC="$WORK/public"
SIDECAR_PID=''
OWNER_RC=125
RESULT_RC=3
finish() {
  local rc=$?
  trap - EXIT INT TERM
  set +e
  if [[ "$SIDECAR_PID" =~ ^[0-9]+$ ]];then
    kill -TERM "$SIDECAR_PID" 2>/dev/null || true
    wait "$SIDECAR_PID" 2>/dev/null || true
  fi
  cd "$HOME" 2>/dev/null || cd /
  if [[ -d "$WORK" && "$WORK" == "$HOME"/.axia_g07_cycle36_checkout_* ]];then
    rm -rf -- "$WORK"
  fi
  if [[ -f "$OUT/sidecar.log" ]];then
    echo 'AXIA_G07_CYCLE36_SIDECAR_LAST_STATUS'
    tail -n 30 "$OUT/sidecar.log"
  fi
  ( cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 |
      sort -z | xargs -0 -r sha256sum > SHA256SUMS ) || true
  echo "AXIA_G07_CYCLE36_OWNER_WRAPPER_RC=$rc PRIVATE_OWNER_RC=$OWNER_RC"
  echo "AXIA_G07_CYCLE36_OWNER_DIAGNOSTICS=$OUT"
  echo 'AXIA_G07_CYCLE36_OWNER_WSLG_SCREENSHOT_AND_ORIGINAL_RAW_REVIEW_REQUIRED'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# PUBLIC visual comes from exact fixed CI source; do not execute mutable main.
git init -q "$PUBLIC" || hold 'PUBLIC_GIT_INIT'
git -C "$PUBLIC" remote add origin "https://github.com/$PUBLIC_REPO.git"
git -C "$PUBLIC" fetch --quiet --depth 1 origin "$PUBLIC_VISUAL_SHA" || hold 'PUBLIC_VISUAL_DOWNLOAD'
git -C "$PUBLIC" checkout -q --detach FETCH_HEAD || hold 'PUBLIC_VISUAL_CHECKOUT'
[[ "$(git -C "$PUBLIC" rev-parse HEAD)" == "$PUBLIC_VISUAL_SHA" &&
   "$(git -C "$PUBLIC" rev-parse 'HEAD^{tree}')" == "$PUBLIC_VISUAL_TREE" ]] ||
    hold 'PUBLIC_VISUAL_TREE_MISMATCH'

gh repo clone "$PRIVATE_REPO" "$PRIVATE" -- --quiet --no-checkout --filter=blob:none >/dev/null ||
  hold 'PRIVATE_SOURCE_CLONE_FAILED'
git -C "$PRIVATE" fetch --quiet --depth 1 origin "$PRIVATE_SHA" ||
  hold 'PRIVATE_SHA_DOWNLOAD_FAILED'
git -C "$PRIVATE" -c advice.detachedHead=false checkout -q --detach FETCH_HEAD ||
  hold 'PRIVATE_CHECKOUT_FAILED'
[[ "$(git -C "$PRIVATE" rev-parse HEAD)" == "$PRIVATE_SHA" &&
   "$(git -C "$PRIVATE" rev-parse 'HEAD^{tree}')" == "$PRIVATE_TREE" ]] ||
    hold 'PRIVATE_SHA_TREE_MISMATCH'

for file in "$PUBLIC/d06/scripts/d06_rviz_sidecar.sh" \
            "$PUBLIC/d06/scripts/g07_shared_gui_clients.sh" \
            "$PUBLIC/d06/live/g07_cycle36_owner_raw_gate.py" \
            "$PRIVATE/scripts/p2_owner_l3_wsl2.sh" \
            "$PRIVATE/tools/p4_g07_sim_server_cm_core_separation.py";do
  [[ -s "$file" ]] || hold 'SOURCE_FILE_MISSING'
done
bash -n "$PUBLIC/d06/scripts/d06_rviz_sidecar.sh" ||
  hold 'PUBLIC_VISUAL_SCRIPT_SYNTAX'
bash -n "$PRIVATE/scripts/p2_owner_l3_wsl2.sh" ||
  hold 'PRIVATE_OWNER_SCRIPT_SYNTAX'

# The accepted L2 CI used 4 cores with exact real multi-node delays.
# This Owner run must remeasure those SAME 7 channels in real WSLg.
readonly ATTEMPTS="$HOME/.axia_g07_cycle36_owner_attempts"
[[ ! -L "$ATTEMPTS" && ( ! -e "$ATTEMPTS" || -d "$ATTEMPTS" ) ]] ||
  hold 'ATTEMPT_STATE_UNTRUSTED'
mkdir -p "$ATTEMPTS"; chmod 700 "$ATTEMPTS"
readonly ATTEMPT="$ATTEMPTS/$PRIVATE_SHA-$CI_L2_RUN"
mkdir -m 700 "$ATTEMPT" 2>/dev/null || hold 'SAME_SHA_ALREADY_ATTEMPTED_NO_RETRY'
printf 'private_sha=%s\nci_run=%s\npublic_visual_sha=%s\n' \
  "$PRIVATE_SHA" "$CI_L2_RUN" "$PUBLIC_VISUAL_SHA" > "$ATTEMPT/source.txt"

readonly MARKER="$OUT/owner-start.marker"
touch "$MARKER"
export AXIA_G07_UNIFIED_GUI_SIDECAR=1
export AXIA_G07_CYCLE36_INTEGRATED_GUI=1
export AXIA_G07_GUI_READY_ATTESTATION_PATH="$OUT/display_attestation.json"
export AXIA_G07_WSLG_SOFTWARE_GL=0
echo 'AXIA_G07_CYCLE36_SINGLE_OWNER_ATTEMPT_RESERVED'
echo 'SIMULATION ONLY: one Goal needs manual physical TTY YES-P2-G07-GOAL.'
echo 'Guard TTL 150ms, 120ms CI release margin unchanged. Hardware E-Stop NOT certified.'

bash "$PUBLIC/d06/scripts/d06_rviz_sidecar.sh" "$MARKER" "$OUT" "$PRIVATE_SHA" \
  > "$OUT/sidecar.log" 2>&1 &
SIDECAR_PID=$!
if ( cd "$PRIVATE" && \
     AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA" \
     AXIA_G11_RUN_CUSTODY_REQUIRED=1 \
     bash scripts/p2_owner_l3_wsl2.sh --case G07 --mvp-relocated-obstacle );then
  OWNER_RC=0
else
  OWNER_RC=$?
  echo "AXIA_G07_CYCLE36_OWNER_INSTRUCTOR_BLOCKED rc=$OWNER_RC"
  exit "$OWNER_RC"
fi

mapfile -d '' -t originals < <(
 find "$HOME/axia_p2_private_evidence" -mindepth 2 -maxdepth 2 \
   -type f -name summary.json -newer "$MARKER" -print0 2>/dev/null
)
[[ "${#originals[@]}" == 1 ]] || hold 'OWNER_NEW_ORIGINAL_ROOT_NOT_UNIQUE'
readonly ORIGINAL_ROOT="$(dirname "${originals[0]}")"
[[ -r "$ORIGINAL_ROOT/source.sha" &&
   "$(cat "$ORIGINAL_ROOT/source.sha")" == "$PRIVATE_SHA" ]] ||
    hold 'OWNER_ORIGINAL_SOURCE_MISMATCH'
python3 "$PUBLIC/d06/live/g07_cycle36_owner_raw_gate.py" \
   --run-root "$ORIGINAL_ROOT" --source-sha "$PRIVATE_SHA" \
   --output "$OUT/g07_owner_raw_gate.json" ||
     hold 'OWNER_RAW_7_CHANNEL_RMW_OR_CANCEL_UNVERIFIED'
echo 'AXIA_G07_CYCLE36_OWNER_NUMERICAL_CANDIDATE_RAW_REVIEW_REQUIRED'
echo "AXIA_G07_CYCLE36_OWNER_PRIVATE_ORIGINAL=$ORIGINAL_ROOT"
echo 'AXIA_G07_CYCLE36_OWNER_WSLG_VISUAL_OBSERVATION_NOT_AUTOMATED'
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
