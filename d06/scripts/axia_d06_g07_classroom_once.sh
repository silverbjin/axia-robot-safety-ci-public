#!/usr/bin/env bash
# D06 classroom reuse of verified G07 Task03 motion L2 and Task04 Owner GUI.
# This script NEVER owns a Nav2 Goal. A real moving Owner runtime is not released.
set -Eeuo pipefail
umask 077
readonly PUBLIC_REPO='silverbjin/axia-robot-safety-ci-public'
readonly STUDENT_SHA='01752add2e30c90c4d3286ef3a450f97746ecb55'
readonly TASK03_GAZEBO_L2_RUN='44223320904'
readonly TASK03_GAZEBO_L2_HEAD='6bc8b0711ab056e63e100f3eede2c5f06cdf3856'
readonly TASK04_GUI_L2_RUN='44238643061'
readonly TASK04_GUI_L2_HEAD='5bb0cd72086f2f1a057f382649b773fff106f1f9'
readonly TASK04_GUI_SCRIPT='scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh'
readonly TASK04_GUI_SCRIPT_BLOB='a15cf37e1a1d2a0253029c0a1dd8e2530e307c25'

hold() {
  echo "D06_G07_CLASSROOM_HOLD=$1" >&2
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false' >&2
  exit 3
}

usage() {
  echo 'D06_G07_CLASSROOM_USAGE --self-check|--ci-status|--doctor|--gui-only|--live' >&2
  exit 2
}

(( $# == 1 )) || usage
mode="$1"
case "$mode" in
  --self-check|--ci-status|--doctor|--gui-only|--live) ;;
  *) usage;;
esac

self_check() {
  [[ "$STUDENT_SHA" =~ ^[0-9a-f]{40}$ &&
     "$TASK03_GAZEBO_L2_HEAD" =~ ^[0-9a-f]{40}$ &&
     "$TASK04_GUI_L2_HEAD" =~ ^[0-9a-f]{40}$ &&
     "$TASK04_GUI_SCRIPT_BLOB" =~ ^[0-9a-f]{40}$ ]] || hold INVALID_SOURCE_PIN
  [[ "$TASK03_GAZEBO_L2_RUN" =~ ^[0-9]+$ &&
     "$TASK04_GUI_L2_RUN" =~ ^[0-9]+$ ]] || hold INVALID_RUN_PIN
  echo "D06_G07_CLASSROOM_STATIC_PASS NO_ROS_NO_GOAL student=$STUDENT_SHA"
  echo "D06_G07_CLASSROOM_REUSED_MOVING_CI=$TASK03_GAZEBO_L2_RUN"
  echo "D06_G07_CLASSROOM_REUSED_GUI_CI=$TASK04_GUI_L2_RUN"
  echo 'D06_G07_CLASSROOM_OWNER_MOVING_L3=NOT_RUN'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
}

check_run() {
  local id="$1" sha="$2" scope="$3" actual
  actual="$(gh api "repos/$PUBLIC_REPO/actions/runs/$id" \
    --jq '(.head_sha // "")+" "+(.status // "")+" "+(.conclusion // "")')" ||
    hold "${scope}_CI_PROVENANCE_UNAVAILABLE"
  [[ "$actual" == "$sha completed success" ]] ||
    hold "${scope}_CI_SOURCE_OR_CONCLUSION_MISMATCH"
  echo "D06_G07_CLASSROOM_${scope}_HISTORICAL_CI_PASS run=$id head=$sha"
}

self_check >/dev/null || hold SELF_CHECK_FAILED
if [[ "$mode" == --self-check ]];then
  self_check
  exit 0
fi
if [[ "$mode" == --live ]];then
  # G07 Task03's moving Goal is explicitly GitHub-Actions-only. Task04
  # WSL2 runner is NO_GOAL. Neither can be turned into Owner authority
  # by spoofing an Actions variable or bypassing safety admission.
  hold D06_G07_CLASSROOM_MOVING_OWNER_NOT_RELEASED
fi
[[ "${GITHUB_ACTIONS:-}" != true || "$mode" == --ci-status ]] ||
  hold D06_G07_CLASSROOM_OWNER_WSL2_ONLY
command -v gh >/dev/null 2>&1 || hold GH_CLI_REQUIRED
check_run "$TASK03_GAZEBO_L2_RUN" "$TASK03_GAZEBO_L2_HEAD" TASK03_MOVING
check_run "$TASK04_GUI_L2_RUN" "$TASK04_GUI_L2_HEAD" TASK04_GUI
if [[ "$mode" == --ci-status ]];then
  echo 'D06_G07_CLASSROOM_CI_REUSE_PROVENANCE_PASS NOT_NEW_INTEGRATED_CI_L2'
  echo 'D06_G07_CLASSROOM_OWNER_MOVING_L3=NOT_RUN'
  exit 0
fi
# Actual GUI modes are for an interactive WSL2 Owner only; no Actions,
# CI Goal permission spoofing, private Instructor checkout or fake approval.
[[ "${GITHUB_ACTIONS:-}" != true ]] || hold D06_G07_CLASSROOM_OWNER_WSL2_ONLY
[[ -r /proc/sys/kernel/osrelease ]] &&
 grep -Eiq 'microsoft|wsl' /proc/sys/kernel/osrelease ||
 hold D06_G07_CLASSROOM_OWNER_WSL2_ONLY
[[ -t 0 && -r /dev/tty ]] || hold OWNER_TERMINAL_REQUIRED
for cmd in curl git bash;do
  command -v "$cmd" >/dev/null 2>&1 || hold "MISSING_$cmd"
done
script="$(mktemp --suffix=.sh)" || hold TEMPFILE_UNAVAILABLE
trap 'rm -f -- "$script"' EXIT
curl -fLsS --retry 3 --retry-delay 2 --max-time 90 \
  "https://raw.githubusercontent.com/$PUBLIC_REPO/$TASK04_GUI_L2_HEAD/$TASK04_GUI_SCRIPT" \
  -o "$script" || hold TASK04_PIN_DOWNLOAD_FAILED
[[ "$(git hash-object "$script")" == "$TASK04_GUI_SCRIPT_BLOB" ]] ||
  hold TASK04_DOWNLOADED_BLOB_MISMATCH
bash -n "$script" || hold TASK04_SCRIPT_SYNTAX
if [[ "$mode" == --doctor ]];then
  bash "$script" --doctor
  echo 'D06_G07_CLASSROOM_OWNER_DOCTOR_COMPLETE NO_GOAL'
else
  echo 'D06_G07_CLASSROOM_GUI_ONLY_START NO_MOVING_GOAL'
  bash "$script" --run
  echo 'D06_G07_CLASSROOM_GUI_ONLY_COMPLETE_OWNER_MOVING_NOT_RUN'
fi
